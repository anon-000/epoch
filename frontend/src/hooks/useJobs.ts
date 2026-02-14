"use client";

import { useState, useCallback, useMemo } from "react";
import { usePolling } from "./usePolling";
import { api } from "@/lib/api";
import type { Job, JobListResponse, JobSubmitRequest, JobState } from "@/lib/types";

interface UseJobsOptions {
  limit?: number;
}

export function useJobs({ limit = 25 }: UseJobsOptions = {}) {
  const [offset, setOffset] = useState(0);
  const [stateFilter, setStateFilter] = useState<JobState | "">("");
  const [tenantFilter, setTenantFilter] = useState("");

  const params = useMemo(
    () => ({
      limit,
      offset,
      ...(stateFilter && { state: stateFilter }),
      ...(tenantFilter && { tenant_id: tenantFilter }),
    }),
    [limit, offset, stateFilter, tenantFilter]
  );

  const { data, error, loading, refetch } = usePolling<JobListResponse>({
    fetcher: (signal) => api.get<JobListResponse>("/jobs", { params, signal }),
  });

  const submitJob = useCallback(
    async (req: JobSubmitRequest): Promise<Job> => {
      const job = await api.post<Job>("/jobs", req);
      refetch();
      return job;
    },
    [refetch]
  );

  const cancelJob = useCallback(
    async (jobId: string): Promise<Job> => {
      const job = await api.post<Job>(`/jobs/${jobId}/cancel`);
      refetch();
      return job;
    },
    [refetch]
  );

  return {
    jobs: data?.jobs ?? [],
    total: data?.total ?? 0,
    loading,
    error,
    refetch,
    offset,
    setOffset,
    limit,
    stateFilter,
    setStateFilter,
    tenantFilter,
    setTenantFilter,
    submitJob,
    cancelJob,
  };
}
