"""
Global audit log endpoint — query events across all jobs.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.models.job import Job
from src.models.job_event import JobEvent

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def list_events(
    event: str | None = Query(default=None, description="Filter by event type (e.g. FAILED, COMPLETED)"),
    job_id: uuid.UUID | None = Query(default=None, description="Filter by job ID"),
    job_name: str | None = Query(default=None, description="Search by job name (partial match)"),
    worker_id: str | None = Query(default=None, description="Filter by worker ID"),
    tenant_id: str | None = Query(default=None, description="Filter by tenant ID"),
    since: datetime | None = Query(default=None, description="Events after this timestamp (ISO 8601)"),
    until: datetime | None = Query(default=None, description="Events before this timestamp (ISO 8601)"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List audit log events across all jobs with optional filtering."""

    # Base query with a join to jobs for tenant_id and job name
    query = (
        select(JobEvent, Job.name.label("job_name"), Job.tenant_id.label("tenant_id"))
        .join(Job, JobEvent.job_id == Job.id)
        .order_by(JobEvent.timestamp.desc())
    )
    count_query = (
        select(func.count(JobEvent.id))
        .join(Job, JobEvent.job_id == Job.id)
    )

    # Apply filters
    if event:
        query = query.where(JobEvent.event == event)
        count_query = count_query.where(JobEvent.event == event)
    if job_id:
        query = query.where(JobEvent.job_id == job_id)
        count_query = count_query.where(JobEvent.job_id == job_id)
    if job_name:
        query = query.where(Job.name.ilike(f"%{job_name}%"))
        count_query = count_query.where(Job.name.ilike(f"%{job_name}%"))
    if worker_id:
        query = query.where(JobEvent.worker_id == worker_id)
        count_query = count_query.where(JobEvent.worker_id == worker_id)
    if tenant_id:
        query = query.where(Job.tenant_id == tenant_id)
        count_query = count_query.where(Job.tenant_id == tenant_id)
    if since:
        query = query.where(JobEvent.timestamp >= since)
        count_query = count_query.where(JobEvent.timestamp >= since)
    if until:
        query = query.where(JobEvent.timestamp <= until)
        count_query = count_query.where(JobEvent.timestamp <= until)

    total = (await session.execute(count_query)).scalar_one()
    result = await session.execute(query.offset(offset).limit(limit))
    rows = result.all()

    return {
        "total": total,
        "events": [
            {
                "id": str(row.JobEvent.id),
                "job_id": str(row.JobEvent.job_id),
                "job_name": row.job_name,
                "tenant_id": row.tenant_id,
                "event": row.JobEvent.event,
                "detail": row.JobEvent.detail,
                "attempt": row.JobEvent.attempt,
                "worker_id": row.JobEvent.worker_id,
                "timestamp": row.JobEvent.timestamp.isoformat(),
                "metadata": row.JobEvent.metadata_,
            }
            for row in rows
        ],
    }
