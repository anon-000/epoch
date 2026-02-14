"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  Server,
  Users,
  AlertTriangle,
  Activity,
  ScrollText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "@/lib/constants";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";

const iconMap: Record<string, React.ElementType> = {
  LayoutDashboard,
  Briefcase,
  Server,
  Users,
  AlertTriangle,
  ScrollText,
};

export function Sidebar() {
  const pathname = usePathname();
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const res = await api.get<HealthResponse>("/admin/health");
        if (!cancelled) setHealthy(res.status === "ok");
      } catch {
        if (!cancelled) setHealthy(false);
      }
    };
    check();
    const id = setInterval(check, 10000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r border-slate-700 bg-slate-900">
      {/* Logo */}
      <div className="flex items-center gap-3 border-b border-slate-700 px-5 py-5">
        <Activity className="h-7 w-7 text-blue-500" />
        <span className="text-xl font-bold tracking-tight text-slate-100">Epoch</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map((item) => {
          const Icon = iconMap[item.icon] || LayoutDashboard;
          const active =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-slate-800 text-blue-400"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Health indicator */}
      <div className="border-t border-slate-700 px-5 py-4">
        <div className="flex items-center gap-2 text-sm">
          <div
            className={cn(
              "h-2 w-2 rounded-full",
              healthy === null
                ? "bg-slate-500"
                : healthy
                  ? "bg-emerald-500"
                  : "bg-red-500"
            )}
          />
          <span className="text-slate-400">
            {healthy === null ? "Checking..." : healthy ? "API Connected" : "API Offline"}
          </span>
        </div>
      </div>
    </aside>
  );
}
