"use client";

import { cn } from "@/lib/utils";

const colorMap: Record<string, string> = {
  slate: "bg-slate-500/20 text-slate-300 border-slate-500/30",
  amber: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  sky: "bg-sky-500/20 text-sky-300 border-sky-500/30",
  blue: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  emerald: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  red: "bg-red-500/20 text-red-300 border-red-500/30",
  orange: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  violet: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  yellow: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  rose: "bg-rose-500/20 text-rose-300 border-rose-500/30",
};

interface StatusBadgeProps {
  label: string;
  color: string;
  className?: string;
}

export function StatusBadge({ label, color, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        colorMap[color] || colorMap.slate,
        className
      )}
    >
      {label}
    </span>
  );
}
