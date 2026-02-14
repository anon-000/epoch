import type { JobState, JobPriority, WorkerState } from "./types";

// Status color maps — tailwind class suffixes
export const JOB_STATE_COLORS: Record<JobState, string> = {
  SUBMITTED: "slate",
  QUEUED: "amber",
  SCHEDULED: "sky",
  RUNNING: "blue",
  COMPLETED: "emerald",
  FAILED: "red",
  TIMED_OUT: "orange",
  CANCELLED: "slate",
  CHECKPOINTED: "violet",
  PREEMPTED: "yellow",
  DEAD_LETTER: "rose",
};

export const PRIORITY_COLORS: Record<JobPriority, string> = {
  CRITICAL: "red",
  HIGH: "amber",
  NORMAL: "slate",
};

export const WORKER_STATE_COLORS: Record<WorkerState, string> = {
  ONLINE: "emerald",
  DRAINING: "amber",
  OFFLINE: "red",
};

// Chart colors (hex)
export const CHART_COLORS: Record<string, string> = {
  SUBMITTED: "#64748b",
  QUEUED: "#f59e0b",
  SCHEDULED: "#0ea5e9",
  RUNNING: "#3b82f6",
  COMPLETED: "#10b981",
  FAILED: "#ef4444",
  TIMED_OUT: "#f97316",
  CANCELLED: "#94a3b8",
  CHECKPOINTED: "#8b5cf6",
  PREEMPTED: "#eab308",
  DEAD_LETTER: "#f43f5e",
};

// Navigation
export interface NavItem {
  label: string;
  href: string;
  icon: string; // lucide icon name
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/", icon: "LayoutDashboard" },
  { label: "Jobs", href: "/jobs", icon: "Briefcase" },
  { label: "Workers", href: "/workers", icon: "Server" },
  { label: "Tenants", href: "/tenants", icon: "Users" },
  { label: "Dead Letter", href: "/dead-letter", icon: "AlertTriangle" },
  { label: "Audit Logs", href: "/audit-logs", icon: "ScrollText" },
];

// Polling
export const POLL_INTERVAL = 5000; // 5 seconds
