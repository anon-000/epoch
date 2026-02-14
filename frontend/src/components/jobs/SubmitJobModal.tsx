"use client";

import { useState, useEffect } from "react";
import { Modal } from "@/components/shared/Modal";
import { Select } from "@/components/shared/Select";
import { api } from "@/lib/api";
import type { JobSubmitRequest, JobPriority, TenantConfig } from "@/lib/types";

interface SubmitJobModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (req: JobSubmitRequest) => Promise<void>;
}

const PRIORITY_OPTIONS = [
  { value: "NORMAL", label: "Normal" },
  { value: "HIGH", label: "High" },
  { value: "CRITICAL", label: "Critical" },
];

const JOB_TYPE_OPTIONS = [
  { value: "jobs.data_processing:DataProcessingJob", label: "Data Processing" },
  { value: "jobs.long_running:LongRunningJob", label: "Long Running" },
];

export function SubmitJobModal({ open, onClose, onSubmit }: SubmitJobModalProps) {
  const [tenantOptions, setTenantOptions] = useState<{ value: string; label: string }[]>([]);
  const [form, setForm] = useState<JobSubmitRequest>({
    name: "",
    tenant_id: "",
    job_type: JOB_TYPE_OPTIONS[0].value,
    priority: "NORMAL",
    max_retries: 3,
    timeout_seconds: 3600,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch tenants when modal opens
  useEffect(() => {
    if (!open) return;
    api.get<TenantConfig[]>("/admin/tenants").then((tenants) => {
      const opts = tenants.map((t) => ({ value: t.tenant_id, label: t.tenant_id }));
      setTenantOptions(opts);
      if (opts.length > 0 && !form.tenant_id) {
        setForm((prev) => ({ ...prev, tenant_id: opts[0].value }));
      }
    }).catch(() => {
      setTenantOptions([]);
    });
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(form);
      setForm({ name: "", tenant_id: tenantOptions[0]?.value || "", job_type: JOB_TYPE_OPTIONS[0].value, priority: "NORMAL", max_retries: 3, timeout_seconds: 3600 });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit job");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Submit New Job">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-slate-400">Name</label>
          <input
            className="input"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-sm text-slate-400">Tenant</label>
            <Select
              value={form.tenant_id}
              onChange={(v) => setForm({ ...form, tenant_id: v })}
              options={tenantOptions}
              placeholder={tenantOptions.length === 0 ? "No tenants found" : "Select tenant..."}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-400">Job Type</label>
            <Select
              value={form.job_type}
              onChange={(v) => setForm({ ...form, job_type: v })}
              options={JOB_TYPE_OPTIONS}
            />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-400">Priority</label>
          <Select
            value={form.priority || "NORMAL"}
            onChange={(v) => setForm({ ...form, priority: v as JobPriority })}
            options={PRIORITY_OPTIONS}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-sm text-slate-400">Max Retries</label>
            <input
              className="input"
              type="number"
              min={0}
              max={100}
              value={form.max_retries}
              onChange={(e) => setForm({ ...form, max_retries: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-400">Timeout (seconds)</label>
            <input
              className="input"
              type="number"
              min={1}
              max={86400}
              value={form.timeout_seconds}
              onChange={(e) => setForm({ ...form, timeout_seconds: Number(e.target.value) })}
            />
          </div>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Submitting..." : "Submit Job"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
