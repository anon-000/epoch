"use client";

import { formatPercent } from "@/lib/utils";

interface WorkerUtilizationBarProps {
  load: number;
  capacity: number;
}

export function WorkerUtilizationBar({ load, capacity }: WorkerUtilizationBarProps) {
  const utilization = capacity > 0 ? load / capacity : 0;
  const percent = Math.round(utilization * 100);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-400">Worker Utilization</span>
        <span className="font-medium text-slate-200">
          {load} / {capacity} slots ({formatPercent(utilization)})
        </span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-700">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-500"
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
    </div>
  );
}
