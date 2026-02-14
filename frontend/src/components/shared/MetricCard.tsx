"use client";

import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export function MetricCard({ title, value, subtitle, icon: Icon, className }: MetricCardProps) {
  return (
    <div className={cn("card flex items-start gap-4", className)}>
      <div className="rounded-lg bg-slate-700/50 p-3">
        <Icon className="h-5 w-5 text-blue-400" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm text-slate-400">{title}</p>
        <p className="mt-1 text-2xl font-semibold text-slate-100">{value}</p>
        {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
      </div>
    </div>
  );
}
