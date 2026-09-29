"use client";

import {
  Area,
  ComposedChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import type { PaperHistory } from "@/lib/types";
import { fmtCurrency } from "@/lib/format";

export default function PaperHistoryChart({ history }: { history: PaperHistory }) {
  const cur = history.base_currency;
  if (history.points.length < 2) {
    return (
      <p className="sub">
        Todavía no hay suficiente historia para el gráfico. A medida que pasen los días
        (y se muevan los precios) vas a ver acá cómo evoluciona tu inversión.
      </p>
    );
  }
  const data = history.points.map((p) => ({
    date: p.date.slice(5), // MM-DD
    value: p.value,
  }));
  const last = history.points[history.points.length - 1].value;
  const up = last >= history.initial_cash;
  const color = up ? "#059669" : "#dc2626";

  return (
    <div className="chart-box" style={{ height: 300 }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 16, bottom: 10, left: 6 }}>
          <defs>
            <linearGradient id="pv" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.25} />
              <stop offset="100%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} minTickGap={24} />
          <YAxis
            tick={{ fontSize: 12 }}
            domain={["auto", "auto"]}
            tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
            width={44}
          />
          <Tooltip
            formatter={(v: number) => [fmtCurrency(v, cur), "Valor"]}
            labelFormatter={(l) => `Día ${l}`}
          />
          <ReferenceLine
            y={history.initial_cash}
            stroke="#94a3b8"
            strokeDasharray="5 4"
            label={{ value: "Inicio", fontSize: 11, fill: "#94a3b8", position: "insideBottomRight" }}
          />
          <Area dataKey="value" stroke={color} strokeWidth={2.5} fill="url(#pv)" dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
