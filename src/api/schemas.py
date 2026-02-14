import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.constants import JobPriority, JobState, WorkerState


# --- Job Schemas ---

class JobSubmitRequest(BaseModel):
    name: str = Field(..., max_length=256)
    tenant_id: str = Field(..., max_length=128)
    job_type: str = Field(..., max_length=256)
    payload: dict = Field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = Field(default=3, ge=0, le=100)
    timeout_seconds: int = Field(default=3600, ge=1, le=86400)


class JobResponse(BaseModel):
    id: uuid.UUID
    name: str
    tenant_id: str
    job_type: str
    payload: dict
    priority: JobPriority
    state: JobState
    attempt: int
    max_retries: int
    timeout_seconds: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    scheduled_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    assigned_worker_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int


# --- Worker Schemas ---

class WorkerResponse(BaseModel):
    id: uuid.UUID
    hostname: str
    pid: int
    max_slots: int
    current_load: int
    state: WorkerState
    last_heartbeat: datetime
    registered_at: datetime

    model_config = {"from_attributes": True}


class WorkerListResponse(BaseModel):
    workers: list[WorkerResponse]
    total: int
