// Enums matching backend constants
export type JobState =
  | "SUBMITTED"
  | "QUEUED"
  | "SCHEDULED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "TIMED_OUT"
  | "CANCELLED"
  | "CHECKPOINTED"
  | "PREEMPTED"
  | "DEAD_LETTER";

export type JobPriority = "CRITICAL" | "HIGH" | "NORMAL";

export type WorkerState = "ONLINE" | "DRAINING" | "OFFLINE";

// API response types
export interface Job {
  id: string;
  name: string;
  tenant_id: string;
  job_type: string;
  payload: Record<string, unknown>;
  priority: JobPriority;
  state: JobState;
  attempt: number;
  max_retries: number;
  timeout_seconds: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  scheduled_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  assigned_worker_id: string | null;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
}

export interface Worker {
  id: string;
  hostname: string;
  pid: number;
  max_slots: number;
  current_load: number;
  state: WorkerState;
  last_heartbeat: string;
  registered_at: string;
}

export interface WorkerListResponse {
  workers: Worker[];
  total: number;
}

export interface TenantConfig {
  tenant_id: string;
  max_concurrent_jobs: number;
  max_workers: number;
  priority_boost: number;
}

export interface DeadLetterJob {
  id: string;
  job_id: string;
  final_error: string | null;
  total_attempts: number;
  moved_at: string;
}

export interface DeadLetterListResponse {
  total: number;
  items: DeadLetterJob[];
}

export interface WorkerStateMetrics {
  count: number;
  current_load: number;
  max_slots: number;
}

export interface MetricsResponse {
  timestamp: string;
  jobs: {
    total: number;
    by_state: Record<string, number>;
    avg_latency_seconds: number | null;
    avg_wait_time_seconds: number | null;
    throughput_last_hour: number;
    failure_rate: number;
  };
  queue: {
    depth: number;
  };
  workers: {
    by_state: Record<string, WorkerStateMetrics>;
    total_capacity: number;
    total_load: number;
    utilization: number;
  };
  tenants: Record<string, Record<string, number>>;
  dead_letter: {
    total: number;
  };
  checkpoints: {
    total: number;
    total_size_bytes: number;
  };
}

export interface HealthResponse {
  status: string;
}

export interface JobSubmitRequest {
  name: string;
  tenant_id: string;
  job_type: string;
  payload?: Record<string, unknown>;
  priority?: JobPriority;
  max_retries?: number;
  timeout_seconds?: number;
}

export interface TenantConfigRequest {
  tenant_id: string;
  max_concurrent_jobs?: number;
  max_workers?: number;
  priority_boost?: number;
}

export interface JobEvent {
  id: string;
  event: string;
  detail: string | null;
  attempt: number | null;
  worker_id: string | null;
  timestamp: string;
  metadata: Record<string, unknown> | null;
}
