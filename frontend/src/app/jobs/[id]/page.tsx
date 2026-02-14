"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, XCircle, RotateCcw } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { JobTimeline } from "@/components/jobs/JobTimeline";
import { usePolling } from "@/hooks/usePolling";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { JOB_STATE_COLORS, PRIORITY_COLORS } from "@/lib/constants";
import { formatDate, formatDuration } from "@/lib/utils";
import { useState } from "react";

const TERMINAL_STATES = new Set(["COMPLETED", "CANCELLED", "DEAD_LETTER"]);
const RETRYABLE_STATES = new Set(["FAILED", "TIMED_OUT", "DEAD_LETTER"]);

export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [cancelling, setCancelling] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [timelineRefresh, setTimelineRefresh] = useState(0);

  const { data: job, loading, refetch } = usePolling<Job>({
    fetcher: (signal) => api.get<Job>(`/jobs/${id}`, { signal }),
  });

  const handleCancel = async () => {
    if (!job || cancelling) return;
    setCancelling(true);
    try {
      await api.post(`/jobs/${job.id}/cancel`);
      refetch();
      setTimelineRefresh((k) => k + 1);
    } finally {
      setCancelling(false);
    }
  };

  const handleRetry = async () => {
    if (!job || retrying) return;
    setRetrying(true);
    try {
      await api.post(`/jobs/${job.id}/retry`);
      refetch();
      setTimelineRefresh((k) => k + 1);
    } finally {
      setRetrying(false);
    }
  };

  if (loading || !job) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const canCancel = !TERMINAL_STATES.has(job.state);
  const canRetry = RETRYABLE_STATES.has(job.state);

  return (
    <PageContainer
      title={job.name}
      description={`Job ${job.id}`}
      actions={
        <div className="flex items-center gap-2">
          <button onClick={() => router.push("/jobs")} className="btn-ghost">
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          {canRetry && (
            <button onClick={handleRetry} disabled={retrying} className="btn-primary">
              <RotateCcw className="h-4 w-4" />
              {retrying ? "Retrying..." : "Retry Job"}
            </button>
          )}
          {canCancel && (
            <button onClick={handleCancel} disabled={cancelling} className="btn-danger">
              <XCircle className="h-4 w-4" />
              {cancelling ? "Cancelling..." : "Cancel Job"}
            </button>
          )}
        </div>
      }
    >
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Info */}
        <div className="card lg:col-span-2 space-y-4">
          <h3 className="text-sm font-medium uppercase tracking-wider text-slate-400">Details</h3>
          <div className="grid grid-cols-2 gap-4">
            <InfoRow label="State">
              <StatusBadge label={job.state} color={JOB_STATE_COLORS[job.state]} />
            </InfoRow>
            <InfoRow label="Priority">
              <StatusBadge label={job.priority} color={PRIORITY_COLORS[job.priority]} />
            </InfoRow>
            <InfoRow label="Tenant" value={job.tenant_id} />
            <InfoRow label="Job Type" value={job.job_type} />
            <InfoRow label="Attempt" value={`${job.attempt} / ${job.max_retries}`} />
            <InfoRow label="Timeout" value={formatDuration(job.timeout_seconds)} />
            <InfoRow label="Created" value={formatDate(job.created_at)} />
            <InfoRow label="Updated" value={formatDate(job.updated_at)} />
            {job.assigned_worker_id && (
              <InfoRow label="Worker" value={job.assigned_worker_id.slice(0, 8) + "..."} />
            )}
          </div>
          {job.error_message && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
              <p className="text-sm font-medium text-red-400">Error</p>
              <p className="mt-1 text-sm text-red-300">{job.error_message}</p>
            </div>
          )}
          {Object.keys(job.payload).length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-slate-400">Payload</h4>
              <pre className="overflow-x-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-300">
                {JSON.stringify(job.payload, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Timeline */}
        <div className="card">
          <h3 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-400">
            Timeline
          </h3>
          <JobTimeline jobId={job.id} refreshKey={timelineRefresh} />
        </div>
      </div>
    </PageContainer>
  );
}

function InfoRow({
  label,
  value,
  children,
}: {
  label: string;
  value?: string;
  children?: React.ReactNode;
}) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <div className="mt-0.5 text-sm text-slate-200">{children ?? value ?? "—"}</div>
    </div>
  );
}
