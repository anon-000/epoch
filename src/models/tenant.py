from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class TenantConfig(Base):
    __tablename__ = "tenant_configs"

    tenant_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    max_concurrent_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    max_workers: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    priority_boost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<TenantConfig {self.tenant_id} max_jobs={self.max_concurrent_jobs}>"
