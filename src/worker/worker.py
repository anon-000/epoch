"""
Worker main loop.
Listens for job assignments via Redis pub/sub, executes them, reports results.
Handles cancellation and preemption notifications.
"""

import asyncio
import json
import logging
import os
import socket
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.constants import JobState, WorkerState
from src.db.session import async_session_factory, init_db
from src.models.job import Job
from src.models.worker import Worker
from src.queue.redis_queue import redis_queue
from src.worker.executor import JobExecutor
from src.worker.heartbeat import HeartbeatSender
from src.services.event_logger import record_event

logger = logging.getLogger("epoch.worker")


class WorkerNode:
    def __init__(self, max_slots: int | None = None):
        self.worker_id = uuid.uuid4()
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        self.max_slots = max_slots or settings.worker_max_slots
        self.executor = JobExecutor()
        self.heartbeat = HeartbeatSender(self.worker_id)
        self._running = False
        self._active_jobs: dict[uuid.UUID, asyncio.Task] = {}
        self._cancelled_jobs: set[uuid.UUID] = set()

    async def start(self):
        """Register worker and start processing loop."""
        logger.info(f"Worker {self.worker_id} starting on {self.hostname}:{self.pid}...")
        await init_db()
        await redis_queue.connect()

        # Register in database
        async with async_session_factory() as session:
            worker = Worker(
                id=self.worker_id,
                hostname=self.hostname,
                pid=self.pid,
                max_slots=self.max_slots,
                state=WorkerState.ONLINE,
            )
            session.add(worker)
            await session.commit()

        self._running = True

        # Start heartbeat, pub/sub listener, and polling concurrently
        await asyncio.gather(
            self.heartbeat.start(),
            self._listen_for_jobs(),
            self._poll_for_assigned_jobs(),
        )

    async def stop(self):
        """Gracefully shut down the worker."""
        self._running = False
        self.heartbeat.stop()

        # Cancel all active job tasks
        for job_id, task in self._active_jobs.items():
            task.cancel()
            logger.info(f"Cancelled active job {job_id}")

        async with async_session_factory() as session:
            worker = await session.get(Worker, self.worker_id)
            if worker:
                worker.state = WorkerState.OFFLINE
                await session.commit()

        await redis_queue.close()
        logger.info(f"Worker {self.worker_id} stopped.")

    async def _listen_for_jobs(self):
        """Listen for job assignment notifications via Redis pub/sub."""
        pubsub = await redis_queue.subscribe_worker_channel()

        while self._running:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await self._handle_notification(data)
            except Exception:
                logger.exception("Error in pub/sub listener")
                await asyncio.sleep(1)

    async def _poll_for_assigned_jobs(self):
        """Fallback polling: check DB for assigned jobs in case pub/sub missed them."""
        while self._running:
            try:
                async with async_session_factory() as session:
                    result = await session.execute(
                        select(Job)
                        .where(Job.assigned_worker_id == self.worker_id)
                        .where(Job.state == JobState.SCHEDULED)
                    )
                    jobs = result.scalars().all()
                    for job in jobs:
                        if job.id not in self._active_jobs:
                            task = asyncio.create_task(self._execute_job(job.id))
                            self._active_jobs[job.id] = task
            except Exception:
                logger.exception("Error in job polling")

            await asyncio.sleep(settings.scheduler_loop_interval * 2)

    async def _handle_notification(self, data: dict):
        """Handle a notification from the scheduler."""
        msg_type = data.get("type")

        if msg_type == "job_assigned":
            worker_id = data.get("worker_id")
            if worker_id == str(self.worker_id):
                job_id = uuid.UUID(data["job_id"])
                if job_id not in self._active_jobs:
                    task = asyncio.create_task(self._execute_job(job_id))
                    self._active_jobs[job_id] = task

        elif msg_type == "cancel":
            job_id = uuid.UUID(data["job_id"])
            self._cancel_job(job_id)

        elif msg_type == "preempt":
            worker_id = data.get("worker_id")
            if worker_id == str(self.worker_id):
                job_id = uuid.UUID(data["job_id"])
                logger.info(f"Preemption received for job {job_id}")
                self._cancel_job(job_id)

    def _cancel_job(self, job_id: uuid.UUID):
        """Cancel a running job task."""
        self._cancelled_jobs.add(job_id)
        if job_id in self._active_jobs:
            self._active_jobs[job_id].cancel()
            logger.info(f"Cancelled job task {job_id}")

    async def _execute_job(self, job_id: uuid.UUID):
        """Execute a single job."""
        logger.info(f"Executing job {job_id}")

        try:
            async with async_session_factory() as session:
                job = await session.get(Job, job_id)
                if not job or job.state != JobState.SCHEDULED:
                    return

                # Transition to RUNNING
                job.state = JobState.RUNNING
                job.started_at = datetime.now(timezone.utc)
                job.attempt += 1
                await record_event(
                    session, job.id, "RUNNING",
                    detail=f"Execution started (attempt {job.attempt}/{job.max_retries})",
                    attempt=job.attempt,
                    worker_id=str(self.worker_id),
                )
                await session.commit()

                # Execute the job (passing job_id enables checkpointing)
                result = await self.executor.execute(job.job_type, job.payload, job_id=job_id)

                # Check if we were cancelled/preempted during execution
                if job_id in self._cancelled_jobs:
                    self._cancelled_jobs.discard(job_id)
                    logger.info(f"Job {job_id} was cancelled/preempted during execution.")
                    return

                # Re-fetch job in case state changed
                await session.refresh(job)
                if job.state != JobState.RUNNING:
                    return  # state was changed externally (cancel/preempt)

                if result["success"]:
                    job.state = JobState.COMPLETED
                    job.completed_at = datetime.now(timezone.utc)
                    await record_event(
                        session, job.id, "COMPLETED",
                        detail="Job completed successfully",
                        attempt=job.attempt,
                        worker_id=str(self.worker_id),
                    )
                    logger.info(f"Job {job_id} completed successfully.")
                else:
                    error_msg = result.get("error", "Unknown error")
                    job.error_message = error_msg
                    logger.warning(f"Job {job_id} failed (attempt {job.attempt}/{job.max_retries}): {error_msg}")

                    # Record the failure event
                    await record_event(
                        session, job.id, "FAILED",
                        detail=error_msg,
                        attempt=job.attempt,
                        worker_id=str(self.worker_id),
                    )

                    if job.attempt < job.max_retries:
                        # Re-queue for retry
                        job.state = JobState.QUEUED
                        job.assigned_worker_id = None
                        job.scheduled_at = None
                        job.started_at = None
                        await record_event(
                            session, job.id, "RETRIED",
                            detail=f"Auto-retry: re-queued (attempt {job.attempt}/{job.max_retries})",
                            attempt=job.attempt,
                            worker_id=str(self.worker_id),
                        )
                        from src.scheduler.priority_queue import compute_priority_score
                        score = compute_priority_score(job.priority)
                        await session.commit()
                        await redis_queue.enqueue_job(job.id, priority_score=score)
                        logger.info(f"Job {job_id} re-queued for retry (attempt {job.attempt}/{job.max_retries})")

                        # Decrement worker load + tenant slots
                        worker = await session.get(Worker, self.worker_id)
                        if worker:
                            if worker.current_load > 0:
                                worker.current_load -= 1
                            tenant_slots = dict(worker.tenant_slots)
                            if job.tenant_id in tenant_slots:
                                tenant_slots[job.tenant_id] = max(0, tenant_slots[job.tenant_id] - 1)
                                if tenant_slots[job.tenant_id] == 0:
                                    del tenant_slots[job.tenant_id]
                                worker.tenant_slots = tenant_slots
                        await session.commit()
                        return
                    else:
                        # Max retries exhausted — move to dead letter
                        from src.models.job import DeadLetterJob
                        job.state = JobState.DEAD_LETTER
                        job.assigned_worker_id = None
                        dead_letter = DeadLetterJob(
                            job_id=job.id,
                            final_error=error_msg,
                            total_attempts=job.attempt,
                        )
                        session.add(dead_letter)
                        await record_event(
                            session, job.id, "DEAD_LETTER",
                            detail=f"Moved to dead letter after {job.attempt} attempts: {error_msg}",
                            attempt=job.attempt,
                            worker_id=str(self.worker_id),
                        )
                        logger.error(f"Job {job_id} moved to dead letter after {job.attempt} attempts: {error_msg}")

                # Decrement worker load + tenant slots
                worker = await session.get(Worker, self.worker_id)
                if worker:
                    if worker.current_load > 0:
                        worker.current_load -= 1
                    tenant_slots = dict(worker.tenant_slots)
                    if job.tenant_id in tenant_slots:
                        tenant_slots[job.tenant_id] = max(0, tenant_slots[job.tenant_id] - 1)
                        if tenant_slots[job.tenant_id] == 0:
                            del tenant_slots[job.tenant_id]
                        worker.tenant_slots = tenant_slots

                await session.commit()

        except asyncio.CancelledError:
            logger.info(f"Job {job_id} execution cancelled.")
        except Exception:
            logger.exception(f"Unexpected error executing job {job_id}")
            # Mark job as failed so scheduler can retry
            try:
                async with async_session_factory() as session:
                    job = await session.get(Job, job_id)
                    if job and job.state == JobState.RUNNING:
                        job.state = JobState.FAILED
                        job.error_message = "Worker execution error"
                        await record_event(
                            session, job.id, "FAILED",
                            detail="Worker execution error (unhandled exception)",
                            attempt=job.attempt,
                            worker_id=str(self.worker_id),
                        )
                        worker = await session.get(Worker, self.worker_id)
                        if worker and worker.current_load > 0:
                            worker.current_load -= 1
                        await session.commit()
            except Exception:
                logger.exception(f"Failed to mark job {job_id} as failed")
        finally:
            self._active_jobs.pop(job_id, None)
            self._cancelled_jobs.discard(job_id)


async def run_worker(max_slots: int | None = None):
    """Entry point for running a worker."""
    worker = WorkerNode(max_slots=max_slots)
    try:
        await worker.start()
        # Keep running until cancelled
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        await worker.stop()
