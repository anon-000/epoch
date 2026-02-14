"""Initial schema — all tables for Epoch distributed job scheduler.

Revision ID: 001
Revises: None
Create Date: 2026-02-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    job_priority = sa.Enum("CRITICAL", "HIGH", "NORMAL", name="job_priority")
    job_state = sa.Enum(
        "SUBMITTED", "QUEUED", "SCHEDULED", "RUNNING", "COMPLETED",
        "FAILED", "TIMED_OUT", "CANCELLED", "CHECKPOINTED", "PREEMPTED", "DEAD_LETTER",
        name="job_state",
    )
    worker_state = sa.Enum("ONLINE", "DRAINING", "OFFLINE", name="worker_state")

    # Workers table (must be created before jobs due to FK)
    op.create_table(
        "workers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("hostname", sa.String(256), nullable=False),
        sa.Column("pid", sa.Integer, nullable=False),
        sa.Column("tenant_slots", JSONB, nullable=False, server_default="{}"),
        sa.Column("max_slots", sa.Integer, nullable=False, server_default="4"),
        sa.Column("current_load", sa.Integer, nullable=False, server_default="0"),
        sa.Column("state", worker_state, nullable=False),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Checkpoints table (must be created before jobs due to FK)
    op.create_table(
        "checkpoints",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer, nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_checkpoints_job_id", "checkpoints", ["job_id"])

    # Jobs table
    op.create_table(
        "jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("job_type", sa.String(256), nullable=False),
        sa.Column("priority", job_priority, nullable=False),
        sa.Column("state", job_state, nullable=False),
        sa.Column("attempt", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("timeout_seconds", sa.Integer, nullable=False, server_default="3600"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_worker_id", UUID(as_uuid=True), sa.ForeignKey("workers.id"), nullable=True),
        sa.Column("checkpoint_id", UUID(as_uuid=True), sa.ForeignKey("checkpoints.id"), nullable=True),
    )
    op.create_index("ix_jobs_tenant_id", "jobs", ["tenant_id"])
    op.create_index("ix_jobs_state", "jobs", ["state"])

    # Add FK from checkpoints.job_id -> jobs.id (deferred due to circular dependency)
    op.create_foreign_key("fk_checkpoints_job_id", "checkpoints", "jobs", ["job_id"], ["id"])

    # Dead letter jobs
    op.create_table(
        "dead_letter_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("final_error", sa.Text, nullable=True),
        sa.Column("total_attempts", sa.Integer, nullable=False),
        sa.Column("moved_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Scheduler leader (singleton row)
    op.create_table(
        "scheduler_leader",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("holder_id", sa.String(64), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("renewed_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Tenant configs
    op.create_table(
        "tenant_configs",
        sa.Column("tenant_id", sa.String(128), primary_key=True),
        sa.Column("max_concurrent_jobs", sa.Integer, nullable=False, server_default="10"),
        sa.Column("max_workers", sa.Integer, nullable=False, server_default="5"),
        sa.Column("priority_boost", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tenant_configs")
    op.drop_table("scheduler_leader")
    op.drop_table("dead_letter_jobs")
    op.drop_table("jobs")
    op.drop_table("checkpoints")
    op.drop_table("workers")

    sa.Enum(name="job_priority").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="job_state").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="worker_state").drop(op.get_bind(), checkfirst=True)
