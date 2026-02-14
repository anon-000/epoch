"use client";

import { RefreshCw } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { Pagination } from "@/components/shared/Pagination";
import { useDeadLetter } from "@/hooks/useDeadLetter";
import { formatDate } from "@/lib/utils";
import type { DeadLetterJob } from "@/lib/types";

export default function DeadLetterPage() {
  const { items, total, loading, refetch, offset, setOffset, limit } = useDeadLetter();

  const columns: Column<DeadLetterJob>[] = [
    {
      key: "job_id",
      header: "Job ID",
      render: (dl) => <span className="font-mono text-xs text-slate-300">{dl.job_id}</span>,
    },
    { key: "attempts", header: "Attempts", render: (dl) => dl.total_attempts },
    {
      key: "error",
      header: "Final Error",
      render: (dl) => (
        <p className="max-w-md truncate text-red-400" title={dl.final_error ?? undefined}>
          {dl.final_error ?? "—"}
        </p>
      ),
    },
    { key: "moved_at", header: "Moved At", render: (dl) => formatDate(dl.moved_at) },
  ];

  return (
    <PageContainer
      title="Dead Letter Queue"
      description="Jobs that exhausted all retries"
      actions={
        <button onClick={refetch} className="btn-ghost">
          <RefreshCw className="h-4 w-4" />
        </button>
      }
    >
      <div className="card">
        {loading && items.length === 0 ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner />
          </div>
        ) : items.length === 0 ? (
          <EmptyState title="No dead letters" message="No jobs have been moved to the dead letter queue." />
        ) : (
          <>
            <DataTable columns={columns} data={items} keyExtractor={(dl) => dl.id} />
            <Pagination offset={offset} limit={limit} total={total} onChange={setOffset} />
          </>
        )}
      </div>
    </PageContainer>
  );
}
