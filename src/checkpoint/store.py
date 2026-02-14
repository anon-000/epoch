"""
Checkpoint storage backends.
- LocalCheckpointStore: stores checkpoints on local filesystem.
- S3CheckpointStore: placeholder for S3/MinIO (future).
"""

import logging
import os
from abc import ABC, abstractmethod

from src.config import settings

logger = logging.getLogger("epoch.checkpoint.store")


class CheckpointStore(ABC):
    @abstractmethod
    async def save(self, job_id: str, sequence: int, data: bytes) -> str:
        """Save checkpoint data. Returns the storage path."""
        ...

    @abstractmethod
    async def load(self, storage_path: str) -> bytes:
        """Load checkpoint data from path."""
        ...

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Delete a checkpoint file."""
        ...

    @abstractmethod
    async def list_checkpoints(self, job_id: str) -> list[str]:
        """List all checkpoint paths for a job."""
        ...


class LocalCheckpointStore(CheckpointStore):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or settings.checkpoint_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _job_dir(self, job_id: str) -> str:
        return os.path.join(self.base_dir, job_id)

    def _checkpoint_path(self, job_id: str, sequence: int) -> str:
        return os.path.join(self._job_dir(job_id), f"checkpoint_{sequence:06d}.bin")

    async def save(self, job_id: str, sequence: int, data: bytes) -> str:
        job_dir = self._job_dir(job_id)
        os.makedirs(job_dir, exist_ok=True)

        path = self._checkpoint_path(job_id, sequence)
        with open(path, "wb") as f:
            f.write(data)

        logger.info(f"Checkpoint saved: {path} ({len(data)} bytes)")
        return path

    async def load(self, storage_path: str) -> bytes:
        if not os.path.exists(storage_path):
            raise FileNotFoundError(f"Checkpoint not found: {storage_path}")

        with open(storage_path, "rb") as f:
            data = f.read()

        logger.info(f"Checkpoint loaded: {storage_path} ({len(data)} bytes)")
        return data

    async def delete(self, storage_path: str) -> None:
        if os.path.exists(storage_path):
            os.remove(storage_path)
            logger.info(f"Checkpoint deleted: {storage_path}")

    async def list_checkpoints(self, job_id: str) -> list[str]:
        job_dir = self._job_dir(job_id)
        if not os.path.exists(job_dir):
            return []
        files = sorted(
            f for f in os.listdir(job_dir) if f.startswith("checkpoint_") and f.endswith(".bin")
        )
        return [os.path.join(job_dir, f) for f in files]

    async def cleanup_job(self, job_id: str) -> int:
        """Delete all checkpoints for a job. Returns number of files deleted."""
        paths = await self.list_checkpoints(job_id)
        for path in paths:
            await self.delete(path)

        job_dir = self._job_dir(job_id)
        if os.path.exists(job_dir) and not os.listdir(job_dir):
            os.rmdir(job_dir)

        return len(paths)
