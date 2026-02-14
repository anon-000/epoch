"use client";

import { useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { Pagination } from "@/components/shared/Pagination";
import { JobFilters } from "@/components/jobs/JobFilters";
import { JobsTable } from "@/components/jobs/JobsTable";
import { SubmitJobModal } from "@/components/jobs/SubmitJobModal";
import { useJobs } from "@/hooks/useJobs";

export default function JobsPage() {
  const [showSubmit, setShowSubmit] = useState(false);
  const {
    jobs,
    total,
    loading,
    refetch,
    offset,
    setOffset,
    limit,
    stateFilter,
    setStateFilter,
    tenantFilter,
    setTenantFilter,
    submitJob,
  } = useJobs();

  return (
    <PageContainer
      title="Jobs"
      description="View and manage scheduled jobs"
      actions={
        <div className="flex items-center gap-2">
          <button onClick={refetch} className="btn-ghost">
            <RefreshCw className="h-4 w-4" />
          </button>
          <button onClick={() => setShowSubmit(true)} className="btn-primary">
            <Plus className="h-4 w-4" />
            Submit Job
          </button>
        </div>
      }
    >
      <div className="card">
        <div className="mb-4">
          <JobFilters
            stateFilter={stateFilter}
            onStateChange={(v) => {
              setStateFilter(v);
              setOffset(0);
            }}
            tenantFilter={tenantFilter}
            onTenantChange={(v) => {
              setTenantFilter(v);
              setOffset(0);
            }}
          />
        </div>

        {loading && jobs.length === 0 ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner />
          </div>
        ) : jobs.length === 0 ? (
          <EmptyState title="No jobs found" message="Submit a new job or adjust your filters." />
        ) : (
          <>
            <JobsTable jobs={jobs} />
            <Pagination offset={offset} limit={limit} total={total} onChange={setOffset} />
          </>
        )}
      </div>

      <SubmitJobModal
        open={showSubmit}
        onClose={() => setShowSubmit(false)}
        onSubmit={async (req) => {
          await submitJob(req);
        }}
      />
    </PageContainer>
  );
}
