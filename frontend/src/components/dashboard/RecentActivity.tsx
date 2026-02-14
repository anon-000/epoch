"use client";

import type { Job } from "@/lib/types";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { JOB_STATE_COLORS } from "@/lib/constants";
import { formatRelativeTime } from "@/lib/utils";

interface RecentActivityProps {
  jobs: Job[];
}

export function RecentActivity({ jobs }: RecentActivityProps) {
  if (jobs.length === 0) {
    return <p className="py-8 text-center text-sm text-slate-500">No recent activity</p>;
  }

  return (
    <div className="space-y-3">
      {jobs.map((job) => (
        <div
          key={job.id}
          className="flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/50 px-4 py-3"
        >
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-200">{job.name}</p>
            <p className="text-xs text-slate-500">{job.tenant_id} &middot; {job.job_type}</p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge label={job.state} color={JOB_STATE_COLORS[job.state]} />
            <span className="text-xs text-slate-500 whitespace-nowrap">
              {formatRelativeTime(job.updated_at)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
