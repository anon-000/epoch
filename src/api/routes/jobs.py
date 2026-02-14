import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import JobListResponse, JobResponse, JobSubmitRequest
from src.constants import VALID_TRANSITIONS, JobState
from src.db.session import get_session
from src.models.job import Job
from src.models.job_event import JobEvent
from src.queue.redis_queue import redis_queue
from src.scheduler.priority_queue import compute_priority_score
from src.services.event_logger import record_event

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def submit_job(req: JobSubmitRequest, session: AsyncSession = Depends(get_session)):
    """Submit a new job for execution."""
    job = Job(
        tenant_id=req.tenant_id,
        name=req.name,
        job_type=req.job_type,
        payload=req.payload,
        priority=req.priority,
        state=JobState.SUBMITTED,
        max_retries=req.max_retries,
        timeout_seconds=req.timeout_seconds,
    )
    session.add(job)
    await session.flush()  # get the job.id

    # Record creation event
    await record_event(session, job.id, "CREATED", detail=f"Job submitted: {req.name}")

    # Transition to QUEUED
    job.state = JobState.QUEUED
    await record_event(session, job.id, "QUEUED", detail="Enqueued for scheduling")
    await session.commit()
    await session.refresh(job)

    # Push to Redis priority queue with computed score
    score = compute_priority_score(job.priority)
    await redis_queue.enqueue_job(job.id, priority_score=score)

    return job


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Get a job by ID."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("", response_model=JobListResponse)
async def list_jobs(
    tenant_id: str | None = None,
    state: JobState | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List jobs with optional filters."""
    query = select(Job).order_by(Job.created_at.desc())
    count_query = select(func.count(Job.id))

    if tenant_id:
        query = query.where(Job.tenant_id == tenant_id)
        count_query = count_query.where(Job.tenant_id == tenant_id)
    if state:
        query = query.where(Job.state == state)
        count_query = count_query.where(Job.state == state)

    total = (await session.execute(count_query)).scalar_one()
    result = await session.execute(query.offset(offset).limit(limit))
    jobs = result.scalars().all()

    return JobListResponse(jobs=jobs, total=total)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Cancel a job."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if JobState.CANCELLED not in VALID_TRANSITIONS.get(job.state, set()):
        raise HTTPException(
            status_code=409, detail=f"Cannot cancel job in state {job.state}"
        )

    job.state = JobState.CANCELLED
    job.completed_at = datetime.now(timezone.utc)
    await record_event(session, job.id, "CANCELLED", detail="Job cancelled by user")
    await session.commit()
    await session.refresh(job)

    # Remove from queue if still queued, notify workers if running
    await redis_queue.remove_job(job_id)
    await redis_queue.notify_workers({"type": "cancel", "job_id": str(job_id)})

    return job


RETRYABLE_STATES = {JobState.FAILED, JobState.TIMED_OUT, JobState.DEAD_LETTER}


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Retry a failed, timed-out, or dead-lettered job."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.state not in RETRYABLE_STATES:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot retry job in state {job.state}. Must be FAILED, TIMED_OUT, or DEAD_LETTER.",
        )

    # Record manual retry event before resetting state
    await record_event(
        session, job.id, "MANUAL_RETRY",
        detail=f"Manual retry from state {job.state.value}",
        attempt=job.attempt,
    )

    # Reset job for retry
    job.state = JobState.QUEUED
    job.attempt = 0
    job.error_message = None
    job.assigned_worker_id = None
    job.scheduled_at = None
    job.started_at = None
    job.completed_at = None
    await record_event(session, job.id, "QUEUED", detail="Re-queued after manual retry")
    await session.commit()
    await session.refresh(job)

    # Re-enqueue in Redis
    score = compute_priority_score(job.priority)
    await redis_queue.enqueue_job(job.id, priority_score=score)

    return job


@router.get("/{job_id}/events")
async def get_job_events(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Get the full event history/audit log for a job."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = await session.execute(
        select(JobEvent)
        .where(JobEvent.job_id == job_id)
        .order_by(JobEvent.timestamp.asc())
    )
    events = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "event": e.event,
            "detail": e.detail,
            "attempt": e.attempt,
            "worker_id": e.worker_id,
            "timestamp": e.timestamp.isoformat(),
            "metadata": e.metadata_,
        }
        for e in events
    ]
