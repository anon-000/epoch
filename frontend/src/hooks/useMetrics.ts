"use client";

import { usePolling } from "./usePolling";
import { api } from "@/lib/api";
import type { MetricsResponse } from "@/lib/types";

export function useMetrics() {
  return usePolling<MetricsResponse>({
    fetcher: (signal) => api.get<MetricsResponse>("/metrics", { signal }),
  });
}
