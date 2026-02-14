"use client";

import type { Worker } from "@/lib/types";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { WORKER_STATE_COLORS } from "@/lib/constants";
import { formatRelativeTime, formatPercent } from "@/lib/utils";
import { Server } from "lucide-react";

interface WorkerCardProps {
  worker: Worker;
}

export function WorkerCard({ worker }: WorkerCardProps) {
  const utilization = worker.max_slots > 0 ? worker.current_load / worker.max_slots : 0;

  return (
    <div className="card space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-slate-700/50 p-2.5">
            <Server className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <p className="font-medium text-slate-200">{worker.hostname}</p>
            <p className="text-xs text-slate-500">PID: {worker.pid}</p>
          </div>
        </div>
        <StatusBadge label={worker.state} color={WORKER_STATE_COLORS[worker.state]} />
      </div>

      {/* Utilization bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-slate-400">
          <span>Slots: {worker.current_load} / {worker.max_slots}</span>
          <span>{formatPercent(utilization)}</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-700">
          <div
            className="h-full rounded-full bg-blue-500 transition-all duration-500"
            style={{ width: `${Math.min(Math.round(utilization * 100), 100)}%` }}
          />
        </div>
      </div>

      <div className="flex justify-between text-xs text-slate-500">
        <span>Registered: {formatRelativeTime(worker.registered_at)}</span>
        <span>Heartbeat: {formatRelativeTime(worker.last_heartbeat)}</span>
      </div>
    </div>
  );
}
