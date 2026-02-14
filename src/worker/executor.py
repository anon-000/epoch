"""
Job executor — runs jobs with checkpoint support.
Phase 1-4: In-process execution using importlib.
Phase 5 will add subprocess isolation with resource limits.
"""

import asyncio
import importlib
import logging
import traceback
import uuid

from src.checkpoint.manager import checkpoint_manager
from src.config import settings

logger = logging.getLogger("epoch.worker.executor")


class JobExecutor:
    async def execute(
        self,
        job_type: str,
        payload: dict,
        job_id: uuid.UUID | None = None,
    ) -> dict:
        """
        Execute a job by importing the job class and calling its run() method.
        Supports checkpointing for long-running jobs.

        job_type format: "module.path:ClassName" e.g. "jobs.data_processing:DataProcessingJob"
        """
        try:
            # Handle aliases for convenience
            if job_type == "data_processing":
                job_type = "jobs.data_processing:DataProcessingJob"
            elif job_type == "long_running":
                job_type = "jobs.long_running:LongRunningJob"

            logger.info(f"Starting execution of job_type: '{job_type}' for job_id: {job_id}")
            if ":" not in job_type:
                raise ValueError(f"Invalid job_type '{job_type}'. Expected format 'module.path:ClassName'")

            module_path, class_name = job_type.rsplit(":", 1)
            module = importlib.import_module(module_path)
            job_class = getattr(module, class_name)

            job_instance = job_class()

            # Check if we should resume from a checkpoint
            resume_state = None
            if job_id and job_instance.supports_checkpointing():
                try:
                    checkpoint_data = await checkpoint_manager.load_latest_checkpoint(job_id)
                    if checkpoint_data:
                        # Ensure we have a tuple of (seq, data)
                        if isinstance(checkpoint_data, (tuple, list)) and len(checkpoint_data) == 2:
                            seq, data = checkpoint_data
                            resume_state = job_instance.parse_checkpoint_data(data)
                            job_instance._checkpoint_sequence = seq
                            logger.info(f"Resuming job {job_id} from checkpoint seq={seq}")
                        else:
                            logger.warning(f"Invalid checkpoint data format for job {job_id}: {checkpoint_data}")
                except Exception as e:
                    logger.error(f"Failed to load checkpoint for job {job_id}: {e}")
                    # Continue without resuming if checkpoint load fails

            # Run with periodic checkpointing if supported
            if job_id and job_instance.supports_checkpointing():
                result = await self._execute_with_checkpointing(
                    job_instance, payload, job_id, resume_state
                )
            else:
                result = await job_instance.run(payload, resume_state=resume_state)

            return {"success": True, "result": result}

        except Exception as e:
            logger.exception(f"Job execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    async def _execute_with_checkpointing(
        self,
        job_instance,
        payload: dict,
        job_id: uuid.UUID,
        resume_state: dict | None,
    ) -> dict:
        """Execute a job with periodic checkpoint saves."""
        checkpoint_task = None

        async def periodic_checkpoint():
            """Periodically save checkpoints while the job is running."""
            while True:
                await asyncio.sleep(settings.checkpoint_interval)
                try:
                    state = await job_instance.save_state()
                    data = job_instance.get_checkpoint_data(state)
                    job_instance._checkpoint_sequence += 1
                    await checkpoint_manager.save_checkpoint(
                        job_id, job_instance._checkpoint_sequence, data
                    )
                    # Clean up old checkpoints, keep latest 2
                    await checkpoint_manager.cleanup_checkpoints(job_id, keep_latest=2)
                except Exception:
                    logger.exception(f"Checkpoint save failed for job {job_id}")

        try:
            # Start periodic checkpointing in background
            checkpoint_task = asyncio.create_task(periodic_checkpoint())
            result = await job_instance.run(payload, resume_state=resume_state)
            return result
        finally:
            if checkpoint_task:
                checkpoint_task.cancel()
                try:
                    await checkpoint_task
                except asyncio.CancelledError:
                    pass

            # Final checkpoint on completion
            try:
                state = await job_instance.save_state()
                data = job_instance.get_checkpoint_data(state)
                job_instance._checkpoint_sequence += 1
                await checkpoint_manager.save_checkpoint(
                    job_id, job_instance._checkpoint_sequence, data
                )
            except Exception:
                logger.exception(f"Final checkpoint save failed for job {job_id}")
