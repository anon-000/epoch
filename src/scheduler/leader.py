"""
Leader election using PostgreSQL advisory locks with heartbeat-based renewal.

How it works:
- Advisory lock ensures only one scheduler holds the lock per DB connection.
- The leader writes heartbeats to the scheduler_leader table every 5s.
- If the leader dies, the advisory lock is automatically released when the
  DB connection drops, and a standby scheduler acquires it.
- On takeover, the new leader rebuilds state from DB (all truth is in PostgreSQL).
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text, select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings

logger = logging.getLogger("epoch.scheduler.leader")

SCHEDULER_LOCK_ID = 123456789
LEADER_SINGLETON_ID = 1


class LeaderElection:
    def __init__(self, instance_id: str | None = None):
        self.instance_id = instance_id or str(uuid.uuid4())[:8]
        self.is_leader = False
        self._heartbeat_task: asyncio.Task | None = None

    async def try_acquire(self, session: AsyncSession) -> bool:
        """Try to acquire the advisory lock. Non-blocking."""
        result = await session.execute(
            text("SELECT pg_try_advisory_lock(:lock_id)"),
            {"lock_id": SCHEDULER_LOCK_ID},
        )
        acquired = result.scalar_one()

        if acquired and not self.is_leader:
            self.is_leader = True
            await self._write_leader_record(session)
            logger.info(f"Instance {self.instance_id} acquired scheduler leadership.")
        elif not acquired:
            self.is_leader = False

        return self.is_leader

    async def renew_heartbeat(self, session: AsyncSession) -> bool:
        """
        Renew the leader heartbeat. Called every heartbeat interval.
        Returns False if we've lost leadership.
        """
        if not self.is_leader:
            return False

        # Verify we still hold the lock
        result = await session.execute(
            text("SELECT pg_try_advisory_lock(:lock_id)"),
            {"lock_id": SCHEDULER_LOCK_ID},
        )
        still_leader = result.scalar_one()

        if still_leader:
            await self._update_heartbeat(session)
            return True
        else:
            self.is_leader = False
            logger.warning(f"Instance {self.instance_id} lost leadership!")
            return False

    async def release(self, session: AsyncSession) -> None:
        """Release the advisory lock."""
        if self.is_leader:
            await session.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": SCHEDULER_LOCK_ID},
            )
            self.is_leader = False
            logger.info(f"Instance {self.instance_id} released scheduler leadership.")

    async def _write_leader_record(self, session: AsyncSession):
        """Write or update the leader record in the scheduler_leader table."""
        now = datetime.now(timezone.utc)
        # Upsert using raw SQL for simplicity with the singleton pattern
        await session.execute(
            text("""
                INSERT INTO scheduler_leader (id, holder_id, acquired_at, renewed_at)
                VALUES (:id, :holder, :now, :now)
                ON CONFLICT (id) DO UPDATE SET
                    holder_id = :holder,
                    acquired_at = :now,
                    renewed_at = :now
            """),
            {"id": LEADER_SINGLETON_ID, "holder": self.instance_id, "now": now},
        )
        await session.commit()

    async def _update_heartbeat(self, session: AsyncSession):
        """Update the heartbeat timestamp."""
        now = datetime.now(timezone.utc)
        await session.execute(
            text("""
                UPDATE scheduler_leader
                SET renewed_at = :now
                WHERE id = :id AND holder_id = :holder
            """),
            {"id": LEADER_SINGLETON_ID, "holder": self.instance_id, "now": now},
        )
        await session.commit()

    async def get_current_leader(self, session: AsyncSession) -> dict | None:
        """Get info about the current leader (for health checks)."""
        result = await session.execute(
            text("SELECT holder_id, acquired_at, renewed_at FROM scheduler_leader WHERE id = :id"),
            {"id": LEADER_SINGLETON_ID},
        )
        row = result.first()
        if row:
            return {
                "holder_id": row[0],
                "acquired_at": row[1].isoformat() if row[1] else None,
                "renewed_at": row[2].isoformat() if row[2] else None,
            }
        return None
