from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class SchedulerLeader(Base):
    __tablename__ = "scheduler_leader"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    holder_id: Mapped[str] = mapped_column(String(64), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    renewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
