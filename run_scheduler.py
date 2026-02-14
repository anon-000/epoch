"""Entry point for the scheduler."""

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

from src.scheduler.scheduler import run_scheduler

if __name__ == "__main__":
    asyncio.run(run_scheduler())
