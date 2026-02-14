"use client";

import { useState, useCallback, useMemo } from "react";
import { RefreshCw, Search, X, FileText, Calendar } from "lucide-react";
import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { Pagination } from "@/components/shared/Pagination";
import { useAuditLog } from "@/hooks/useAuditLog";
import { cn } from "@/lib/utils";

// Event type badge colors
const EVENT_BADGE: Record<string, { bg: string; text: string; dot: string }> = {
  CREATED:      { bg: "bg-slate-500/15",   text: "text-slate-300",   dot: "bg-slate-400"   },
  QUEUED:       { bg: "bg-amber-500/15",   text: "text-amber-300",   dot: "bg-amber-400"   },
  SCHEDULED:    { bg: "bg-sky-500/15",     text: "text-sky-300",     dot: "bg-sky-400"     },
  RUNNING:      { bg: "bg-blue-500/15",    text: "text-blue-300",    dot: "bg-blue-400"    },
  COMPLETED:    { bg: "bg-emerald-500/15", text: "text-emerald-300", dot: "bg-emerald-400" },
  FAILED:       { bg: "bg-red-500/15",     text: "text-red-300",     dot: "bg-red-400"     },
  RETRIED:      { bg: "bg-amber-500/15",   text: "text-amber-300",   dot: "bg-amber-500"   },
  MANUAL_RETRY: { bg: "bg-indigo-500/15",  text: "text-indigo-300",  dot: "bg-indigo-400"  },
  TIMED_OUT:    { bg: "bg-orange-500/15",  text: "text-orange-300",  dot: "bg-orange-400"  },
  CANCELLED:    { bg: "bg-slate-500/15",   text: "text-slate-400",   dot: "bg-slate-500"   },
  DEAD_LETTER:  { bg: "bg-rose-500/15",    text: "text-rose-300",    dot: "bg-rose-400"    },
  PREEMPTED:    { bg: "bg-yellow-500/15",  text: "text-yellow-300",  dot: "bg-yellow-400"  },
  CHECKPOINTED: { bg: "bg-violet-500/15",  text: "text-violet-300",  dot: "bg-violet-400"  },
};

const ALL_EVENTS = [
  "CREATED", "QUEUED", "SCHEDULED", "RUNNING", "COMPLETED",
  "FAILED", "RETRIED", "MANUAL_RETRY", "TIMED_OUT",
  "CANCELLED", "DEAD_LETTER", "PREEMPTED", "CHECKPOINTED",
];

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// Preset date range helpers
function daysAgoISO(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  d.setHours(0, 0, 0, 0);
  return d.toISOString();
}

function toDateInputValue(iso: string): string {
  if (!iso) return "";
  return new Date(iso).toISOString().slice(0, 10);
}

function fromDateInputValue(dateStr: string, endOfDay = false): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (endOfDay) d.setHours(23, 59, 59, 999);
  else d.setHours(0, 0, 0, 0);
  return d.toISOString();
}

type DatePreset = "24h" | "7d" | "30d" | "all";

export default function AuditLogsPage() {
  const {
    events,
    total,
    loading,
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
  } = useAuditLog();

  const [searchInput, setSearchInput] = useState("");
  const [activePreset, setActivePreset] = useState<DatePreset>("7d");

  const handleSearch = useCallback(() => {
    setJobNameSearch(searchInput);
    setOffset(0);
  }, [searchInput, setJobNameSearch, setOffset]);

  const applyPreset = useCallback(
    (preset: DatePreset) => {
      setActivePreset(preset);
      setUntil("");
      setOffset(0);
      switch (preset) {
        case "24h":
          setSince(daysAgoISO(1));
          break;
        case "7d":
          setSince(daysAgoISO(7));
          break;
        case "30d":
          setSince(daysAgoISO(30));
          break;
        case "all":
          setSince("");
          break;
      }
    },
    [setSince, setUntil, setOffset]
  );

  const clearFilters = useCallback(() => {
    setEventFilter("");
    setTenantFilter("");
    setJobNameSearch("");
    setSearchInput("");
    setSince(daysAgoISO(7));
    setUntil("");
    setActivePreset("7d");
    setOffset(0);
  }, [setEventFilter, setTenantFilter, setJobNameSearch, setSince, setUntil, setOffset]);

  const hasFilters = eventFilter || tenantFilter || jobNameSearch || activePreset !== "7d";

  return (
    <PageContainer
      title="Audit Logs"
      description="Immutable event history across all jobs"
      actions={
        <button onClick={refetch} className="btn-ghost">
          <RefreshCw className="h-4 w-4" />
        </button>
      }
    >
      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-3">
          {/* Event type filter */}
          <select
            value={eventFilter}
            onChange={(e) => {
              setEventFilter(e.target.value);
              setOffset(0);
            }}
            className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Events</option>
            {ALL_EVENTS.map((ev) => (
              <option key={ev} value={ev}>
                {ev.replace(/_/g, " ")}
              </option>
            ))}
          </select>

          {/* Tenant filter */}
          <input
            type="text"
            placeholder="Tenant ID..."
            value={tenantFilter}
            onChange={(e) => {
              setTenantFilter(e.target.value);
              setOffset(0);
            }}
            className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 w-40"
          />

          {/* Job name search */}
          <div className="flex items-center gap-1">
            <input
              type="text"
              placeholder="Search job name..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 w-48"
            />
            <button onClick={handleSearch} className="btn-ghost px-2 py-2">
              <Search className="h-4 w-4" />
            </button>
          </div>

          {/* Clear filters */}
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1 rounded-lg border border-slate-600 bg-slate-800/50 px-3 py-2 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors"
            >
              <X className="h-3 w-3" />
              Clear filters
            </button>
          )}

          {/* Total count */}
          <div className="ml-auto text-sm text-slate-500">
            {total.toLocaleString()} event{total !== 1 ? "s" : ""}
          </div>
        </div>

        {/* Date range row */}
        <div className="flex flex-wrap items-center gap-3 mt-3 pt-3 border-t border-slate-700/50">
          <Calendar className="h-4 w-4 text-slate-500" />
          <span className="text-xs text-slate-500 mr-1">Range:</span>

          {/* Preset buttons */}
          {(["24h", "7d", "30d", "all"] as DatePreset[]).map((preset) => (
            <button
              key={preset}
              onClick={() => applyPreset(preset)}
              className={cn(
                "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
                activePreset === preset
                  ? "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                  : "bg-slate-800 text-slate-400 border border-slate-600 hover:text-slate-200 hover:border-slate-500"
              )}
            >
              {preset === "all" ? "All time" : `Last ${preset}`}
            </button>
          ))}

          <div className="h-4 w-px bg-slate-700 mx-1" />

          {/* Custom date inputs */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500">From</label>
            <input
              type="date"
              value={toDateInputValue(since)}
              onChange={(e) => {
                setActivePreset("all"); // deselect presets when custom
                setSince(fromDateInputValue(e.target.value));
                setOffset(0);
              }}
              className="rounded-md border border-slate-600 bg-slate-800 px-2 py-1 text-xs text-slate-200 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 [color-scheme:dark]"
            />
            <label className="text-xs text-slate-500">To</label>
            <input
              type="date"
              value={toDateInputValue(until)}
              onChange={(e) => {
                setActivePreset("all"); // deselect presets when custom
                setUntil(fromDateInputValue(e.target.value, true));
                setOffset(0);
              }}
              className="rounded-md border border-slate-600 bg-slate-800 px-2 py-1 text-xs text-slate-200 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 [color-scheme:dark]"
            />
          </div>
        </div>
      </div>

      {/* Event list */}
      <div className="card p-0">
        {loading && events.length === 0 ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner />
          </div>
        ) : events.length === 0 ? (
          <div className="p-6">
            <EmptyState
              title="No events found"
              message={hasFilters ? "Try adjusting your filters." : "Events will appear as jobs are processed."}
            />
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="grid grid-cols-[1fr_140px_100px_80px_1fr_100px] gap-4 border-b border-slate-700 px-5 py-3 text-xs font-medium uppercase tracking-wider text-slate-500">
              <span>Event</span>
              <span>Job</span>
              <span>Tenant</span>
              <span>Attempt</span>
              <span>Detail</span>
              <span className="text-right">Time</span>
            </div>

            {/* Rows */}
            <div className="divide-y divide-slate-800">
              {events.map((ev) => {
                const badge = EVENT_BADGE[ev.event] || EVENT_BADGE.CREATED;

                return (
                  <div
                    key={ev.id}
                    className="grid grid-cols-[1fr_140px_100px_80px_1fr_100px] gap-4 px-5 py-3.5 hover:bg-slate-800/40 transition-colors group"
                  >
                    {/* Event badge */}
                    <div className="flex items-center gap-2 min-w-0">
                      <div className={cn("h-2 w-2 rounded-full shrink-0", badge.dot)} />
                      <span
                        className={cn(
                          "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
                          badge.bg,
                          badge.text
                        )}
                      >
                        {ev.event.replace(/_/g, " ")}
                      </span>
                    </div>

                    {/* Job name + link */}
                    <div className="flex items-center min-w-0">
                      <Link
                        href={`/jobs/${ev.job_id}`}
                        className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300 truncate transition-colors"
                      >
                        <FileText className="h-3.5 w-3.5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                        <span className="truncate">{ev.job_name}</span>
                      </Link>
                    </div>

                    {/* Tenant */}
                    <div className="flex items-center">
                      <span className="text-xs text-slate-400 truncate">{ev.tenant_id}</span>
                    </div>

                    {/* Attempt */}
                    <div className="flex items-center">
                      {ev.attempt !== null ? (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 font-mono">
                          #{ev.attempt}
                        </span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </div>

                    {/* Detail */}
                    <div className="flex items-center min-w-0">
                      <span className="text-xs text-slate-400 truncate">
                        {ev.detail || "—"}
                      </span>
                    </div>

                    {/* Timestamp */}
                    <div className="flex items-center justify-end">
                      <span
                        className="text-xs text-slate-500 cursor-default"
                        title={formatTimestamp(ev.timestamp)}
                      >
                        {timeAgo(ev.timestamp)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Pagination */}
            <div className="px-4 pb-3">
              <Pagination offset={offset} limit={limit} total={total} onChange={setOffset} />
            </div>
          </>
        )}
      </div>
    </PageContainer>
  );
}
