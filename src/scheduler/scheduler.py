"""
Core scheduler loop.
Dequeues jobs from the priority queue and assigns them to workers.
Supports preemption, leader election, timeout detection, retry with
exponential backoff, dead letter queue, and tenant-aware fair-share scheduling.
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.constants import JobState, WorkerState
from src.db.session import async_session_factory, init_db
from src.models.job import Job, DeadLetterJob
from src.models.tenant import TenantConfig
from src.models.worker import Worker
from src.queue.redis_queue import redis_queue
from src.scheduler.leader import LeaderElection
from src.scheduler.preemption import find_preemptable_job, preempt_job
from src.services.event_logger import record_event
from src.scheduler.priority_queue import compute_priority_score

logger = logging.getLogger("epoch.scheduler")

# Default tenant limits when no TenantConfig exists
DEFAULT_MAX_CONCURRENT_JOBS = 10


def compute_retry_delay(attempt: int) -> float:
    """Exponential backoff with jitter: min(base * 2^attempt + jitter, max_delay)."""
    delay = settings.retry_base_delay * (2 ** attempt)
    jitter = random.uniform(0, settings.retry_base_delay)
    return min(delay + jitter, settings.retry_max_delay)


class Scheduler:
    def __init__(self):
        self.leader = LeaderElection()
        self._running = False
        self._heartbeat_counter = 0
        self._tenant_configs: dict[str, TenantConfig] = {}

    async def start(self):
        """Main scheduler loop."""
        logger.info(f"Scheduler starting (instance={self.leader.instance_id})...")
        await init_db()
        await redis_queue.connect()
        self._running = True

        # Rebuild state from DB
        async with async_session_factory() as session:
            await self._rebuild_queue_from_db(session)
            await self._load_tenant_configs(session)

        while self._running:
            try:
                async with async_session_factory() as session:
                    if not self.leader.is_leader:
                        acquired = await self.leader.try_acquire(session)
                        if not acquired:
                            await asyncio.sleep(settings.scheduler_loop_interval)
                            continue
                    else:
                        self._heartbeat_counter += 1
                        if self._heartbeat_counter >= int(
                            settings.leader_heartbeat_interval / settings.scheduler_loop_interval
                        ):
                            self._heartbeat_counter = 0
                            still_leader = await self.leader.renew_heartbeat(session)
                            if not still_leader:
                                continue

                    await self._schedule_cycle(session)

            except Exception:
                logger.exception("Error in scheduler loop")

            await asyncio.sleep(settings.scheduler_loop_interval)

    async def stop(self):
        self._running = False
        logger.info("Scheduler stopping...")

    async def _load_tenant_configs(self, session: AsyncSession):
        """Load tenant configurations into memory."""
        result = await session.execute(select(TenantConfig))
        configs = result.scalars().all()
        self._tenant_configs = {c.tenant_id: c for c in configs}
        logger.info(f"Loaded {len(self._tenant_configs)} tenant configs.")

    def _get_tenant_max_concurrent(self, tenant_id: str) -> int:
        config = self._tenant_configs.get(tenant_id)
        return config.max_concurrent_jobs if config else DEFAULT_MAX_CONCURRENT_JOBS

    async def _get_tenant_running_count(self, session: AsyncSession, tenant_id: str) -> int:
        """Count jobs currently SCHEDULED or RUNNING for a tenant."""
        result = await session.execute(
            select(func.count(Job.id))
            .where(Job.tenant_id == tenant_id)
            .where(Job.state.in_([JobState.SCHEDULED, JobState.RUNNING]))
        )
        return result.scalar_one()

    async def _rebuild_queue_from_db(self, session: AsyncSession):
        result = await session.execute(
            select(Job).where(Job.state == JobState.QUEUED)
        )
        queued_jobs = result.scalars().all()
        for job in queued_jobs:
            score = compute_priority_score(job.priority)
            await redis_queue.enqueue_job(job.id, priority_score=score)
        if queued_jobs:
            logger.info(f"Rebuilt Redis queue with {len(queued_jobs)} jobs from DB.")

    async def _schedule_cycle(self, session: AsyncSession):
        """One scheduling cycle: detect failures, dequeue, assign."""
        await self._detect_dead_workers(session)
        await self._detect_timed_out_jobs(session)

        # Periodically refresh tenant configs
        await self._load_tenant_configs(session)

        assigned = 0
        deferred_jobs: list[tuple[uuid.UUID, float]] = []

        while True:
            job_id_str = await redis_queue.dequeue_job()
            if not job_id_str:
                break

            job_id = uuid.UUID(job_id_str)
            job = await session.get(Job, job_id)
            if not job or job.state != JobState.QUEUED:
                continue

            # Tenant quota check
            max_concurrent = self._get_tenant_max_concurrent(job.tenant_id)
            current_count = await self._get_tenant_running_count(session, job.tenant_id)
            if current_count >= max_concurrent:
                # Tenant at capacity — defer this job
                score = compute_priority_score(job.priority)
                deferred_jobs.append((job_id, score))
                logger.debug(
                    f"Job {job.id} deferred: tenant {job.tenant_id} at quota "
                    f"({current_count}/{max_concurrent})"
                )
                continue

            worker = await self._find_available_worker(session)

            if not worker:
                victim = await find_preemptable_job(session, job.priority)
                if victim:
                    freed_worker_id = await preempt_job(session, victim)
                    worker = await session.get(Worker, freed_worker_id)
                else:
                    score = compute_priority_score(job.priority)
                    deferred_jobs.append((job_id, score))
                    break

            # Assign the job
            job.state = JobState.SCHEDULED
            job.assigned_worker_id = worker.id
            job.scheduled_at = datetime.now(timezone.utc)
            worker.current_load += 1

            # Track tenant slot on worker
            tenant_slots = dict(worker.tenant_slots)
            tenant_slots[job.tenant_id] = tenant_slots.get(job.tenant_id, 0) + 1
            worker.tenant_slots = tenant_slots

            await record_event(
                session, job.id, "SCHEDULED",
                detail=f"Assigned to worker {worker.id} ({worker.hostname})",
                attempt=job.attempt,
                worker_id=str(worker.id),
            )

            await session.commit()

            await redis_queue.notify_workers({
                "type": "job_assigned",
                "job_id": str(job.id),
                "worker_id": str(worker.id),
            })

            assigned += 1
            logger.info(
                f"Assigned job {job.id} ({job.name}, priority={job.priority}, "
                f"tenant={job.tenant_id}) to worker {worker.id}"
            )

        # Put deferred jobs back into the queue
        for job_id, score in deferred_jobs:
            await redis_queue.enqueue_job(job_id, priority_score=score)

        if assigned:
            logger.info(f"Scheduling cycle: {assigned} jobs assigned.")

    async def _find_available_worker(self, session: AsyncSession) -> Worker | None:
        result = await session.execute(
            select(Worker)
            .where(Worker.state == WorkerState.ONLINE)
            .where(Worker.current_load < Worker.max_slots)
            .order_by(Worker.current_load.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _detect_dead_workers(self, session: AsyncSession):
        cutoff = datetime.now(timezone.utc).timestamp() - settings.worker_heartbeat_timeout
        cutoff_dt = datetime.fromtimestamp(cutoff, tz=timezone.utc)

        result = await session.execute(
            select(Worker)
            .where(Worker.state == WorkerState.ONLINE)
            .where(Worker.last_heartbeat < cutoff_dt)
        )
        dead_workers = result.scalars().all()

        for worker in dead_workers:
            logger.warning(f"Worker {worker.id} ({worker.hostname}) missed heartbeat, marking OFFLINE.")
            worker.state = WorkerState.OFFLINE

            jobs_result = await session.execute(
                select(Job)
                .where(Job.assigned_worker_id == worker.id)
                .where(Job.state.in_([JobState.SCHEDULED, JobState.RUNNING]))
            )
            orphaned_jobs = jobs_result.scalars().all()
            for job in orphaned_jobs:
                await self._handle_job_failure(
                    session, job, error="Worker died (missed heartbeat)"
                )

        if dead_workers:
            await session.commit()

    async def _detect_timed_out_jobs(self, session: AsyncSession):
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(Job).where(Job.state == JobState.RUNNING).where(Job.started_at.isnot(None))
        )
        running_jobs = result.scalars().all()

        timed_out = 0
        for job in running_jobs:
            elapsed = (now - job.started_at).total_seconds()
            if elapsed > job.timeout_seconds:
                logger.warning(
                    f"Job {job.id} timed out after {elapsed:.0f}s (limit={job.timeout_seconds}s)"
                )
                job.state = JobState.TIMED_OUT
                await record_event(
                    session, job.id, "TIMED_OUT",
                    detail=f"Timed out after {elapsed:.0f}s (limit={job.timeout_seconds}s)",
                    attempt=job.attempt,
                    worker_id=str(job.assigned_worker_id) if job.assigned_worker_id else None,
                )
                await self._handle_job_failure(session, job, error=f"Timed out after {elapsed:.0f}s")
                timed_out += 1

        if timed_out:
            await session.commit()

    async def _handle_job_failure(self, session: AsyncSession, job: Job, error: str):
        job.error_message = error
        old_worker_id = job.assigned_worker_id
        job.assigned_worker_id = None

        if job.attempt < job.max_retries:
            delay = compute_retry_delay(job.attempt)
            job.state = JobState.QUEUED
            job.scheduled_at = None
            await record_event(
                session, job.id, "RETRIED",
                detail=f"Auto-retry by scheduler (attempt {job.attempt}/{job.max_retries}): {error}",
                attempt=job.attempt,
                worker_id=str(old_worker_id) if old_worker_id else None,
            )
            logger.info(
                f"Re-queuing job {job.id} for retry (attempt {job.attempt}/{job.max_retries}, "
                f"delay={delay:.1f}s)"
            )
            score = compute_priority_score(job.priority)
            await redis_queue.enqueue_job(job.id, priority_score=score)
        else:
            job.state = JobState.DEAD_LETTER
            dead_letter = DeadLetterJob(
                job_id=job.id,
                final_error=error,
                total_attempts=job.attempt,
            )
            session.add(dead_letter)
            await record_event(
                session, job.id, "DEAD_LETTER",
                detail=f"Moved to dead letter after {job.attempt} attempts: {error}",
                attempt=job.attempt,
                worker_id=str(old_worker_id) if old_worker_id else None,
            )
            logger.error(
                f"Job {job.id} moved to dead letter after {job.attempt} attempts: {error}"
            )

        # Decrement worker load and tenant slot
        if old_worker_id:
            worker = await session.get(Worker, old_worker_id)
            if worker:
                if worker.current_load > 0:
                    worker.current_load -= 1
                # Decrement tenant slot
                tenant_slots = dict(worker.tenant_slots)
                if job.tenant_id in tenant_slots:
                    tenant_slots[job.tenant_id] = max(0, tenant_slots[job.tenant_id] - 1)
                    if tenant_slots[job.tenant_id] == 0:
                        del tenant_slots[job.tenant_id]
                    worker.tenant_slots = tenant_slots


async def run_scheduler():
    """Entry point for running the scheduler."""
    scheduler = Scheduler()
    try:
        await scheduler.start()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await scheduler.stop()
