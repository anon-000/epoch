"""Entry point for a worker node."""

import asyncio
import argparse

from src.worker.worker import run_worker

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Epoch Worker")
    parser.add_argument("--slots", type=int, default=None, help="Max concurrent job slots")
    args = parser.parse_args()
    asyncio.run(run_worker(max_slots=args.slots))
