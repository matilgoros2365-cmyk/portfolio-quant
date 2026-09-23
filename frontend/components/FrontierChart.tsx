"use client";

import {
  CartesianGrid,
  Scatter,
  ScatterChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { FrontierPoint, OptimizedPortfolio } from "@/lib/types";

export default function FrontierChart({
  frontier,
  recommended,
}: {
  frontier: FrontierPoint[];
  recommended: OptimizedPortfolio;
}) {
  const line = frontier.map((p) => ({
    x: p.volatility * 100,
    y: p.expected_return * 100,
  }));
  const point = [
    {
      x: recommended.volatility * 100,
      y: recommended.expected_return * 100,
    },
  ];

  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
          <XAxis
            type="number"
            dataKey="x"
            name="Volatilidad"
            domain={["auto", "auto"]}
            tickFormatter={(v: number) => `${v.toFixed(1)}%`}
            label={{ value: "Riesgo (volatilidad anual)", position: "bottom", offset: 12, fontSize: 12 }}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Retorno"
            width={52}
            domain={["auto", "auto"]}
            tickFormatter={(v: number) => `${v.toFixed(1)}%`}
            tick={{ fontSize: 12 }}
          />
          <ZAxis range={[60, 61]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            formatter={(v: number) => `${v.toFixed(2)}%`}
          />
          <Scatter name="Frontera eficiente" data={line} fill="#c7d2fe" line shape="circle" />
          <Scatter name="Tu cartera" data={point} fill="#4f46e5" shape="star" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
