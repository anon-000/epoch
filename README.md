<p align="center">
  <img src="assets/epoch-title.svg" alt="Epoch" width="370" />
</p>

<p align="center">
  <strong>A production-grade distributed job scheduler built from scratch.</strong><br/>
  Priority queues · Leader election · Fault tolerance · Tenant isolation · Real-time dashboard
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis-7+-DC382D?logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white" />
</p>

<p align="center">
  <a href="#-quickstart">Quickstart</a> ·
  <a href="#-architecture">Architecture</a> ·
  <a href="#-how-it-works">How It Works</a> ·
  <a href="#-fault-tolerance">Fault Tolerance</a> ·
  <a href="#-walkthroughs">Walkthroughs</a>
</p>

---

## What is Epoch?

Epoch is a **distributed job scheduling system** that handles job submission, prioritized scheduling, execution across a pool of workers, automatic retries with exponential backoff, checkpointing for long-running jobs, tenant-aware fair-share scheduling, and leader-elected fault tolerance — all built from the ground up with no external orchestration frameworks.

It's designed to answer the question: _"What does it actually take to build a reliable job scheduler that handles failures gracefully?"_

### Key Features

| Feature                           | Description                                                                                     |
| --------------------------------- | ----------------------------------------------------------------------------------------------- |
| 🎯 **Multi-Level Priority Queue** | CRITICAL > HIGH > NORMAL with automatic priority aging to prevent starvation                    |
| 👑 **Leader-Elected Scheduler**   | PostgreSQL advisory lock-based leader election with automatic failover                          |
| 🔄 **Automatic Retries**          | Exponential backoff with jitter, configurable per job, dead letter queue for permanent failures |
| ⚡ **Job Preemption**             | Higher-priority jobs can preempt lower-priority running jobs                                    |
| 💾 **Checkpointing**              | Long-running jobs save progress periodically — crash recovery resumes from last checkpoint      |
| 🏢 **Tenant Isolation**           | Per-tenant worker quotas and fair-share scheduling prevent noisy neighbors                      |
| 📊 **Real-Time Dashboard**        | Live monitoring with job states, worker utilization, tenant activity, and full event history    |
| 🔍 **Immutable Audit Log**        | Every state transition is recorded — full lifecycle traceability for any job                    |

---

## 📸 Walkthroughs

### 🖥️ Dashboard Overview

Real-time metrics, job distribution charts, worker utilization, and recent activity feed.

[https://raw.githubusercontent.com/anon-000/epoch/main/walkthroughs/dashboard_walkthrough.mov
](https://github.com/user-attachments/assets/8a534ec5-80e3-4e6f-9aab-cba97237fede)

### 📋 Jobs Lifecycle

Submitting jobs, watching state transitions, retries, failures, dead letter flow, and the full event timeline.

https://github.com/user-attachments/assets/00a87619-30f1-4c93-a8f4-1f02cf4ea1e2

### 👷 Workers

Worker pool management, heartbeats, slot utilization, and drain mode.

https://github.com/user-attachments/assets/03dc02a9-5ae6-4f45-aa03-825940dd2217

### 🏢 Tenant Management

Multi-tenant configuration, per-tenant quotas, and priority boost.

https://github.com/user-attachments/assets/eb8378c9-4952-444d-ab93-80aaf3e00551

---

## 🚀 Quickstart

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) v2+

### One-Command Setup

```bash
git clone https://github.com/your-username/epoch.git
cd epoch
docker compose up --build
```

That's it. This spins up the entire stack:

| Service               | Port                                    | Description                             |
| --------------------- | --------------------------------------- | --------------------------------------- |
| **Frontend**          | [localhost:3000](http://localhost:3000) | Next.js dashboard                       |
| **API**               | [localhost:8000](http://localhost:8000) | FastAPI REST API                        |
| **Scheduler**         | —                                       | Leader-elected scheduler                |
| **Scheduler Standby** | —                                       | Hot standby (takes over if leader dies) |
| **Worker 1**          | —                                       | 4 execution slots                       |
| **Worker 2**          | —                                       | 4 execution slots                       |
| **PostgreSQL**        | 5432                                    | Source of truth                         |
| **Redis**             | 6379                                    | Priority queues & pub/sub               |

### Submit Your First Job

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-job",
    "tenant_id": "default",
    "job_type": "jobs.data_processing:DataProcessingJob",
    "payload": {"input_size": 5},
    "priority": "NORMAL",
    "max_retries": 3,
    "timeout_seconds": 60
  }'
```

Then open [localhost:3000](http://localhost:3000) to watch it flow through the system.

### API Quick Reference

| Method | Endpoint                           | Description                                 |
| ------ | ---------------------------------- | ------------------------------------------- |
| `POST` | `/api/v1/jobs`                     | Submit a new job                            |
| `GET`  | `/api/v1/jobs`                     | List all jobs (filterable by state, tenant) |
| `GET`  | `/api/v1/jobs/{id}`                | Get job details                             |
| `GET`  | `/api/v1/jobs/{id}/events`         | Full event audit log                        |
| `POST` | `/api/v1/jobs/{id}/retry`          | Manually retry a failed/dead-lettered job   |
| `POST` | `/api/v1/jobs/{id}/cancel`         | Cancel a job                                |
| `GET`  | `/api/v1/workers`                  | List all workers and their status           |
| `POST` | `/api/v1/admin/workers/{id}/drain` | Drain a worker (stop accepting new jobs)    |
| `GET`  | `/api/v1/admin/scheduler/leader`   | Current scheduler leader info               |
| `GET`  | `/api/v1/dashboard/stats`          | Dashboard metrics                           |

---

## 🏗 Architecture

### System Overview

```
┌─────────────────┐
│     Client      │
│  (Dashboard /   │
│   REST API)     │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   API Server    │  ← Stateless, horizontally scalable
│   (FastAPI)     │
└────────┬────────┘
         │ Writes job to DB + pushes to Redis queue
         ▼
┌───────────────────────────────────────────────────────────┐
│                                                           │
│   ┌──────────────┐         ┌──────────────┐               │
│   │  PostgreSQL  │◄───────►│    Redis     │               │
│   │              │         │              │               │
│   │ • Job state  │         │ • Priority   │               │
│   │ • Workers    │         │   queue      │               │
│   │ • Leader     │         │ • Pub/Sub    │               │
│   │   election   │         │ • Job locks  │               │
│   │ • Checkpoints│         │              │               │
│   │ • Audit log  │         │              │               │
│   └──────────────┘         └──────┬───────┘               │
│                                   │                       │
│   ┌───────────────────────────────┼────────────────────┐  │
│   │         Scheduler (Leader-Elected)                 │  │
│   │                               │                    │  │
│   │  ┌─────────────┐    ┌────────┴──────┐              │  │
│   │  │  Scheduler  │    │  Scheduler    │              │  │
│   │  │  (Active) 👑│    │  (Standby) ⏳ │               │  │
│   │  └──────┬──────┘    └──────────────┘               │  │
│   │         │ Assigns jobs to workers                  │  │
│   └─────────┼──────────────────────────────────────────┘  │
│             ▼                                             │
│   ┌────────────────────────────────────────────────────┐  │
│   │              Worker Pool                           │  │
│   │                                                    │  │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│   │  │ Worker 1 │  │ Worker 2 │  │ Worker N │          │  │
│   │  │ (4 slots)│  │ (4 slots)│  │ (4 slots)│          │  │
│   │  └──────────┘  └──────────┘  └──────────┘          │  │
│   └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer                    | Technology                                      |
| ------------------------ | ----------------------------------------------- |
| **API**                  | FastAPI + Uvicorn                               |
| **Database**             | PostgreSQL 15 (advisory locks, JSONB)           |
| **Queue & Coordination** | Redis 7 (sorted sets, pub/sub)                  |
| **ORM**                  | SQLAlchemy 2.0 (fully async)                    |
| **Migrations**           | Alembic                                         |
| **Frontend**             | Next.js 16 + React 19 + Recharts + Tailwind CSS |
| **Containerization**     | Docker + Docker Compose                         |
| **Checkpoints**          | Local filesystem (S3-compatible interface)      |

---

## ⚙ How It Works

### The Job State Machine

Every job follows a deterministic state machine. **Every transition is persisted to PostgreSQL before any action is taken** — this is the cornerstone of crash safety.

```
SUBMITTED ──► QUEUED ──► SCHEDULED ──► RUNNING ──► COMPLETED ✅
                │              │           │
                │              │           ├──► CHECKPOINTED ──► RUNNING (resume)
                │              │           │
                │              │           ├──► FAILED ──► QUEUED (retry with backoff)
                │              │           │         └──► DEAD_LETTER 💀 (max retries exhausted)
                │              │           │
                │              │           └──► TIMED_OUT ──► QUEUED (retry)
                │              │                     └──► DEAD_LETTER 💀
                │              │
                │              └──► PREEMPTED ──► QUEUED (re-queued, same priority)
                │
                └──► CANCELLED 🚫
```

**State definitions:**

| State          | What it means                                          |
| -------------- | ------------------------------------------------------ |
| `SUBMITTED`    | Job received by the API                                |
| `QUEUED`       | Sitting in the priority queue, waiting to be scheduled |
| `SCHEDULED`    | Assigned to a specific worker, about to execute        |
| `RUNNING`      | Currently executing on a worker                        |
| `COMPLETED`    | Finished successfully                                  |
| `FAILED`       | Execution failed (will be retried or dead-lettered)    |
| `TIMED_OUT`    | Exceeded its timeout — treated like a failure          |
| `CHECKPOINTED` | Progress saved mid-execution (long-running jobs)       |
| `PREEMPTED`    | Interrupted by a higher-priority job                   |
| `CANCELLED`    | Manually cancelled by the user                         |
| `DEAD_LETTER`  | Exhausted all retries — parked for manual inspection   |

### The Scheduling Loop

The scheduler runs a continuous loop (every ~1 second):

```
┌──────────────────────────────────────────────────────────────┐
│                     SCHEDULER LOOP                           │
│                                                              │
│  1. Am I the leader? (check advisory lock)                   │
│     └─ No → sleep, try again                                 │
│     └─ Yes ↓                                                 │
│                                                              │
│  2. Dequeue highest-priority job from Redis sorted set       │
│                                                              │
│  3. Check tenant quota:                                      │
│     └─ Tenant at max concurrent jobs? → defer, try next job  │
│                                                              │
│  4. Find an available worker:                                │
│     └─ Worker with free slots? → assign job                  │
│     └─ No free workers? → try preemption (if CRITICAL)       │
│     └─ Still no slot? → put job back in queue                │
│                                                              │
│  5. Assign: Job → SCHEDULED, notify worker via pub/sub       │
│                                                              │
│  6. Repeat                                                   │
└──────────────────────────────────────────────────────────────┘
```

### Priority Queue with Aging

Jobs are stored in a **Redis sorted set** (ZPOPMIN — lowest score dequeued first). The score formula:

```
score = -(priority_weight × 1000) + enqueue_timestamp
```

| Priority | Weight | Effective Score Range              |
| -------- | ------ | ---------------------------------- |
| CRITICAL | 3      | ≈ -3000 + timestamp (always first) |
| HIGH     | 2      | ≈ -2000 + timestamp                |
| NORMAL   | 1      | ≈ -1000 + timestamp                |

**Anti-starvation aging**: NORMAL jobs gain +0.1 effective weight per minute in the queue. After ~10 minutes, a NORMAL job's effective priority equals HIGH. After ~20 minutes, it matches CRITICAL. This prevents low-priority jobs from waiting forever — a classic technique borrowed from [Multi-Level Feedback Queue](https://en.wikipedia.org/wiki/Multilevel_feedback_queue) scheduling in operating systems.

### Job Preemption

When a CRITICAL job arrives and all workers are full:

```
1. Find the lowest-priority RUNNING job
2. CRITICAL can preempt HIGH or NORMAL
3. HIGH can preempt NORMAL
4. Preempted job → PREEMPTED → re-queued with same priority
5. CRITICAL job gets the freed worker slot
```

The preempted job doesn't lose its work — if it supports checkpointing, it resumes from the last checkpoint when rescheduled.

---

## 🛡 Fault Tolerance

This is where things get interesting. Distributed systems fail in creative ways. Here's how Epoch handles each failure mode:

### 1. Worker Crashes

**Problem**: A worker dies mid-execution. The job is stuck in `RUNNING` with no one executing it.

**Detection**: Workers send heartbeats every 5 seconds. The scheduler monitors these. If a worker misses heartbeats for 30 seconds, it's declared dead.

**Recovery**:

```
1. Scheduler detects stale heartbeat (> 30s old)
2. Worker marked as OFFLINE
3. All jobs assigned to that worker are re-examined
4. RUNNING jobs → TIMED_OUT → queued for retry (with backoff)
5. If the job has a checkpoint, the retry resumes from there
```

**No job is lost.** PostgreSQL is the source of truth — a job in `RUNNING` state with no live worker will always be detected and recovered.

### 2. Scheduler Crashes

**Problem**: The scheduler (the brain of the system) dies.

**Detection**: PostgreSQL advisory locks. The leader holds a session-level advisory lock. If its connection drops (process crash, network partition), PostgreSQL **automatically releases the lock**.

**Recovery**:

```
1. Standby scheduler continuously tries pg_try_advisory_lock()
2. Leader dies → lock released → standby acquires it
3. New leader reads all state from PostgreSQL
4. Rebuilds in-memory queues from DB (QUEUED jobs → Redis)
5. Resumes scheduling — no jobs lost, failover < 15 seconds
```

This is why we use PostgreSQL advisory locks instead of ZooKeeper or etcd — one fewer infrastructure dependency, and it's equally reliable for single-region deployments.

### 3. Job Execution Failures

**Problem**: A job throws an exception during execution.

**Handling**: Exponential backoff with jitter.

```
delay = min(base_delay × 2^attempt + random_jitter, max_delay)

Example with base_delay=5s, max_delay=300s:
  Attempt 1: ~5s   wait
  Attempt 2: ~10s  wait
  Attempt 3: ~20s  wait
  Attempt 4: ~40s  wait
  ...
  Attempt N: max 300s wait
```

After `max_retries` (configurable per job, default: 3), the job moves to **Dead Letter Queue** — a holding area for permanently failed jobs that can be inspected and manually retried.

### 4. Timeout Detection

**Problem**: A job hangs — doesn't fail, doesn't complete, just sits there.

**Detection**: The scheduler checks for jobs in `RUNNING` state that have exceeded their `timeout_seconds`.

**Recovery**: Same as failure — `TIMED_OUT` → retry with backoff → dead letter after max retries.

### 5. Redis Crashes

**Problem**: Redis (the coordination layer) goes down.

**Impact**: The priority queue and pub/sub notifications are unavailable. Jobs can't be enqueued or dequeued.

**Recovery**: Redis is **volatile** — it's a performance optimization, not the source of truth. When Redis recovers:

```
1. Scheduler detects Redis reconnection
2. Rebuilds the priority queue from PostgreSQL
3. All QUEUED jobs in DB → re-pushed to Redis sorted set
4. Scheduling resumes normally
```

No data is lost because PostgreSQL always has the canonical state.

---

## 🔁 Retry System Deep Dive

### The Retry Flow

```
Job executes → FAILS
     │
     ▼
attempt < max_retries?
     │
     ├── YES → compute backoff delay
     │          → Job state: FAILED → QUEUED
     │          → Re-enqueue in Redis with delay
     │          → Will be rescheduled after delay
     │
     └── NO  → Job state: DEAD_LETTER 💀
              → Moved to dead_letter_jobs table
              → Error details preserved
              → Available for manual retry via API or dashboard
```

### Backoff Formula

```python
delay = min(base_delay × 2^attempt + random.uniform(0, base_delay), max_delay)
```

The jitter prevents the **thundering herd problem** — if 100 jobs fail at the same time, they don't all retry at exactly the same moment.

### Dead Letter Queue

Jobs that exhaust all retries are moved to the dead letter queue with:

- The final error message
- Total number of attempts
- Full event history (every state transition)

From the dashboard or API, you can:

- **Inspect** the failure reason
- **Manually retry** — resets the attempt counter and re-queues the job

---

## 💾 Checkpointing

For long-running jobs (hours, days), losing all progress on a crash is unacceptable.

### How It Works

```
Job starts → executes work → periodically saves checkpoint
     │
     │   Every N seconds (configurable, default: 30s):
     │   ┌──────────────────────────────────────┐
     │   │ 1. Job serializes its current state  │
     │   │ 2. Blob written to checkpoint store  │
     │   │ 3. Metadata saved to PostgreSQL      │
     │   │    (path, sequence #, timestamp)     │
     │   └──────────────────────────────────────┘
     │
     ▼
Worker crashes!
     │
     ▼
Scheduler detects dead worker → re-queues the job
     │
     ▼
New worker picks up the job:
  1. Loads latest checkpoint from store
  2. Deserializes saved state
  3. Resumes execution from where it left off
```

Jobs implement the `BaseJob` interface which provides `save_checkpoint()` and `load_checkpoint()` hooks:

```python
class MyLongRunningJob(BaseJob):
    async def execute(self, job_id, payload, checkpoint_data=None):
        start = 0
        if checkpoint_data:
            start = checkpoint_data["progress"]  # Resume from checkpoint

        for i in range(start, 1000):
            # Do work...
            if i % 100 == 0:
                await self.save_checkpoint(job_id, {"progress": i})

        return {"success": True, "result": "done"}
```

---

## 🏢 Tenant Isolation

Epoch is designed for **multi-tenant environments** where different teams or customers share the same scheduler infrastructure.

### Fair-Share Scheduling

Each tenant has configurable limits:

```json
{
  "tenant_id": "team-ml",
  "max_concurrent_jobs": 5,
  "max_workers": 3,
  "priority_boost": 0
}
```

The scheduler enforces these during assignment:

```
1. Dequeue next job from priority queue
2. Check: "Is tenant X at their max_concurrent_jobs limit?"
   └─ Yes → skip this job, try the next one
   └─ No  → proceed to assign
3. This ensures no single tenant can monopolize all workers
```

### Why This Matters

Without tenant isolation, a single tenant submitting 10,000 jobs would starve everyone else. Epoch's fair-share model ensures:

- Each tenant gets their fair share of resources
- One tenant's failures don't cascade to others
- Priority boost lets you give premium tenants an edge

---

## 👑 Leader Election

Only **one scheduler** should be assigning jobs at any time. Multiple schedulers assigning the same job would cause duplicate execution.

### How It Works

```
                  ┌─────────────────────────────────┐
                  │       PostgreSQL                │
                  │                                 │
                  │   Advisory Lock #123456789      │
                  │   ┌───────────────────────┐     │
                  │   │   Held by: Scheduler A│     │
                  │   │   Since: 2 minutes ago│     │
                  │   └───────────────────────┘     │
                  │                                 │
                  └─────────────┬───────────────────┘
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
              ▼                 ▼                  ▼
     ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐
     │ Scheduler A │  │ Scheduler B  │  │  Scheduler C    │
     │  (Leader) 👑│  │ (Standby) ⏳ │  │  (Standby) ⏳    │
     │             │  │              │  │                 │
     │ Acquired ✅ │  │ Try → fail   │  │  Try → fail     │
     │ Scheduling  │  │ Try → fail   │  │  Try → fail     │
     │             │  │ Try → fail   │  │  Try → fail     │
     └─────────────┘  └──────────────┘  └─────────────────┘
```

1. `pg_try_advisory_lock(123456789)` — non-blocking lock attempt
2. One scheduler wins → becomes leader, writes to `scheduler_leader` table
3. Others fail → keep retrying every loop iteration
4. Leader renews heartbeat every 5 seconds
5. If leader dies → PostgreSQL releases the lock → standby takes over

**No split-brain is possible** — PostgreSQL guarantees at most one holder of an advisory lock at any time.

---

## 📊 Event Audit Log

Every state transition for every job is recorded in an immutable `job_events` table:

```
Job: data-pipeline-42

CREATED         | Job submitted: data-pipeline-42
QUEUED          | Enqueued for scheduling
SCHEDULED       | Assigned to worker abc123 (host-1)
RUNNING         | Execution started (attempt 1/3)
FAILED          | TimeoutError: connection to database timed out
RETRIED         | Auto-retry: re-queued (attempt 1/3)
SCHEDULED       | Assigned to worker def456 (host-2)
RUNNING         | Execution started (attempt 2/3)
COMPLETED       | Job completed successfully
```

Each event captures:

- **Timestamp** (microsecond precision)
- **Event type** (CREATED, QUEUED, SCHEDULED, RUNNING, FAILED, RETRIED, DEAD_LETTER, etc.)
- **Attempt number**
- **Worker ID** (which worker executed it)
- **Detail text** (error messages, assignment info)

This gives you complete **lifecycle traceability** — you can reconstruct exactly what happened to any job.

---

## 📁 Project Structure

```
epoch/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── server.py           #   App factory, middleware, lifespan
│   │   ├── routes/
│   │   │   ├── jobs.py         #   Job CRUD + event history endpoint
│   │   │   ├── workers.py      #   Worker listing
│   │   │   ├── admin.py        #   Admin ops (drain, leader info, tenants)
│   │   │   └── dashboard.py    #   Dashboard stats aggregation
│   │   └── schemas.py          #   Pydantic request/response models
│   │
│   ├── scheduler/              # Core scheduling engine
│   │   ├── scheduler.py        #   Main loop: dequeue → assign → commit
│   │   ├── leader.py           #   PostgreSQL advisory lock leader election
│   │   ├── priority_queue.py   #   Score computation + aging formula
│   │   └── preemption.py       #   Find preemptable jobs + preempt logic
│   │
│   ├── worker/                 # Job execution
│   │   ├── worker.py           #   Worker lifecycle, pub/sub listener
│   │   ├── executor.py         #   Subprocess isolation, timeout enforcement
│   │   └── heartbeat.py        #   Periodic heartbeat sender
│   │
│   ├── checkpoint/             # Checkpoint management
│   │   ├── manager.py          #   Save/load/cleanup checkpoints
│   │   └── store.py            #   Storage backend (local FS, S3-ready)
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── job.py              #   Job + DeadLetterJob models
│   │   ├── job_event.py        #   Immutable audit log model
│   │   ├── worker.py           #   Worker model
│   │   ├── checkpoint.py       #   Checkpoint metadata model
│   │   ├── scheduler.py        #   Scheduler leader model
│   │   └── tenant.py           #   Tenant config model
│   │
│   ├── services/
│   │   └── event_logger.py     #   record_event() helper for audit log
│   │
│   ├── queue/
│   │   └── redis_queue.py      #   Redis sorted set + pub/sub operations
│   │
│   ├── db/
│   │   └── session.py          #   Async session factory + init
│   │
│   ├── config.py               #   Pydantic settings (env-driven)
│   └── constants.py            #   State enums, transitions, Redis keys
│
├── jobs/                       # Sample job implementations
│   ├── base.py                 #   BaseJob interface (checkpoint hooks)
│   ├── data_processing.py      #   Simple data processing job
│   └── long_running.py         #   Long-running job with checkpointing
│
├── frontend/                   # Next.js 16 dashboard
│   └── src/
│       ├── app/                #   Pages (dashboard, jobs, workers, tenants)
│       ├── components/         #   React components
│       └── lib/                #   API client, types, constants
│
├── walkthroughs/               # Demo videos
│   ├── dashboard_walkthrough.mov
│   ├── jobs_walkthrough.mov
│   ├── workers.mov
│   └── tenants_demo.mov
│
├── docker-compose.yml          # Full stack: PG + Redis + API + Scheduler(×2) + Worker(×2) + Frontend
├── Dockerfile                  # Python 3.12 multi-service image
├── requirements.txt            # Python dependencies
└── Plan.md                     # Original system design document
```

---

## ⚙️ Configuration

All configuration is via environment variables with the `EPOCH_` prefix:

| Variable                          | Default                                                 | Description                        |
| --------------------------------- | ------------------------------------------------------- | ---------------------------------- |
| `EPOCH_DATABASE_URL`              | `postgresql+asyncpg://epoch:epoch@localhost:5432/epoch` | PostgreSQL connection (async)      |
| `EPOCH_REDIS_URL`                 | `redis://localhost:6379/0`                              | Redis connection                   |
| `EPOCH_SCHEDULER_LOOP_INTERVAL`   | `1.0`                                                   | Scheduler cycle interval (seconds) |
| `EPOCH_LEADER_HEARTBEAT_INTERVAL` | `5.0`                                                   | Leader heartbeat interval          |
| `EPOCH_LEADER_LOCK_TTL`           | `15.0`                                                  | Leader lock timeout                |
| `EPOCH_WORKER_MAX_SLOTS`          | `4`                                                     | Max concurrent jobs per worker     |
| `EPOCH_WORKER_HEARTBEAT_INTERVAL` | `5.0`                                                   | Worker heartbeat interval          |
| `EPOCH_WORKER_HEARTBEAT_TIMEOUT`  | `30.0`                                                  | Declare worker dead after this     |
| `EPOCH_DEFAULT_MAX_RETRIES`       | `3`                                                     | Default retry limit                |
| `EPOCH_RETRY_BASE_DELAY`          | `5.0`                                                   | Base retry delay (seconds)         |
| `EPOCH_RETRY_MAX_DELAY`           | `300.0`                                                 | Max retry delay (5 minutes)        |
| `EPOCH_CHECKPOINT_DIR`            | `/tmp/epoch-checkpoints`                                | Checkpoint storage directory       |
| `EPOCH_CHECKPOINT_INTERVAL`       | `30.0`                                                  | Checkpoint save interval           |

---

## 🧪 Writing Custom Jobs

Create a new job by extending `BaseJob`:

```python
# jobs/my_job.py
from jobs.base import BaseJob

class MyJob(BaseJob):
    async def execute(self, job_id, payload, checkpoint_data=None):
        # Your job logic here
        items = payload.get("items", [])

        for item in items:
            result = await process(item)

        return {"success": True, "processed": len(items)}
```

Submit it via the API:

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-custom-job",
    "tenant_id": "my-team",
    "job_type": "jobs.my_job:MyJob",
    "payload": {"items": [1, 2, 3]},
    "priority": "HIGH",
    "max_retries": 5,
    "timeout_seconds": 120
  }'
```

The `job_type` field uses Python's `module:ClassName` format — the executor dynamically imports and instantiates your job class.

---

## 🔑 Design Principles

1. **PostgreSQL is the source of truth.** Redis is a performance optimization. If Redis dies, rebuild from PG. If PG has it, it happened.

2. **State transitions are atomic.** Every state change is committed to the database before any side effect. Crash at any point → consistent recovery.

3. **At-least-once execution.** A job will be executed to completion, possibly more than once if a worker crashes. Design your jobs to be **idempotent**.

4. **No external orchestration dependencies.** No ZooKeeper, no etcd, no Kubernetes CRDs. Just PostgreSQL + Redis — tools every team already runs.

5. **Fail loudly, recover quietly.** Every failure is logged, tracked, and visible. Recovery happens automatically in the background.

---

<p align="center">
  <sub>Built with ☕ and a deep appreciation for distributed systems that don't lose your data.</sub>
</p>
