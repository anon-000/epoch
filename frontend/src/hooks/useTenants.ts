"use client";

import { useCallback } from "react";
import { usePolling } from "./usePolling";
import { api } from "@/lib/api";
import type { TenantConfig, TenantConfigRequest } from "@/lib/types";

export function useTenants() {
  const { data, error, loading, refetch } = usePolling<TenantConfig[]>({
    fetcher: (signal) => api.get<TenantConfig[]>("/admin/tenants", { signal }),
  });

  const createTenant = useCallback(
    async (req: TenantConfigRequest): Promise<TenantConfig> => {
      const tenant = await api.post<TenantConfig>("/admin/tenants", req);
      refetch();
      return tenant;
    },
    [refetch]
  );

  const updateTenant = useCallback(
    async (tenantId: string, req: TenantConfigRequest): Promise<TenantConfig> => {
      const tenant = await api.put<TenantConfig>(`/admin/tenants/${tenantId}`, req);
      refetch();
      return tenant;
    },
    [refetch]
  );

  return {
    tenants: data ?? [],
    loading,
    error,
    refetch,
    createTenant,
    updateTenant,
  };
}
