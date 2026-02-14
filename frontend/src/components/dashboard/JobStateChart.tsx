"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { CHART_COLORS } from "@/lib/constants";

interface JobStateChartProps {
  byState: Record<string, number>;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0];
  return (
    <div
      style={{
        backgroundColor: "#0f172a",
        border: "1px solid #475569",
        borderRadius: "8px",
        padding: "8px 12px",
        boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
      }}
    >
      <p style={{ color: "#e2e8f0", fontSize: "13px", margin: 0, fontWeight: 500 }}>
        <span
          style={{
            display: "inline-block",
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: CHART_COLORS[name] || "#64748b",
            marginRight: 8,
          }}
        />
        {name}: <strong>{value}</strong>
      </p>
    </div>
  );
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
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(148, 163, 184, 0.1)" }} />
        <Legend
          formatter={(value) => <span className="text-sm text-slate-300">{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

