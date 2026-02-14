from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import WorkerListResponse
from src.constants import WorkerState
from src.db.session import get_session
from src.models.worker import Worker

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("", response_model=WorkerListResponse)
async def list_workers(
    state: WorkerState | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List all registered workers."""
    query = select(Worker).order_by(Worker.registered_at.desc())
    if state:
        query = query.where(Worker.state == state)

    result = await session.execute(query)
    workers = result.scalars().all()

    return WorkerListResponse(workers=workers, total=len(workers))
