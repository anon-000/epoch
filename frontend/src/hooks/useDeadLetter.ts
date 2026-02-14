"use client";

import { useState, useMemo } from "react";
import { usePolling } from "./usePolling";
import { api } from "@/lib/api";
import type { DeadLetterListResponse } from "@/lib/types";

interface UseDeadLetterOptions {
  limit?: number;
}

export function useDeadLetter({ limit = 25 }: UseDeadLetterOptions = {}) {
  const [offset, setOffset] = useState(0);

  const params = useMemo(() => ({ limit, offset }), [limit, offset]);

  const { data, error, loading, refetch } = usePolling<DeadLetterListResponse>({
    fetcher: (signal) => api.get<DeadLetterListResponse>("/admin/dead-letter", { params, signal }),
  });

  return {
    items: data?.items ?? [],
    total: data?.total ?? 0,
    loading,
    error,
    refetch,
    offset,
    setOffset,
    limit,
  };
}
