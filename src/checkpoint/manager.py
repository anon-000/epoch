"""
Checkpoint manager.
Orchestrates periodic checkpoint saving during job execution and
handles recovery from the last checkpoint on job restart.
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.checkpoint.store import LocalCheckpointStore
from src.db.session import async_session_factory
from src.models.checkpoint import Checkpoint
from src.models.job import Job

logger = logging.getLogger("epoch.checkpoint.manager")


class CheckpointManager:
    def __init__(self):
        self.store = LocalCheckpointStore()

    async def save_checkpoint(self, job_id: uuid.UUID, sequence: int, data: bytes) -> Checkpoint:
        """Save a checkpoint: write blob to store, record metadata in DB."""
        job_id_str = str(job_id)

        # Write to storage
        storage_path = await self.store.save(job_id_str, sequence, data)
        size_bytes = len(data)

        # Record in database
        async with async_session_factory() as session:
            checkpoint = Checkpoint(
                job_id=job_id,
                sequence_number=sequence,
                storage_path=storage_path,
                size_bytes=size_bytes,
            )
            session.add(checkpoint)

            # Update job's latest checkpoint reference
            job = await session.get(Job, job_id)
            if job:
                job.checkpoint_id = checkpoint.id
            await session.commit()
            await session.refresh(checkpoint)

        logger.info(f"Checkpoint saved for job {job_id}: seq={sequence}, size={size_bytes}")
        return checkpoint

    async def load_latest_checkpoint(self, job_id: uuid.UUID) -> tuple[int, bytes] | None:
        """
        Load the latest checkpoint for a job.
        Returns (sequence_number, data) or None if no checkpoint exists.
        """
        async with async_session_factory() as session:
            job = await session.get(Job, job_id)
            if not job or not job.checkpoint_id:
                return None

            checkpoint = await session.get(Checkpoint, job.checkpoint_id)
            if not checkpoint:
                return None

        try:
            data = await self.store.load(checkpoint.storage_path)
            logger.info(
                f"Loaded checkpoint for job {job_id}: seq={checkpoint.sequence_number}, "
                f"size={len(data)}"
            )
            return checkpoint.sequence_number, data
        except FileNotFoundError:
            logger.warning(f"Checkpoint file missing for job {job_id}: {checkpoint.storage_path}")
            return None

    async def cleanup_checkpoints(self, job_id: uuid.UUID, keep_latest: int = 1) -> int:
        """
        Clean up old checkpoints for a job, keeping the latest N.
        Returns number of checkpoints deleted.
        """
        from sqlalchemy import select

        async with async_session_factory() as session:
            result = await session.execute(
                select(Checkpoint)
                .where(Checkpoint.job_id == job_id)
                .order_by(Checkpoint.sequence_number.desc())
            )
            all_checkpoints = result.scalars().all()

            if len(all_checkpoints) <= keep_latest:
                return 0

            to_delete = all_checkpoints[keep_latest:]
            deleted = 0
            for cp in to_delete:
                await self.store.delete(cp.storage_path)
                await session.delete(cp)
                deleted += 1

            await session.commit()

        logger.info(f"Cleaned up {deleted} old checkpoints for job {job_id}")
        return deleted


# Singleton
checkpoint_manager = CheckpointManager()
