"use client";

import { useState, useEffect } from "react";
import { Modal } from "@/components/shared/Modal";
import type { TenantConfig, TenantConfigRequest } from "@/lib/types";
import { ApiError } from "@/lib/api";

interface TenantFormModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (req: TenantConfigRequest) => Promise<void>;
  editing?: TenantConfig | null;
}

export function TenantFormModal({ open, onClose, onSubmit, editing }: TenantFormModalProps) {
  const [form, setForm] = useState<TenantConfigRequest>({
    tenant_id: "",
    max_concurrent_jobs: 10,
    max_workers: 5,
    priority_boost: 0,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editing) {
      setForm({
        tenant_id: editing.tenant_id,
        max_concurrent_jobs: editing.max_concurrent_jobs,
        max_workers: editing.max_workers,
        priority_boost: editing.priority_boost,
      });
    } else {
      setForm({ tenant_id: "", max_concurrent_jobs: 10, max_workers: 5, priority_boost: 0 });
    }
  }, [editing, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(form);
      onClose();
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object" && "detail" in err.body) {
        setError(String((err.body as any).detail));
      } else {
        setError(err instanceof Error ? err.message : "Failed to save tenant");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={editing ? "Edit Tenant" : "Create Tenant"}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-slate-400">Tenant ID</label>
          <input
            className="input"
            required
            disabled={!!editing}
            value={form.tenant_id}
            onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
          />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="mb-1 block text-sm text-slate-400">Max Concurrent</label>
            <input
              className="input"
              type="number"
              min={1}
              max={1000}
              value={form.max_concurrent_jobs}
              onChange={(e) => setForm({ ...form, max_concurrent_jobs: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-400">Max Workers</label>
            <input
              className="input"
              type="number"
              min={1}
              max={100}
              value={form.max_workers}
              onChange={(e) => setForm({ ...form, max_workers: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-400">Priority Boost</label>
            <input
              className="input"
              type="number"
              min={0}
              max={10}
              value={form.priority_boost}
              onChange={(e) => setForm({ ...form, priority_boost: Number(e.target.value) })}
            />
          </div>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Saving..." : editing ? "Update" : "Create"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
