"use client";

import {
  Briefcase,
  Clock,
  CheckCircle,
  AlertTriangle,
  Server,
  Layers,
} from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { MetricCard } from "@/components/shared/MetricCard";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { JobStateChart } from "@/components/dashboard/JobStateChart";
import { WorkerUtilizationBar } from "@/components/dashboard/WorkerUtilizationBar";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { useMetrics } from "@/hooks/useMetrics";
import { useJobs } from "@/hooks/useJobs";
import { formatDuration, formatPercent } from "@/lib/utils";

export default function DashboardPage() {
  const { data: metrics, loading } = useMetrics();
  const { jobs: recentJobs } = useJobs({ limit: 8 });

  if (loading || !metrics) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <PageContainer title="Dashboard" description="System overview and real-time metrics">
      {/* Metric cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          title="Total Jobs"
          value={metrics.jobs.total}
          icon={Briefcase}
          subtitle={`${metrics.jobs.throughput_last_hour} completed/hr`}
        />
        <MetricCard
          title="Avg Latency"
          value={metrics.jobs.avg_latency_seconds ? formatDuration(metrics.jobs.avg_latency_seconds) : "—"}
          icon={Clock}
          subtitle={
            metrics.jobs.avg_wait_time_seconds
              ? `${formatDuration(metrics.jobs.avg_wait_time_seconds)} avg wait`
              : undefined
          }
        />
        <MetricCard
          title="Completed"
          value={metrics.jobs.by_state["COMPLETED"] ?? 0}
          icon={CheckCircle}
        />
        <MetricCard
          title="Failure Rate"
          value={formatPercent(metrics.jobs.failure_rate)}
          icon={AlertTriangle}
          subtitle={`${metrics.dead_letter.total} dead letters`}
        />
        <MetricCard
          title="Workers"
          value={`${metrics.workers.total_load} / ${metrics.workers.total_capacity}`}
          icon={Server}
          subtitle={`${formatPercent(metrics.workers.utilization)} utilized`}
        />
        <MetricCard
          title="Queue Depth"
          value={metrics.queue.depth}
          icon={Layers}
          subtitle={`${metrics.checkpoints.total} checkpoints`}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-400">
            Jobs by State
          </h3>
          <JobStateChart byState={metrics.jobs.by_state} />
        </div>
        <div className="card space-y-6">
          <div>
            <h3 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-400">
              Worker Utilization
            </h3>
            <WorkerUtilizationBar
              load={metrics.workers.total_load}
              capacity={metrics.workers.total_capacity}
            />
          </div>
          <div>
            <h3 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-400">
              Tenant Activity
            </h3>
            <div className="space-y-2">
              {Object.entries(metrics.tenants).length === 0 ? (
                <p className="text-sm text-slate-500">No tenant data</p>
              ) : (
                Object.entries(metrics.tenants).map(([tenantId, states]) => {
                  const total = Object.values(states).reduce((sum, n) => sum + n, 0);
                  const running = states["RUNNING"] ?? 0;
                  return (
                    <div key={tenantId} className="flex items-center justify-between text-sm">
                      <span className="text-slate-300">{tenantId}</span>
                      <span className="text-slate-500">
                        {running} running / {total} total
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recent activity */}
      <div className="card">
        <h3 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-400">
          Recent Activity
        </h3>
        <RecentActivity jobs={recentJobs} />
      </div>
    </PageContainer>
  );
}
