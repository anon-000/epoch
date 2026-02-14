"use client";

import { usePolling } from "./usePolling";
import { api } from "@/lib/api";
import type { WorkerListResponse } from "@/lib/types";

export function useWorkers() {
  return usePolling<WorkerListResponse>({
    fetcher: (signal) => api.get<WorkerListResponse>("/workers", { signal }),
  });
}
