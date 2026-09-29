"use client";

import { useEffect, useState } from "react";
import { getArgentinaMarket } from "@/lib/api";
import type { ArgentinaMarket } from "@/lib/types";

export default function ArgentinaPanel() {
  const [data, setData] = useState<ArgentinaMarket | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    getArgentinaMarket()
      .then((d) => { if (alive) { setData(d); setLoading(false); } })
      .catch(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  if (loading) return <div className="notes">Cargando referencias del mercado argentino…</div>;
  if (!data || (data.dollars.length === 0 && !data.merval)) return null;

  return (
    <div className="arg-panel">
      <div className="arg-dollars">
        {data.dollars.map((r) => (
          <div className="arg-rate" key={r.name}>
            <div className="arg-rate-name">Dólar {r.name}</div>
            <div className="arg-rate-val">${r.sell?.toLocaleString("es-AR") ?? "—"}</div>
          </div>
        ))}
        {data.merval?.price != null ? (
          <div className="arg-rate">
            <div className="arg-rate-name">Merval (puntos)</div>
            <div className="arg-rate-val">{data.merval.price.toLocaleString("es-AR", { maximumFractionDigits: 0 })}</div>
          </div>
        ) : null}
      </div>
      <div className="arg-note">{data.note} · Fuente: {data.source}</div>
    </div>
  );
}
