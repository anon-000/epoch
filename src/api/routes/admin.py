from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.constants import JobState
from src.db.session import get_session
from src.models.job import DeadLetterJob, Job
from src.models.tenant import TenantConfig
from src.queue.redis_queue import redis_queue
from src.scheduler.leader import LeaderElection

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("epoch.api")


# --- Health & Stats ---

@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/queue/stats")
async def queue_stats(session: AsyncSession = Depends(get_session)):
    length = await redis_queue.queue_length()
    upcoming = await redis_queue.peek_queue(5)

    result = await session.execute(
        select(Job.state, func.count(Job.id)).group_by(Job.state)
    )
    state_counts = {row[0].value: row[1] for row in result}

    # Per-tenant running counts
    tenant_result = await session.execute(
        select(Job.tenant_id, func.count(Job.id))
        .where(Job.state.in_([JobState.SCHEDULED, JobState.RUNNING]))
        .group_by(Job.tenant_id)
    )
    tenant_counts = {row[0]: row[1] for row in tenant_result}

    return {
        "queue_length": length,
        "upcoming_jobs": upcoming,
        "job_state_counts": state_counts,
        "tenant_running_counts": tenant_counts,
    }


# --- Dead Letter ---

@router.get("/dead-letter")
async def list_dead_letter_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    count = (await session.execute(select(func.count(DeadLetterJob.id)))).scalar_one()
    result = await session.execute(
        select(DeadLetterJob)
        .order_by(DeadLetterJob.moved_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = result.scalars().all()

    return {
        "total": count,
        "items": [
            {
                "id": str(dl.id),
                "job_id": str(dl.job_id),
                "final_error": dl.final_error,
                "total_attempts": dl.total_attempts,
                "moved_at": dl.moved_at.isoformat(),
            }
            for dl in items
        ],
    }


# --- Leader ---

@router.get("/leader")
async def get_leader(session: AsyncSession = Depends(get_session)):
    leader = LeaderElection()
    info = await leader.get_current_leader(session)
    return {"leader": info}


# --- Tenant Management ---

class TenantConfigRequest(BaseModel):
    tenant_id: str = Field(..., max_length=128)
    max_concurrent_jobs: int = Field(default=10, ge=1, le=1000)
    max_workers: int = Field(default=5, ge=1, le=100)
    priority_boost: int = Field(default=0, ge=0, le=10)


class TenantConfigResponse(BaseModel):
    tenant_id: str
    max_concurrent_jobs: int
    max_workers: int
    priority_boost: int

    model_config = {"from_attributes": True}


@router.post("/tenants", response_model=TenantConfigResponse, status_code=201)
async def create_tenant_config(req: TenantConfigRequest, session: AsyncSession = Depends(get_session)):
    existing = await session.get(TenantConfig, req.tenant_id)
    if existing:
        raise HTTPException(status_code=409, detail="Tenant config already exists")

    config = TenantConfig(
        tenant_id=req.tenant_id,
        max_concurrent_jobs=req.max_concurrent_jobs,
        max_workers=req.max_workers,
        priority_boost=req.priority_boost,
    )
    session.add(config)
    try:
        await session.commit()
        await session.refresh(config)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Tenant config already exists (duplicate ID)")
    except Exception as e:
        logger.error(f"Error creating tenant: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    
    return config


@router.put("/tenants/{tenant_id}", response_model=TenantConfigResponse)
async def update_tenant_config(
    tenant_id: str, req: TenantConfigRequest, session: AsyncSession = Depends(get_session)
):
    config = await session.get(TenantConfig, tenant_id)
    if not config:
        raise HTTPException(status_code=404, detail="Tenant config not found")

    config.max_concurrent_jobs = req.max_concurrent_jobs
    config.max_workers = req.max_workers
    config.priority_boost = req.priority_boost
    await session.commit()
    await session.refresh(config)
    return config


@router.get("/tenants", response_model=list[TenantConfigResponse])
async def list_tenants(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(TenantConfig))
    return result.scalars().all()


@router.get("/tenants/{tenant_id}", response_model=TenantConfigResponse)
async def get_tenant(tenant_id: str, session: AsyncSession = Depends(get_session)):
    config = await session.get(TenantConfig, tenant_id)
    if not config:
        raise HTTPException(status_code=404, detail="Tenant config not found")
    return config
