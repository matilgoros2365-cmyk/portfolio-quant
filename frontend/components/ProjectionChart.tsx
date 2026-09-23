"use client";

import {
  Area,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import type { YearBand } from "@/lib/types";
import { fmtCurrency } from "@/lib/format";

export default function ProjectionChart({
  bands,
  target,
  currency,
}: {
  bands: YearBand[];
  target: number | null;
  currency: string;
}) {
  // Para dibujar la banda p5-p95 usamos un área apilada: base (p5) invisible
  // + rango (p95 - p5) coloreado.
  const data = bands.map((b) => ({
    year: b.year,
    base: b.p5,
    range: b.p95 - b.p5,
    p50: b.p50,
  }));

  return (
    <div className="chart-box" style={{ height: 340 }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 12 }}
            label={{ value: "Año", position: "bottom", offset: 0, fontSize: 12 }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
          />
          <Tooltip
            formatter={(v: number, name: string) => [
              fmtCurrency(v, currency),
              name === "p50" ? "Mediana" : name,
            ]}
            labelFormatter={(l) => `Año ${l}`}
          />
          <Area
            dataKey="base"
            stackId="band"
            stroke="none"
            fill="transparent"
            isAnimationActive={false}
          />
          <Area
            dataKey="range"
            stackId="band"
            stroke="none"
            fill="#c7d2fe"
            fillOpacity={0.6}
            name="Rango p5–p95"
            isAnimationActive={false}
          />
          <Line
            dataKey="p50"
            stroke="#4f46e5"
            strokeWidth={2.5}
            dot={false}
            name="p50"
          />
          {target ? (
            <ReferenceLine
              y={target}
              stroke="#059669"
              strokeDasharray="6 4"
              label={{ value: `Meta: ${fmtCurrency(target, currency)}`, fontSize: 12, fill: "#059669", position: "insideTopRight" }}
            />
          ) : null}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
