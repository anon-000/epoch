import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants import JobPriority, JobState
from src.db.session import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    job_type: Mapped[str] = mapped_column(String(256), nullable=False)
    priority: Mapped[JobPriority] = mapped_column(
        Enum(JobPriority, name="job_priority"), nullable=False, default=JobPriority.NORMAL
    )
    state: Mapped[JobState] = mapped_column(
        Enum(JobState, name="job_state"), nullable=False, default=JobState.SUBMITTED, index=True
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=3600)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assigned_worker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workers.id"), nullable=True
    )
    checkpoint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkpoints.id"), nullable=True
    )

    assigned_worker: Mapped["Worker | None"] = relationship(
        "Worker", back_populates="assigned_jobs", foreign_keys=[assigned_worker_id]
    )
    latest_checkpoint: Mapped["Checkpoint | None"] = relationship(
        "Checkpoint", foreign_keys=[checkpoint_id], lazy="selectin"
    )
    checkpoints: Mapped[list["Checkpoint"]] = relationship(
        "Checkpoint", back_populates="job", foreign_keys="Checkpoint.job_id"
    )

    def __repr__(self) -> str:
        return f"<Job {self.id} name={self.name} state={self.state}>"


class DeadLetterJob(Base):
    __tablename__ = "dead_letter_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    final_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["Job"] = relationship("Job")


# Forward references resolved via imports in __init__.py
from src.models.worker import Worker  # noqa: E402
from src.models.checkpoint import Checkpoint  # noqa: E402
