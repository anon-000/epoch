import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants import WorkerState
from src.db.session import Base


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hostname: Mapped[str] = mapped_column(String(256), nullable=False)
    pid: Mapped[int] = mapped_column(Integer, nullable=False)
    tenant_slots: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    max_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    current_load: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    state: Mapped[WorkerState] = mapped_column(
        Enum(WorkerState, name="worker_state"), nullable=False, default=WorkerState.ONLINE
    )
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    assigned_jobs: Mapped[list["Job"]] = relationship(
        "Job", back_populates="assigned_worker", foreign_keys="Job.assigned_worker_id"
    )

    def __repr__(self) -> str:
        return f"<Worker {self.id} host={self.hostname} state={self.state}>"


from src.models.job import Job  # noqa: E402
