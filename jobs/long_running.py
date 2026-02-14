"""
Sample job: simulates a long-running computation with checkpointing support.
Runs for a configurable number of steps. On resume from checkpoint, skips
already-completed steps.
"""

import asyncio
import logging

from jobs.base import BaseJob

logger = logging.getLogger("epoch.jobs.long_running")


class LongRunningJob(BaseJob):
    def __init__(self):
        super().__init__()
        self.current_step = 0
        self.total_steps = 100

    def supports_checkpointing(self) -> bool:
        return True

    async def save_state(self) -> dict:
        return {"current_step": self.current_step, "total_steps": self.total_steps}

    async def load_state(self, state: dict) -> None:
        self.current_step = state.get("current_step", 0)
        self.total_steps = state.get("total_steps", 100)

    async def run(self, payload: dict, resume_state: dict | None = None) -> dict:
        self.total_steps = payload.get("total_steps", 100)
        step_duration = payload.get("step_duration", 0.5)
        fail_at_step = payload.get("fail_at_step", None)

        start_step = 1
        if resume_state:
            await self.load_state(resume_state)
            start_step = self.current_step + 1
            logger.info(f"Resuming from checkpoint at step {self.current_step}")

        logger.info(f"Long-running job: steps {start_step}-{self.total_steps}")

        for step in range(start_step, self.total_steps + 1):
            if fail_at_step and step == fail_at_step:
                raise RuntimeError(f"Simulated failure at step {step}")

            await asyncio.sleep(step_duration)
            self.current_step = step

            if step % 10 == 0:
                logger.info(f"Step {step}/{self.total_steps} complete")

        return {"steps_completed": self.total_steps, "resumed_from": start_step - 1}
