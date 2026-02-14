"""
Base job interface.
All jobs must inherit from this and implement the run() method.
Jobs that support checkpointing should also implement save_state() and load_state().
"""

import json
from abc import ABC, abstractmethod


class BaseJob(ABC):
    def __init__(self):
        self._checkpoint_sequence: int = 0

    @abstractmethod
    async def run(self, payload: dict, resume_state: dict | None = None) -> dict:
        """
        Execute the job with the given payload.

        Args:
            payload: Job-specific data passed at submission time.
            resume_state: If resuming from checkpoint, the restored state dict.
                          None if this is a fresh start.

        Returns:
            A dict with the job's result data.
        """
        ...

    def supports_checkpointing(self) -> bool:
        """Override to return True if this job supports checkpointing."""
        return False

    async def save_state(self) -> dict:
        """
        Serialize the current job state for checkpointing.
        Override this in jobs that support checkpointing.
        Returns a JSON-serializable dict.
        """
        return {}

    async def load_state(self, state: dict) -> None:
        """
        Restore job state from a checkpoint.
        Override this in jobs that support checkpointing.
        """
        pass

    def get_checkpoint_data(self, state: dict) -> bytes:
        """Serialize state dict to bytes for storage."""
        return json.dumps(state).encode("utf-8")

    @staticmethod
    def parse_checkpoint_data(data: bytes) -> dict:
        """Deserialize bytes from storage to state dict."""
        return json.loads(data.decode("utf-8"))
