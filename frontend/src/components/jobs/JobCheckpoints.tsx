"use client";

import { HardDrive, Star, Database, Clock } from "lucide-react";
import { usePolling } from "@/hooks/usePolling";
import { api } from "@/lib/api";
import type { CheckpointListResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

interface JobCheckpointsProps {
  jobId: string;
}

export function JobCheckpoints({ jobId }: JobCheckpointsProps) {
  const { data, loading } = usePolling<CheckpointListResponse>({
    fetcher: (signal) =>
      api.get<CheckpointListResponse>(`/jobs/${jobId}/checkpoints`, { signal }),
  });

  // Don't render the section at all if no checkpoints exist and not loading
  if (!loading && (!data || data.total === 0)) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium uppercase tracking-wider text-slate-400">
          Checkpoints
        </h3>
        {data && data.total > 0 && (
          <span className="text-xs text-slate-500">
            {data.total} checkpoint{data.total !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {loading && !data ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-slate-400" />
          Loading...
        </div>
      ) : (
        <div className="space-y-2">
          {data?.checkpoints.map((cp) => (
            <div
              key={cp.id}
              className={cn(
                "group relative rounded-lg border px-4 py-3 transition-colors",
                cp.is_latest
                  ? "border-violet-500/40 bg-violet-500/5 hover:bg-violet-500/10"
                  : "border-slate-700/60 bg-slate-800/30 hover:bg-slate-800/60"
              )}
            >
              {/* Latest badge */}
              {cp.is_latest && (
                <div className="absolute -top-2 right-3">
                  <span className="inline-flex items-center gap-1 rounded-full bg-violet-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-violet-300 border border-violet-500/30">
                    <Star className="h-2.5 w-2.5" />
                    Latest
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between gap-4">
                {/* Left: sequence + icon */}
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-lg shrink-0",
                      cp.is_latest
                        ? "bg-violet-500/20 text-violet-400"
                        : "bg-slate-700/50 text-slate-400"
                    )}
                  >
                    <HardDrive className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-200">
                        Sequence #{cp.sequence_number}
                      </span>
                    </div>
                    <p
                      className="text-xs text-slate-500 truncate font-mono mt-0.5"
                      title={cp.storage_path}
                    >
                      {cp.storage_path.split("/").slice(-2).join("/")}
                    </p>
                  </div>
                </div>

                {/* Right: metadata */}
                <div className="flex items-center gap-4 shrink-0">
                  {/* Size */}
                  <div className="flex items-center gap-1.5" title="Size">
                    <Database className="h-3 w-3 text-slate-500" />
                    <span className="text-xs text-slate-400 font-mono">
                      {formatBytes(cp.size_bytes)}
                    </span>
                  </div>
                  {/* Time */}
                  <div
                    className="flex items-center gap-1.5"
                    title={formatTimestamp(cp.created_at)}
                  >
                    <Clock className="h-3 w-3 text-slate-500" />
                    <span className="text-xs text-slate-400">
                      {timeAgo(cp.created_at)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
