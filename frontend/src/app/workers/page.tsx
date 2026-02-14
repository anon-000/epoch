"use client";

import { RefreshCw } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { WorkerCard } from "@/components/workers/WorkerCard";
import { useWorkers } from "@/hooks/useWorkers";

export default function WorkersPage() {
  const { data, loading, refetch } = useWorkers();
  const workers = data?.workers ?? [];

  return (
    <PageContainer
      title="Workers"
      description="Monitor registered worker instances"
      actions={
        <button onClick={refetch} className="btn-ghost">
          <RefreshCw className="h-4 w-4" />
        </button>
      }
    >
      {loading && workers.length === 0 ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : workers.length === 0 ? (
        <EmptyState title="No workers" message="No worker instances are currently registered." />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {workers.map((worker) => (
            <WorkerCard key={worker.id} worker={worker} />
          ))}
        </div>
      )}
    </PageContainer>
  );
}
