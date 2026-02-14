"""
Metrics and observability endpoints.
Exposes system-wide stats for monitoring: job latencies, queue depth,
worker utilization, per-tenant breakdowns, and checkpoint stats.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import JobState, WorkerState
from src.db.session import get_session
from src.models.job import Job, DeadLetterJob
from src.models.worker import Worker
from src.models.checkpoint import Checkpoint
from src.queue.redis_queue import redis_queue

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_metrics(session: AsyncSession = Depends(get_session)):
    """Comprehensive metrics endpoint."""
    now = datetime.now(timezone.utc)

    # --- Job Metrics ---
    state_counts_result = await session.execute(
        select(Job.state, func.count(Job.id)).group_by(Job.state)
    )
    job_state_counts = {row[0].value: row[1] for row in state_counts_result}

    total_jobs = sum(job_state_counts.values())

    # Average job latency (time from SUBMITTED to COMPLETED)
    latency_result = await session.execute(
        select(func.avg(
            func.extract("epoch", Job.completed_at) - func.extract("epoch", Job.created_at)
        ))
        .where(Job.state == JobState.COMPLETED)
        .where(Job.completed_at.isnot(None))
    )
    avg_latency = latency_result.scalar_one()

    # Average queue wait time (time from created to started)
    wait_result = await session.execute(
        select(func.avg(
            func.extract("epoch", Job.started_at) - func.extract("epoch", Job.created_at)
        ))
        .where(Job.started_at.isnot(None))
    )
    avg_wait_time = wait_result.scalar_one()

    # Jobs completed in last hour
    from datetime import timedelta
    one_hour_ago = now - timedelta(hours=1)
    throughput_result = await session.execute(
        select(func.count(Job.id))
        .where(Job.state == JobState.COMPLETED)
        .where(Job.completed_at >= one_hour_ago)
    )
    jobs_completed_last_hour = throughput_result.scalar_one()

    # Failure rate
    failed_count = job_state_counts.get("FAILED", 0) + job_state_counts.get("DEAD_LETTER", 0)
    completed_count = job_state_counts.get("COMPLETED", 0)
    failure_rate = (
        failed_count / (failed_count + completed_count) if (failed_count + completed_count) > 0 else 0
    )

    # --- Queue Metrics ---
    queue_depth = await redis_queue.queue_length()

    # --- Worker Metrics ---
    worker_result = await session.execute(
        select(
            Worker.state,
            func.count(Worker.id),
            func.sum(Worker.current_load),
            func.sum(Worker.max_slots),
        ).group_by(Worker.state)
    )
    worker_stats = {}
    total_capacity = 0
    total_load = 0
    for row in worker_result:
        state = row[0].value
        worker_stats[state] = {
            "count": row[1],
            "current_load": row[2] or 0,
            "max_slots": row[3] or 0,
        }
        if row[0] == WorkerState.ONLINE:
            total_capacity = row[3] or 0
            total_load = row[2] or 0

    utilization = total_load / total_capacity if total_capacity > 0 else 0

    # --- Per-Tenant Metrics ---
    tenant_result = await session.execute(
        select(
            Job.tenant_id,
            Job.state,
            func.count(Job.id),
        ).group_by(Job.tenant_id, Job.state)
    )
    tenant_metrics: dict[str, dict] = {}
    for row in tenant_result:
        tenant_id = row[0]
        if tenant_id not in tenant_metrics:
            tenant_metrics[tenant_id] = {}
        tenant_metrics[tenant_id][row[1].value] = row[2]

    # --- Dead Letter Metrics ---
    dead_letter_count = (
        await session.execute(select(func.count(DeadLetterJob.id)))
    ).scalar_one()

    # --- Checkpoint Metrics ---
    checkpoint_result = await session.execute(
        select(func.count(Checkpoint.id), func.sum(Checkpoint.size_bytes))
    )
    checkpoint_row = checkpoint_result.first()
    total_checkpoints = checkpoint_row[0] or 0
    total_checkpoint_bytes = checkpoint_row[1] or 0

    return {
        "timestamp": now.isoformat(),
        "jobs": {
            "total": total_jobs,
            "by_state": job_state_counts,
            "avg_latency_seconds": round(avg_latency, 2) if avg_latency else None,
            "avg_wait_time_seconds": round(avg_wait_time, 2) if avg_wait_time else None,
            "throughput_last_hour": jobs_completed_last_hour,
            "failure_rate": round(failure_rate, 4),
        },
        "queue": {
            "depth": queue_depth,
        },
        "workers": {
            "by_state": worker_stats,
            "total_capacity": total_capacity,
            "total_load": total_load,
            "utilization": round(utilization, 4),
        },
        "tenants": tenant_metrics,
        "dead_letter": {
            "total": dead_letter_count,
        },
        "checkpoints": {
            "total": total_checkpoints,
            "total_size_bytes": total_checkpoint_bytes,
        },
    }
