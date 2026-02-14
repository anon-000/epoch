Distributed Job Scheduler — System Design & Planning
Let me break this down properly. This is a meaty distributed systems project, so let's get the architecture right before writing a single line of code.

Core Components

1. API Server (FastAPI)
   The entry point. Clients submit jobs, query status, cancel jobs through REST endpoints. Stateless — can run multiple instances behind a load balancer.
2. Scheduler (Leader-elected)
   The brain. Picks jobs from the queue, assigns them to workers based on priority, fairness, and tenant quotas. Only ONE active scheduler at a time (leader election via PostgreSQL advisory locks — no need for etcd/ZooKeeper, keeps the stack simple but still production-grade).
3. Worker Pool
   Actual execution engines. Each worker pulls assigned jobs, executes them, reports progress/checkpoints back. Workers are tenant-isolated — a misbehaving tenant's job can't starve others.
4. PostgreSQL (State Store)
   Single source of truth for everything: job definitions, state machines, checkpoints, worker heartbeats, leader election locks. Jobs survive crashes because state is always persisted before acknowledgment.
5. Redis (Coordination Layer)
   Priority queues for job scheduling, pub/sub for real-time worker notifications, distributed locking for job-level mutual exclusion. Redis is volatile here — if it dies, PostgreSQL is the recovery source.
6. Checkpoint Store (S3-compatible / Local filesystem)
   Large checkpoint blobs for long-running jobs. Workers periodically dump their progress here. On crash recovery, jobs resume from last checkpoint, not from scratch.

Component Communication Flow
┌─────────────┐
│ Client │
└──────┬──────┘
│ REST API
▼
┌─────────────┐
│ API Server │ (stateless, multiple instances)
└──────┬──────┘
│ writes job to DB + pushes to Redis queue
▼
┌────────────────────────┐
│ PostgreSQL │
│ - Job state machine │
│ - Worker registry │
│ - Leader election lock │
│ - Checkpoint metadata │
└────────────┬───────────┘
│
┌──────────────────┼──────────────────┐
│ │ │
▼ ▼ ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ Scheduler │ │ Redis │ │ Checkpoint │
│ (Leader) │◄─►│ - Priority │ │ Store (S3) │
│ │ │ Queues │ │ │
└──────┬───────┘ │ - Pub/Sub │ └───────▲───────┘
│ │ - Locks │ │
│ └──────┬──────┘ │
│ assigns jobs │ notifications │ checkpoint blobs
▼ ▼ │
┌─────────────────────────────────────────────┤
│ Worker Pool │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │ Worker 1 │ │ Worker 2 │ │ Worker 3 │────┘
│ │(tenant-A)│ │(tenant-B)│ │(tenant-A)│
│ └──────────┘ └──────────┘ └──────────┘
└─────────────────────────────────────────────┘

Job State Machine
This is critical — every job transition is persisted to DB before any action is taken.
SUBMITTED ──► QUEUED ──► SCHEDULED ──► RUNNING ──► COMPLETED
│ │ │
│ │ ├──► CHECKPOINTED ──► RUNNING (resume)
│ │ │
│ ▼ ├──► FAILED ──► QUEUED (retry w/ backoff)
│ PREEMPTED │
│ │ └──► TIMED_OUT ──► QUEUED (retry)
│ ▼
│ QUEUED (re-queued with same priority)
│
└──► CANCELLED

Key Design Decisions
Leader Election — PostgreSQL Advisory Locks
Why not ZooKeeper/etcd? Because we already have PostgreSQL. Advisory locks are lightweight, and a heartbeat-based renewal (every 5s, 15s TTL) gives us leader failover in under 15 seconds. The standby scheduler keeps trying to acquire the lock. When the leader dies, the standby grabs it and rebuilds its in-memory state from the DB. No job progress is lost because it's all in PostgreSQL + checkpoint store.
Priority Queue — Multi-level with Aging
Three priority tiers: CRITICAL, HIGH, NORMAL. But to prevent starvation, NORMAL jobs age — their effective priority increases over time. This is a classic scheduling fairness technique (think MLFQ from OS design). Implemented in Redis sorted sets with a composite score: (priority_weight _ 1000) - (time_in_queue_seconds).
Retry & Backoff
Exponential backoff with jitter: min(base _ 2^attempt + random_jitter, max_delay). Max retries configurable per job. Each retry is a fresh state transition: FAILED → QUEUED with incremented attempt counter. After max retries → DEAD_LETTER state for manual inspection.
Checkpointing for Long-Running Jobs
Jobs implement a checkpoint interface. Every N seconds (configurable), the worker serializes job progress and writes it to the checkpoint store. Checkpoint metadata (location, timestamp, sequence number) goes to PostgreSQL. On recovery: scheduler sees a RUNNING job with no live worker → re-queues it → new worker picks it up → loads last checkpoint → resumes.
Tenant Isolation
Each tenant gets a configurable worker quota (e.g., tenant-A can use max 5 workers). The scheduler enforces this during assignment. Workers run jobs in isolated processes (subprocess with resource limits — CPU, memory, timeout). One tenant's runaway job can't kill another tenant's work.
Exactly-once vs At-least-once
We go with at-least-once with idempotency. Jobs must be designed to be idempotent (or use checkpoint sequence numbers to skip already-completed work). The scheduler guarantees a job will be executed to completion, possibly more than once if a worker crashes mid-execution before checkpointing.

Data Models (Core Tables)
jobs:
id (UUID, PK)
tenant_id (FK)
name, payload (JSONB)
priority (CRITICAL/HIGH/NORMAL)
state (enum — the state machine above)
attempt (int, current retry count)
max_retries (int)
timeout_seconds (int)
created_at, updated_at, scheduled_at, started_at, completed_at
assigned_worker_id (FK, nullable)
checkpoint_id (FK, nullable — latest checkpoint)

workers:
id (UUID, PK)
hostname, pid
tenant_slots (JSONB — {tenant_id: current_count})
max_slots (int)
state (ONLINE/DRAINING/OFFLINE)
last_heartbeat (timestamp)

checkpoints:
id (UUID, PK)
job_id (FK)
sequence_number (int)
storage_path (text — S3/local path)
size_bytes (bigint)
created_at

scheduler_leader:
id (singleton row)
holder_id (text — scheduler instance ID)
acquired_at (timestamp)
renewed_at (timestamp)

dead_letter_jobs:
id (UUID, PK)
job_id (FK)
final_error (text)
total_attempts (int)
moved_at (timestamp)

Tech Stack
Component Technology
= = = = = = = = = = = = = = = = = = >
API Server : FastAPI + uvicorn
Database : PostgreSQL 15+ (with advisory locks)
Coordination : Redis 7+ (sorted sets, pub/sub)
ORM : SQLAlchemy 2.0 (async)
Migrations : Alembic
Checkpoint Storage : Local filesystem (S3 interface later) if possible use minio
Process Isolation : Python subprocess + resource limits
Serialization : JSON (jobs), pickle/msgpack (checkpoints)
Testing : pytest + testcontainers (real PG + Redis)

Project Structure
distributed-scheduler/
├── src/
│ ├── api/ # FastAPI routes
│ │ ├── routes/
│ │ │ ├── jobs.py
│ │ │ ├── workers.py
│ │ │ └── admin.py
│ │ └── server.py
│ ├── scheduler/ # Core scheduling logic
│ │ ├── leader.py # Leader election
│ │ ├── scheduler.py # Main scheduling loop
│ │ ├── priority_queue.py # Multi-level priority queue
│ │ └── preemption.py # Preemption logic
│ ├── worker/ # Worker pool
│ │ ├── worker.py # Worker main loop
│ │ ├── executor.py # Job execution + isolation
│ │ └── heartbeat.py # Heartbeat sender
│ ├── checkpoint/ # Checkpoint management
│ │ ├── manager.py
│ │ └── store.py # Storage backend abstraction
│ ├── models/ # SQLAlchemy models
│ │ ├── job.py
│ │ ├── worker.py
│ │ └── checkpoint.py
│ ├── db/ # Database setup
│ │ ├── session.py
│ │ └── migrations/
│ ├── queue/ # Redis queue operations
│ │ └── redis_queue.py
│ ├── config.py
│ └── constants.py
├── jobs/ # Sample job implementations
│ ├── base.py # Base job interface (with checkpoint hooks)
│ ├── data_processing.py
│ └── long_running.py
├── tests/
├── docker-compose.yml # PG + Redis + API + Scheduler + Workers
├── Dockerfile
└── requirements.txt

Build Order (Phases)
Phase 1 — Foundation: DB models, migrations, basic API (submit/query jobs), simple FIFO scheduler (no priority yet), single worker that executes jobs. Get end-to-end working first.
Phase 2 — Priority & Fairness: Multi-level priority queue in Redis, aging mechanism, preemption logic. This is where the scheduling algorithms shine.
Phase 3 — Fault Tolerance: Leader election, worker heartbeats, dead worker detection, job re-queuing on failure, retry with exponential backoff, dead letter queue.
Phase 4 — Checkpointing: Checkpoint interface for jobs, periodic checkpoint writes, crash recovery from last checkpoint, checkpoint garbage collection.
Phase 5 — Tenant Isolation: Tenant-aware scheduling, per-tenant quotas, process-level resource isolation, fair share scheduling across tenants.
Phase 6 — Observability & Polish: Metrics (job latency, queue depth, worker utilization), health endpoints, Docker Compose for full stack, sample jobs that demonstrate all features.
