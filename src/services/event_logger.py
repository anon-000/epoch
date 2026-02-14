"""
Helper to record job events from anywhere in the codebase.
"""

import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.job_event import JobEvent

logger = logging.getLogger("epoch.events")


async def record_event(
    session: AsyncSession,
    job_id: uuid.UUID,
    event: str,
    detail: str | None = None,
    attempt: int | None = None,
    worker_id: str | None = None,
    metadata: dict | None = None,
    *,
    auto_commit: bool = False,
) -> JobEvent:
    """
    Append an event to the job's audit log.

    Common event names:
      CREATED, QUEUED, SCHEDULED, RUNNING, COMPLETED,
      FAILED, RETRIED, DEAD_LETTER, CANCELLED, TIMED_OUT,
      PREEMPTED, MANUAL_RETRY
    """
    evt = JobEvent(
        job_id=job_id,
        event=event,
        detail=detail,
        attempt=attempt,
        worker_id=worker_id,
        metadata_=metadata,
        timestamp=datetime.now(timezone.utc),
    )
    session.add(evt)
    if auto_commit:
        await session.commit()
    return evt
