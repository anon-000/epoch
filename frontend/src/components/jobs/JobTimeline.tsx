"use client";

import { useEffect, useState } from "react";
import type { JobEvent } from "@/lib/types";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

// Color mapping for event types
const EVENT_COLORS: Record<string, string> = {
  CREATED: "bg-slate-400",
  QUEUED: "bg-amber-400",
  SCHEDULED: "bg-sky-400",
  RUNNING: "bg-blue-400",
  COMPLETED: "bg-emerald-400",
  FAILED: "bg-red-400",
  RETRIED: "bg-amber-500",
  MANUAL_RETRY: "bg-indigo-400",
  TIMED_OUT: "bg-orange-400",
  CANCELLED: "bg-slate-500",
  DEAD_LETTER: "bg-rose-400",
  PREEMPTED: "bg-yellow-400",
  CHECKPOINTED: "bg-violet-400",
};

// Human-friendly labels
const EVENT_LABELS: Record<string, string> = {
  CREATED: "Created",
  QUEUED: "Queued",
  SCHEDULED: "Scheduled",
  RUNNING: "Running",
  COMPLETED: "Completed",
  FAILED: "Failed",
  RETRIED: "Retried",
  MANUAL_RETRY: "Manual Retry",
  TIMED_OUT: "Timed Out",
  CANCELLED: "Cancelled",
  DEAD_LETTER: "Dead Letter",
  PREEMPTED: "Preempted",
  CHECKPOINTED: "Checkpointed",
};

interface JobTimelineProps {
  jobId: string;
  /** Bumped externally to trigger a re-fetch (e.g. after retry) */
  refreshKey?: number;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function JobTimeline({ jobId, refreshKey }: JobTimelineProps) {
  const [events, setEvents] = useState<JobEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    api.get<JobEvent[]>(`/jobs/${jobId}/events`).then((data) => {
      if (!cancelled) {
        setEvents(data);
        setLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setLoading(false);
    });

    return () => { cancelled = true; };
  }, [jobId, refreshKey]);

  if (loading) {
    return (
      <div className="text-sm text-slate-500 py-4">Loading timeline...</div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="text-sm text-slate-500 py-4">No events recorded yet.</div>
    );
  }

  return (
    <div className="space-y-0">
      {events.map((event, i) => {
        const color = EVENT_COLORS[event.event] || "bg-slate-500";
        const label = EVENT_LABELS[event.event] || event.event;

        return (
          <div key={event.id} className="flex gap-4">
            {/* Timeline dot + connector */}
            <div className="flex flex-col items-center">
              <div className={cn("h-3 w-3 rounded-full shrink-0", color)} />
              {i < events.length - 1 && <div className="w-px flex-1 bg-slate-700" />}
            </div>

            {/* Content */}
            <div className="pb-5 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-slate-200">{label}</p>
                {event.attempt !== null && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-400">
                    Attempt {event.attempt}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{formatTime(event.timestamp)}</p>
              {event.detail && (
                <p className="text-xs text-slate-400 mt-1 break-words">{event.detail}</p>
              )}
              {event.worker_id && (
                <p className="text-[10px] text-slate-600 mt-0.5 font-mono">
                  worker: {event.worker_id.substring(0, 12)}...
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
