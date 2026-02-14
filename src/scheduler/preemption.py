"""
Preemption logic.

When a high-priority job arrives and all workers are busy:
1. Find the lowest-priority RUNNING job.
2. If the new job has strictly higher priority, preempt the running job.
3. Preempted job → PREEMPTED → re-queued with same priority.
4. New job gets the freed worker slot.

Only CRITICAL jobs can preempt. CRITICAL preempts HIGH and NORMAL. HIGH preempts NORMAL.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import PRIORITY_WEIGHTS, JobPriority, JobState
from src.models.job import Job
from src.queue.redis_queue import redis_queue
from src.scheduler.priority_queue import compute_priority_score

logger = logging.getLogger("epoch.scheduler.preemption")


async def find_preemptable_job(
    session: AsyncSession,
    incoming_priority: JobPriority,
) -> Job | None:
    """
    Find the lowest-priority running job that can be preempted by the incoming job.
    Returns None if no preemption is possible.
    """
    incoming_weight = PRIORITY_WEIGHTS[incoming_priority]

    # Only preempt if the incoming job is strictly higher priority
    preemptable_priorities = [
        p for p in JobPriority if PRIORITY_WEIGHTS[p] < incoming_weight
    ]
    if not preemptable_priorities:
        return None

    # Find the running job with the lowest priority (best preemption target)
    result = await session.execute(
        select(Job)
        .where(Job.state == JobState.RUNNING)
        .where(Job.priority.in_(preemptable_priorities))
        .order_by(
            # Lowest priority first (best target)
            Job.priority.asc(),
            # Among same priority, preempt the most recently started (least work done)
            Job.started_at.desc(),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def preempt_job(session: AsyncSession, job: Job) -> uuid.UUID:
    """
    Preempt a running job. Returns the freed worker_id.

    The preempted job transitions: RUNNING → PREEMPTED → QUEUED (re-queued).
    """
    freed_worker_id = job.assigned_worker_id
    logger.warning(
        f"Preempting job {job.id} ({job.name}, priority={job.priority}) "
        f"from worker {freed_worker_id}"
    )

    job.state = JobState.PREEMPTED
    job.assigned_worker_id = None
    await session.flush()

    # Re-queue the preempted job with its original priority
    job.state = JobState.QUEUED
    score = compute_priority_score(job.priority)
    await session.flush()

    await redis_queue.enqueue_job(job.id, priority_score=score)

    # Notify the worker to stop executing this job
    await redis_queue.notify_workers({
        "type": "preempt",
        "job_id": str(job.id),
        "worker_id": str(freed_worker_id),
    })

    return freed_worker_id
