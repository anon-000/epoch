import enum


class JobState(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    QUEUED = "QUEUED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    CHECKPOINTED = "CHECKPOINTED"
    PREEMPTED = "PREEMPTED"
    DEAD_LETTER = "DEAD_LETTER"


class JobPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"


PRIORITY_WEIGHTS = {
    JobPriority.CRITICAL: 3,
    JobPriority.HIGH: 2,
    JobPriority.NORMAL: 1,
}


class WorkerState(str, enum.Enum):
    ONLINE = "ONLINE"
    DRAINING = "DRAINING"
    OFFLINE = "OFFLINE"


# Valid state transitions
VALID_TRANSITIONS: dict[JobState, set[JobState]] = {
    JobState.SUBMITTED: {JobState.QUEUED, JobState.CANCELLED},
    JobState.QUEUED: {JobState.SCHEDULED, JobState.CANCELLED},
    JobState.SCHEDULED: {JobState.RUNNING, JobState.PREEMPTED, JobState.CANCELLED},
    JobState.RUNNING: {
        JobState.COMPLETED,
        JobState.FAILED,
        JobState.TIMED_OUT,
        JobState.CHECKPOINTED,
        JobState.CANCELLED,
    },
    JobState.CHECKPOINTED: {JobState.RUNNING},
    JobState.FAILED: {JobState.QUEUED, JobState.DEAD_LETTER},
    JobState.TIMED_OUT: {JobState.QUEUED, JobState.DEAD_LETTER},
    JobState.PREEMPTED: {JobState.QUEUED},
    JobState.COMPLETED: set(),
    JobState.CANCELLED: set(),
    JobState.DEAD_LETTER: set(),
}

# Redis keys
REDIS_JOB_QUEUE = "epoch:queue:jobs"
REDIS_WORKER_CHANNEL = "epoch:channel:workers"
REDIS_JOB_LOCK_PREFIX = "epoch:lock:job:"
