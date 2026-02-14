"use client";

import { useState } from "react";
import { Plus, RefreshCw, Pencil } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { TenantFormModal } from "@/components/tenants/TenantFormModal";
import { useTenants } from "@/hooks/useTenants";
import type { TenantConfig } from "@/lib/types";

export default function TenantsPage() {
  const { tenants, loading, refetch, createTenant, updateTenant } = useTenants();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<TenantConfig | null>(null);

  const columns: Column<TenantConfig>[] = [
    {
      key: "tenant_id",
      header: "Tenant ID",
      render: (t) => <span className="font-medium text-slate-200">{t.tenant_id}</span>,
    },
    { key: "max_concurrent", header: "Max Concurrent", render: (t) => t.max_concurrent_jobs },
    { key: "max_workers", header: "Max Workers", render: (t) => t.max_workers },
    { key: "priority_boost", header: "Priority Boost", render: (t) => t.priority_boost },
    {
      key: "actions",
      header: "",
      render: (t) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setEditing(t);
            setShowForm(true);
          }}
          className="btn-ghost px-2 py-1"
        >
          <Pencil className="h-4 w-4" />
        </button>
      ),
      className: "w-12",
    },
  ];

  return (
    <PageContainer
      title="Tenants"
      description="Manage tenant configurations and quotas"
      actions={
        <div className="flex items-center gap-2">
          <button onClick={refetch} className="btn-ghost">
            <RefreshCw className="h-4 w-4" />
          </button>
          <button
            onClick={() => {
              setEditing(null);
              setShowForm(true);
            }}
            className="btn-primary"
          >
            <Plus className="h-4 w-4" />
            Add Tenant
          </button>
        </div>
      }
    >
      <div className="card">
        {loading && tenants.length === 0 ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner />
          </div>
        ) : tenants.length === 0 ? (
          <EmptyState title="No tenants" message="Create a tenant configuration to get started." />
        ) : (
          <DataTable columns={columns} data={tenants} keyExtractor={(t) => t.tenant_id} />
        )}
      </div>

      <TenantFormModal
        open={showForm}
        onClose={() => {
          setShowForm(false);
          setEditing(null);
        }}
        editing={editing}
        onSubmit={async (req) => {
          if (editing) {
            await updateTenant(editing.tenant_id, req);
          } else {
            await createTenant(req);
          }
        }}
      />
    </PageContainer>
  );
}
