"""
Worker heartbeat sender.
Periodically updates the worker's last_heartbeat timestamp in PostgreSQL.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.constants import WorkerState
from src.db.session import async_session_factory
from src.models.worker import Worker

logger = logging.getLogger("epoch.worker.heartbeat")


class HeartbeatSender:
    def __init__(self, worker_id: uuid.UUID):
        self.worker_id = worker_id
        self._running = False

    async def start(self):
        """Send heartbeats on a loop."""
        self._running = True
        logger.info(f"Heartbeat sender started for worker {self.worker_id}")

        while self._running:
            try:
                async with async_session_factory() as session:
                    worker = await session.get(Worker, self.worker_id)
                    if worker:
                        worker.last_heartbeat = datetime.now(timezone.utc)
                        if worker.state == WorkerState.OFFLINE:
                            worker.state = WorkerState.ONLINE
                            logger.info(f"Worker {self.worker_id} recovered from OFFLINE state.")
                        await session.commit()
            except Exception:
                logger.exception("Heartbeat send failed")

            await asyncio.sleep(settings.worker_heartbeat_interval)

    def stop(self):
        self._running = False
