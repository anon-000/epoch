"use client";

import { useState, useCallback, useMemo } from "react";
import { usePolling } from "./usePolling";
import { api } from "@/lib/api";
import type { AuditLogResponse, AuditEvent } from "@/lib/types";

interface UseAuditLogOptions {
  limit?: number;
}

function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  d.setHours(0, 0, 0, 0);
  return d.toISOString();
}

export function useAuditLog({ limit = 50 }: UseAuditLogOptions = {}) {
  const [offset, setOffset] = useState(0);
  const [eventFilter, setEventFilter] = useState("");
  const [tenantFilter, setTenantFilter] = useState("");
  const [jobNameSearch, setJobNameSearch] = useState("");
  const [since, setSince] = useState<string>(daysAgo(7));
  const [until, setUntil] = useState<string>("");

  const params = useMemo(
    () => ({
      limit,
      offset,
      ...(eventFilter && { event: eventFilter }),
      ...(tenantFilter && { tenant_id: tenantFilter }),
      ...(jobNameSearch && { job_name: jobNameSearch }),
      ...(since && { since }),
      ...(until && { until }),
    }),
    [limit, offset, eventFilter, tenantFilter, jobNameSearch, since, until]
  );

  const { data, error, loading, refetch } = usePolling<AuditLogResponse>({
    fetcher: (signal) => api.get<AuditLogResponse>("/events", { params, signal }),
  });

  return {
    events: data?.events ?? [],
    total: data?.total ?? 0,
    loading,
    error,
    refetch,
    offset,
    setOffset,
    limit,
    eventFilter,
    setEventFilter,
    tenantFilter,
    setTenantFilter,
    jobNameSearch,
    setJobNameSearch,
    since,
    setSince,
    until,
    setUntil,
  };
}

