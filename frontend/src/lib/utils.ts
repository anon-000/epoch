import { clsx, type ClassValue } from "clsx";

/** Merge Tailwind classes with clsx */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/** Format ISO date string to locale display */
export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return "—";
  return new Date(isoString).toLocaleString();
}

/** Format relative time (e.g., "2m ago", "just now") */
export function formatRelativeTime(isoString: string | null | undefined): string {
  if (!isoString) return "—";
  const now = Date.now();
  const then = new Date(isoString).getTime();
  const diffMs = now - then;

  if (diffMs < 0) return "just now";

  const seconds = Math.floor(diffMs / 1000);
  if (seconds < 60) return `${seconds}s ago`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

/** Format bytes to human-readable (e.g., "1.2 MB") */
export function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null || bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/** Format seconds to human-readable duration (e.g., "2m 30s") */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  if (m < 60) return s > 0 ? `${m}m ${s}s` : `${m}m`;
  const h = Math.floor(m / 60);
  const rm = m % 60;
  return rm > 0 ? `${h}h ${rm}m` : `${h}h`;
}

/** Format a number as percentage */
export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}
