"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RiskContributionItem } from "@/lib/types";

export default function RiskContribChart({
  data,
}: {
  data: RiskContributionItem[];
}) {
  const rows = data.map((d) => ({
    symbol: d.symbol,
    Peso: +(d.weight * 100).toFixed(1),
    "Riesgo aportado": +(d.risk_contribution * 100).toFixed(1),
  }));

  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
          <XAxis dataKey="symbol" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} unit="%" />
          <Tooltip formatter={(v: number) => `${v}%`} />
          <Legend />
          <Bar dataKey="Peso" fill="#c7d2fe" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Riesgo aportado" fill="#4f46e5" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
