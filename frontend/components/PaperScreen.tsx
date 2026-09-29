"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  getCatalog,
  getPaper,
  getPaperHistory,
  paperBuy,
  paperBuyPortfolio,
  paperReset,
  paperSell,
  searchMarket,
} from "@/lib/api";
import type {
  MarketCatalog,
  PaperHistory,
  PaperSnapshot,
  ProposedWeight,
  SearchResult,
} from "@/lib/types";
import { fmtCurrency, fmtPct } from "@/lib/format";
import PaperHistoryChart from "@/components/PaperHistoryChart";

export default function PaperScreen({
  userId,
  userName,
  recommended,
  onBack,
}: {
  userId: string;
  userName: string;
  recommended?: ProposedWeight[];
  onBack: () => void;
}) {
  const [snap, setSnap] = useState<PaperSnapshot | null>(null);
  const [history, setHistory] = useState<PaperHistory | null>(null);
  const [catalog, setCatalog] = useState<MarketCatalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [selected, setSelected] = useState<{ symbol: string; name: string } | null>(null);
  const [amount, setAmount] = useState<number | "">(1000);
  const [searchQ, setSearchQ] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [activeCat, setActiveCat] = useState<string>("");
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    Promise.all([getPaper(userId), getCatalog()])
      .then(([s, c]) => {
        setSnap(s);
        setCatalog(c);
        setActiveCat(Object.keys(c.categorias)[0] ?? "");
        setLoading(false);
      })
      .catch((e) => {
        setError(String(e.message ?? e));
        setLoading(false);
      });
    getPaperHistory(userId).then(setHistory).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Búsqueda con debounce.
  useEffect(() => {
    if (searchQ.trim().length < 2) {
      setResults([]);
      return;
    }
    const t = setTimeout(() => {
      setSearching(true);
      searchMarket(searchQ)
        .then((r) => { setResults(r); setSearching(false); })
        .catch(() => setSearching(false));
    }, 400);
    return () => clearTimeout(t);
  }, [searchQ]);

  async function run(fn: () => Promise<PaperSnapshot>, msg: string) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const s = await fn();
      setSnap(s);
      setNotice(msg);
      getPaperHistory(userId).then(setHistory).catch(() => {});
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setBusy(false);
    }
  }

  const cur = snap?.base_currency ?? "USD";
  const amt = amount === "" ? 0 : Number(amount);

  function doBuy() {
    if (!selected || amt <= 0) return;
    run(() => paperBuy(userId, selected.symbol, amt), `Compraste ${fmtCurrency(amt, cur)} de ${selected.symbol}.`);
  }
  function doSellAll(symbol: string) {
    run(() => paperSell(userId, symbol, { all: true }), `Vendiste todo tu ${symbol}.`);
  }
  function doBuyRecommended() {
    if (!recommended?.length) return;
    const allocations = recommended.map((w) => ({ symbol: w.symbol, weight: w.weight }));
    run(() => paperBuyPortfolio(userId, allocations, amt > 0 ? amt : undefined),
      "Compraste tu cartera recomendada.");
  }
  function doBuyBasket(tickers: string[], name: string) {
    const allocations = tickers.map((t) => ({ symbol: t, weight: 1 }));
    run(() => paperBuyPortfolio(userId, allocations, amt > 0 ? amt : undefined),
      `Compraste la cartera «${name}».`);
  }
  function doReset() {
    run(() => paperReset(userId), "Reiniciaste tu juego a " + fmtCurrency(100000, cur) + ".");
  }

  const returnClass = useMemo(
    () => (snap && snap.total_return >= 0 ? "pos" : "neg"),
    [snap]
  );

  if (loading) return <div className="container"><div className="card placeholder">Cargando tu juego…</div></div>;
  if (!snap) return <div className="container"><div className="card"><div className="alert">{error ?? "Error"}</div></div></div>;

  return (
    <div className="container rs">
      <div className="rs-head">
        <h1>Modo práctica — {userName}</h1>
        <div style={{ display: "flex", gap: 12 }}>
          <button className="linkbtn" onClick={doReset} disabled={busy}>Reiniciar</button>
          <button className="linkbtn" onClick={onBack}>Volver</button>
        </div>
      </div>

      <div className="card">
        <p className="sub" style={{ marginTop: 0 }}>
          Plata ficticia para practicar. Precios reales diferidos (~15 min). No es dinero real.
        </p>
        <div className="stat-row">
          <div className="stat"><div className="k">Valor total</div><div className="v big">{fmtCurrency(snap.total_value, cur)}</div></div>
          <div className="stat"><div className="k">Rendimiento</div><div className={`v ${returnClass}`}>{fmtPct(snap.total_return, 2)}</div></div>
          <div className="stat"><div className="k">Efectivo disponible</div><div className="v">{fmtCurrency(snap.cash, cur)}</div></div>
          <div className="stat"><div className="k">Invertido (valor)</div><div className="v">{fmtCurrency(snap.positions_value, cur)}</div></div>
        </div>
        {notice ? <div className="rs-lever" style={{ background: "#ecfdf5", borderColor: "#6ee7b7", color: "#065f46", marginTop: 14, marginBottom: 0 }}>{notice}</div> : null}
        {error ? <div className="alert" style={{ marginTop: 14 }}>{error}</div> : null}
      </div>

      {/* Evolución */}
      {history ? (
        <div className="card">
          <h2>Evolución de tu inversión</h2>
          <p className="sub" style={{ marginBottom: 12 }}>
            Cómo se mueve el valor total de tu cartera de práctica en el tiempo.
          </p>
          <PaperHistoryChart history={history} />
        </div>
      ) : null}

      {/* Tenencias */}
      <div className="card">
        <h2>Tus tenencias</h2>
        {snap.positions.length === 0 ? (
          <p className="sub">Todavía no invertiste. Buscá algo abajo y comprá.</p>
        ) : (
          <table>
            <thead><tr><th>Activo</th><th className="num">Cantidad</th><th className="num">Precio</th><th className="num">Valor</th><th className="num">Ganancia/pérdida</th><th></th></tr></thead>
            <tbody>
              {snap.positions.map((p) => (
                <tr key={p.symbol}>
                  <td><strong>{p.symbol}</strong></td>
                  <td className="num">{p.quantity.toLocaleString("es-AR", { maximumFractionDigits: 4 })}</td>
                  <td className="num">{p.price != null ? fmtCurrency(p.price, cur) : "—"}</td>
                  <td className="num">{fmtCurrency(p.market_value, cur)}</td>
                  <td className={`num ${p.pnl >= 0 ? "pos" : "neg"}`}>
                    {p.pnl >= 0 ? "+" : ""}{fmtCurrency(p.pnl, cur)} ({fmtPct(p.pnl_pct, 1)})
                  </td>
                  <td><button className="linkbtn" onClick={() => doSellAll(p.symbol)} disabled={busy}>Vender</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Comprar */}
      <div className="card">
        <h2>Comprar</h2>
        <label>Monto a invertir</label>
        <div className="q-money" style={{ maxWidth: 260 }}>
          <span className="q-cur">{cur}</span>
          <input type="number" min={0} value={amount}
            onChange={(e) => setAmount(e.target.value === "" ? "" : +e.target.value)} />
        </div>

        <div className="section-title">Buscar cualquier activo (acción, cripto, bono, ETF…)</div>
        <input placeholder="Ej: apple, bitcoin, tesla, TLT…" value={searchQ}
          onChange={(e) => setSearchQ(e.target.value)} />
        {searching ? <div className="notes">Buscando…</div> : null}
        {results.length > 0 ? (
          <div className="search-results">
            {results.map((r) => (
              <button key={r.symbol} className={`q-option ${selected?.symbol === r.symbol ? "selected" : ""}`}
                onClick={() => setSelected({ symbol: r.symbol, name: r.name })}>
                <strong>{r.symbol}</strong> — {r.name} <span className="pill">{r.type}</span>
              </button>
            ))}
          </div>
        ) : null}

        <div className="section-title">O elegí de una categoría</div>
        {catalog ? (
          <>
            <div className="tabs">
              {Object.keys(catalog.categorias).map((cat) => (
                <div key={cat} className={`tab ${activeCat === cat ? "active" : ""}`} onClick={() => setActiveCat(cat)}>{cat}</div>
              ))}
            </div>
            <div className="chips">
              {(catalog.categorias[activeCat] ?? []).map((it) => (
                <button key={it.symbol} className={`chip ${selected?.symbol === it.symbol ? "selected" : ""}`}
                  onClick={() => setSelected({ symbol: it.symbol, name: it.name })}>
                  {it.symbol} · {it.name}
                </button>
              ))}
            </div>
          </>
        ) : null}

        <div className="buy-bar">
          <div>{selected ? <>Elegido: <strong>{selected.symbol}</strong> — {selected.name}</> : <span className="sub">Elegí un activo arriba</span>}</div>
          <button className="btn" style={{ width: "auto", marginTop: 0 }} disabled={!selected || amt <= 0 || busy} onClick={doBuy}>
            {busy ? <span className="spinner" /> : "Comprar"}
          </button>
        </div>
      </div>

      {/* Carteras armadas */}
      <div className="card">
        <h2>Comprar una cartera armada</h2>
        <p className="sub">Invierte el monto de arriba repartido en varios activos de una.</p>
        {recommended?.length ? (
          <div className="basket">
            <div><strong>Mi cartera recomendada</strong> <span className="sub">({recommended.map((w) => w.symbol).join(", ")})</span></div>
            <button className="btn-secondary" disabled={busy} onClick={doBuyRecommended}>Comprar</button>
          </div>
        ) : null}
        {catalog?.carteras.map((c) => (
          <div className="basket" key={c.id}>
            <div><strong>{c.name}</strong> <span className="sub">({c.tickers.join(", ")})</span></div>
            <button className="btn-secondary" disabled={busy} onClick={() => doBuyBasket(c.tickers, c.name)}>Comprar</button>
          </div>
        ))}
      </div>

      {/* Historial */}
      <div className="card">
        <h2>Historial de operaciones</h2>
        {snap.transactions.length === 0 ? (
          <p className="sub">Sin operaciones todavía.</p>
        ) : (
          <table>
            <thead><tr><th>Fecha</th><th>Op.</th><th>Activo</th><th className="num">Cantidad</th><th className="num">Precio</th><th className="num">Monto</th></tr></thead>
            <tbody>
              {snap.transactions.map((t, i) => (
                <tr key={i}>
                  <td>{new Date(t.created_at).toLocaleString("es-AR")}</td>
                  <td><span className={t.side === "buy" ? "pos" : "neg"}>{t.side === "buy" ? "Compra" : "Venta"}</span></td>
                  <td>{t.symbol}</td>
                  <td className="num">{t.quantity.toLocaleString("es-AR", { maximumFractionDigits: 4 })}</td>
                  <td className="num">{fmtCurrency(t.price, cur)}</td>
                  <td className="num">{fmtCurrency(t.amount, cur)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
