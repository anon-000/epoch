"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  offset: number;
  limit: number;
  total: number;
  onChange: (offset: number) => void;
}

export function Pagination({ offset, limit, total, onChange }: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="flex items-center justify-between border-t border-slate-700 px-2 pt-4">
      <span className="text-sm text-slate-400">
        {total > 0 ? `${offset + 1}–${Math.min(offset + limit, total)} of ${total}` : "No results"}
      </span>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onChange(Math.max(0, offset - limit))}
          disabled={offset === 0}
          className="btn-ghost px-2 py-1"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="text-sm text-slate-300">
          {currentPage} / {totalPages}
        </span>
        <button
          onClick={() => onChange(offset + limit)}
          disabled={offset + limit >= total}
          className="btn-ghost px-2 py-1"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
