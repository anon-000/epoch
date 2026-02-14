"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { CHART_COLORS } from "@/lib/constants";

interface JobStateChartProps {
  byState: Record<string, number>;
}

export function JobStateChart({ byState }: JobStateChartProps) {
  const data = Object.entries(byState)
    .filter(([, count]) => count > 0)
    .map(([state, count]) => ({ name: state, value: count }));

  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500">
        No job data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={CHART_COLORS[entry.name] || "#64748b"} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "#0f172a",
            border: "1px solid #334155",
            borderRadius: "8px",
            color: "#e2e8f0",
            boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
          }}
          itemStyle={{ color: "#e2e8f0" }}
          labelStyle={{ color: "#94a3b8", fontWeight: 600, marginBottom: 4 }}
          cursor={{ fill: "rgba(148, 163, 184, 0.1)" }}
        />
        <Legend
          formatter={(value) => <span className="text-sm text-slate-300">{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
