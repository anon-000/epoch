"""
Multi-level priority queue with aging.

Score formula for Redis sorted set (ZPOPMIN takes lowest score first):
    score = -(priority_weight * 1000) + enqueue_timestamp

This means:
- CRITICAL (weight=3): score ≈ -3000 + timestamp → always dequeued first
- HIGH (weight=2):     score ≈ -2000 + timestamp → dequeued before NORMAL
- NORMAL (weight=1):   score ≈ -1000 + timestamp → dequeued last

Within the same priority tier, earlier jobs (lower timestamp) get lower scores → FIFO.

Aging: NORMAL jobs that have been in the queue longer have smaller timestamps,
so their scores naturally decrease relative to newer NORMAL jobs. For explicit
aging across tiers, we periodically recalculate scores (Phase 2 enhancement).
"""

import time

from src.constants import PRIORITY_WEIGHTS, JobPriority


def compute_priority_score(priority: JobPriority, enqueue_time: float | None = None) -> float:
    """
    Compute the sorted set score for a job.

    Lower score = dequeued first (ZPOPMIN).
    """
    if enqueue_time is None:
        enqueue_time = time.time()

    weight = PRIORITY_WEIGHTS[priority]
    # Negative weight term ensures higher priority always wins.
    # Timestamp ensures FIFO within same tier.
    return -(weight * 1000) + enqueue_time


def compute_aged_score(priority: JobPriority, enqueue_time: float, now: float | None = None) -> float:
    """
    Recompute score with aging applied.

    Aging: for every `aging_interval` seconds in the queue, NORMAL jobs
    get a bonus that effectively promotes them toward HIGH priority.
    This prevents starvation of low-priority jobs.

    Aging rate: +0.1 priority weight per 60 seconds in queue.
    A NORMAL job (weight=1) after 600s becomes effectively weight=2 (HIGH).
    """
    if now is None:
        now = time.time()

    weight = PRIORITY_WEIGHTS[priority]
    time_in_queue = now - enqueue_time
    aging_bonus = (time_in_queue / 60.0) * 0.1  # +0.1 weight per minute

    # Cap aging: NORMAL can age up to CRITICAL level but not beyond
    max_weight = PRIORITY_WEIGHTS[JobPriority.CRITICAL]
    effective_weight = min(weight + aging_bonus, max_weight)

    return -(effective_weight * 1000) + enqueue_time
