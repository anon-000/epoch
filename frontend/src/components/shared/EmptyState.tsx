"use client";

import { InboxIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title?: string;
  message?: string;
  className?: string;
}

export function EmptyState({
  title = "No data",
  message = "Nothing to display yet.",
  className,
}: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-16 text-slate-400", className)}>
      <InboxIcon className="mb-4 h-12 w-12 text-slate-600" />
      <p className="text-lg font-medium text-slate-300">{title}</p>
      <p className="mt-1 text-sm">{message}</p>
    </div>
  );
}
