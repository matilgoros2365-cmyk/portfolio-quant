"use client";

import { useEffect, useState } from "react";
import { getAssetDetail } from "@/lib/api";
import type { AssetDetail, ProposedWeight } from "@/lib/types";
import { fmtPct } from "@/lib/format";

export default function PortfolioComposition({ weights }: { weights: ProposedWeight[] }) {
  const [details, setDetails] = useState<Record<string, AssetDetail>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    Promise.all(
      weights.map((w) => getAssetDetail(w.symbol).then((d) => [w.symbol, d] as const).catch(() => null))
    ).then((pairs) => {
      if (!alive) return;
      const map: Record<string, AssetDetail> = {};
      for (const p of pairs) if (p) map[p[0]] = p[1];
      setDetails(map);
      setLoading(false);
    });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) return <div className="notes"><span className="spinner" style={{ borderColor: "#c7d2fe", borderTopColor: "#4f46e5" }} /> Buscando qué hay adentro y los precios…</div>;

  return (
    <div className="comp-list">
      {weights.map((w) => {
        const d = details[w.symbol];
        const c = d?.composition;
        const q = d?.quote;
        const change = q?.change_pct ?? null;
        return (
          <div className="comp-card" key={w.symbol}>
            <div className="comp-head">
              <div>
                <span className="comp-sym">{w.symbol}</span>
                <span className="comp-name">{c?.name ?? w.name ?? ""}</span>
              </div>
              <div className="comp-right">
                <div className="comp-weight">{fmtPct(w.weight, 0)} de tu cartera</div>
                {q?.price != null ? (
                  <div className="comp-price">
                    {q.currency === "USD" ? "US$" : q.currency + " "}{q.price.toLocaleString("es-AR", { maximumFractionDigits: 2 })}
                    {change != null ? <span className={change >= 0 ? "pos" : "neg"}> {change >= 0 ? "▲" : "▼"} {fmtPct(Math.abs(change), 2)}</span> : null}
                  </div>
                ) : null}
              </div>
            </div>

            {/* Rubro */}
            {c?.category || c?.sector ? (
              <div className="comp-rubro">
                {c?.category ? `Categoría: ${c.category}. ` : ""}
                {c?.sector ? `Sector: ${c.sector}${c.industry ? " · " + c.industry : ""}.` : ""}
              </div>
            ) : null}

            {/* Sectores (ETF) */}
            {c && c.sector_weights.length > 0 ? (
              <div className="comp-sectors">
                {c.sector_weights.slice(0, 4).map((s) => (
                  <span key={s.sector} className="comp-tag">{s.sector} {fmtPct(s.weight, 0)}</span>
                ))}
              </div>
            ) : null}

            {/* Empresas (ETF) */}
            {c && c.top_holdings.length > 0 ? (
              <div className="comp-holdings">
                <span className="comp-holdings-t">Principales empresas:</span>{" "}
                {c.top_holdings.slice(0, 6).map((h) => `${h.name ?? h.symbol} (${fmtPct(h.weight, 1)})`).join(" · ")}
              </div>
            ) : null}

            {/* Descripción (acción individual) */}
            {c && c.top_holdings.length === 0 && c.summary ? (
              <div className="comp-summary">{c.summary}…</div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
