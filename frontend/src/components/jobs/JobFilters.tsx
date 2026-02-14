"use client";

import { Select } from "@/components/shared/Select";
import type { JobState } from "@/lib/types";

const JOB_STATE_OPTIONS = [
  { value: "SUBMITTED", label: "Submitted" },
  { value: "QUEUED", label: "Queued" },
  { value: "SCHEDULED", label: "Scheduled" },
  { value: "RUNNING", label: "Running" },
  { value: "COMPLETED", label: "Completed" },
  { value: "FAILED", label: "Failed" },
  { value: "TIMED_OUT", label: "Timed Out" },
  { value: "CANCELLED", label: "Cancelled" },
  { value: "CHECKPOINTED", label: "Checkpointed" },
  { value: "PREEMPTED", label: "Preempted" },
  { value: "DEAD_LETTER", label: "Dead Letter" },
];

interface JobFiltersProps {
  stateFilter: JobState | "";
  onStateChange: (state: JobState | "") => void;
  tenantFilter: string;
  onTenantChange: (tenant: string) => void;
}

export function JobFilters({ stateFilter, onStateChange, tenantFilter, onTenantChange }: JobFiltersProps) {
  return (
    <div className="flex items-center gap-3">
      <Select
        value={stateFilter}
        onChange={(v) => onStateChange(v as JobState | "")}
        options={JOB_STATE_OPTIONS}
        placeholder="All States"
        className="w-44"
      />
      <input
        type="text"
        value={tenantFilter}
        onChange={(e) => onTenantChange(e.target.value)}
        placeholder="Filter by tenant..."
        className="input w-48"
      />
    </div>
  );
}
