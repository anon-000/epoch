"use client";

import { useRouter } from "next/navigation";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { Job } from "@/lib/types";
import { JOB_STATE_COLORS, PRIORITY_COLORS } from "@/lib/constants";
import { formatRelativeTime } from "@/lib/utils";

interface JobsTableProps {
  jobs: Job[];
}

export function JobsTable({ jobs }: JobsTableProps) {
  const router = useRouter();

  const columns: Column<Job>[] = [
    {
      key: "name",
      header: "Name",
      render: (job) => (
        <div>
          <p className="font-medium text-slate-200">{job.name}</p>
          <p className="text-xs text-slate-500">{job.id.slice(0, 8)}...</p>
        </div>
      ),
    },
    {
      key: "tenant",
      header: "Tenant",
      render: (job) => job.tenant_id,
    },
    {
      key: "type",
      header: "Type",
      render: (job) => job.job_type,
    },
    {
      key: "priority",
      header: "Priority",
      render: (job) => <StatusBadge label={job.priority} color={PRIORITY_COLORS[job.priority]} />,
    },
    {
      key: "state",
      header: "State",
      render: (job) => <StatusBadge label={job.state} color={JOB_STATE_COLORS[job.state]} />,
    },
    {
      key: "attempt",
      header: "Attempt",
      render: (job) => `${job.attempt} / ${job.max_retries}`,
    },
    {
      key: "updated",
      header: "Updated",
      render: (job) => formatRelativeTime(job.updated_at),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={jobs}
      keyExtractor={(job) => job.id}
      onRowClick={(job) => router.push(`/jobs/${job.id}`)}
    />
  );
}
