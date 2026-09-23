"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { ProposedWeight } from "@/lib/types";
import { CHART_COLORS, fmtPct } from "@/lib/format";

export default function WeightsPie({ weights }: { weights: ProposedWeight[] }) {
  const data = weights.map((w) => ({ name: w.symbol, value: w.weight }));
  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={100}
            innerRadius={55}
            paddingAngle={2}
            label={(e: any) => `${e.name} ${(e.value * 100).toFixed(0)}%`}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(v: number) => fmtPct(v)} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
