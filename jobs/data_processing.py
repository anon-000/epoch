"""
Sample job: simulates a data processing task.
Processes N items from the payload, sleeping briefly to simulate work.
"""

import asyncio
import logging

from jobs.base import BaseJob

logger = logging.getLogger("epoch.jobs.data_processing")


class DataProcessingJob(BaseJob):
    async def run(self, payload: dict, resume_state: dict | None = None) -> dict:
        items = payload.get("items", [])
        batch_size = payload.get("batch_size", 10)
        sleep_per_batch = payload.get("sleep_per_batch", 0.1)

        logger.info(f"Processing {len(items)} items in batches of {batch_size}")
        processed = 0

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            # Simulate processing
            await asyncio.sleep(sleep_per_batch)
            processed += len(batch)
            logger.info(f"Processed {processed}/{len(items)} items")

        return {"processed": processed, "total": len(items)}
