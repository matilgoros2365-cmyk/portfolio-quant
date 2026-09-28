"use client";

import { useEffect, useState } from "react";
import {
  analyzeFactors,
  analyzeRisk,
  analyzeRobustness,
  getAnalysis,
  listAnalyses,
  optimize,
  simulate,
} from "@/lib/api";
import type {
  AnalysisDetail,
  AnalysisSummary,
  FactorResponse,
  FormInputs,
  OptimizedPortfolio,
  OptimizeResponse,
  RiskProfile,
  RiskResponse,
  RobustnessResponse,
  SimulateResponse,
} from "@/lib/types";
import { fmtCurrency, fmtNum, fmtPct } from "@/lib/format";
import WeightsPie from "@/components/WeightsPie";
import FrontierChart from "@/components/FrontierChart";
import ProjectionChart from "@/components/ProjectionChart";
import RiskContribChart from "@/components/RiskContribChart";

const RISK_OPTIONS: { value: RiskProfile; label: string }[] = [
  { value: "VERY_CONSERVATIVE", label: "Muy conservador" },
  { value: "CONSERVATIVE", label: "Conservador" },
  { value: "MODERATE", label: "Moderado" },
  { value: "AGGRESSIVE", label: "Agresivo" },
  { value: "VERY_AGGRESSIVE", label: "Muy agresivo" },
];

type Results = { optimize: OptimizeResponse; risk: RiskResponse; simulate: SimulateResponse };
type TabId = "cartera" | "riesgo" | "proyeccion" | "factores" | "robustez" | "historial";
type Async<T> = { data: T | null; loading: boolean; error: string | null };

const emptyAsync = <T,>(): Async<T> => ({ data: null, loading: false, error: null });

export default function Home() {
  const [capital, setCapital] = useState(50000);
  const [monthly, setMonthly] = useState(1000);
  const [horizon, setHorizon] = useState(10);
  const [currency, setCurrency] = useState("USD");
  const [risk, setRisk] = useState<RiskProfile>("MODERATE");
  const [target, setTarget] = useState<number | "">(250000);
  const [universe, setUniverse] = useState("VOO, QQQ, TLT, GLD");
  const [maxWeight, setMaxWeight] = useState<number | "">(40);
  const [method, setMethod] = useState<FormInputs["method"]>("gaussian");
  const [nSims, setNSims] = useState(50000);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<Results | null>(null);
  const [inputs, setInputs] = useState<FormInputs | null>(null);
  const [tab, setTab] = useState<TabId>("cartera");

  // Pestañas avanzadas (carga perezosa).
  const [factors, setFactors] = useState<Async<FactorResponse>>(emptyAsync());
  const [robust, setRobust] = useState<Async<RobustnessResponse>>(emptyAsync());
  const [history, setHistory] = useState<Async<AnalysisSummary[]>>(emptyAsync());

  function buildInputs(): FormInputs {
    return {
      initial_capital: capital,
      monthly_contribution: monthly,
      investment_horizon_years: horizon,
      base_currency: currency,
      risk_profile: risk,
      target_wealth: target === "" ? null : Number(target),
      custom_asset_universe: universe.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean),
      max_weight: maxWeight === "" ? null : Number(maxWeight) / 100,
      method,
      n_simulations: nSims,
    };
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const inp = buildInputs();
    // Reiniciar pestañas avanzadas al recalcular.
    setFactors(emptyAsync());
    setRobust(emptyAsync());
    try {
      const [o, r, s] = await Promise.all([optimize(inp), analyzeRisk(inp), simulate(inp)]);
      setResults({ optimize: o, risk: r, simulate: s });
      setInputs(inp);
      setTab("cartera");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }

  // Carga perezosa de Factores / Robustez cuando se abre la pestaña.
  useEffect(() => {
    if (tab === "factores" && inputs && !factors.data && !factors.loading) {
      setFactors({ data: null, loading: true, error: null });
      analyzeFactors(inputs)
        .then((d) => setFactors({ data: d, loading: false, error: null }))
        .catch((e) => setFactors({ data: null, loading: false, error: String(e.message ?? e) }));
    }
    if (tab === "robustez" && inputs && !robust.data && !robust.loading) {
      setRobust({ data: null, loading: true, error: null });
      analyzeRobustness(inputs)
        .then((d) => setRobust({ data: d, loading: false, error: null }))
        .catch((e) => setRobust({ data: null, loading: false, error: String(e.message ?? e) }));
    }
    if (tab === "historial") {
      setHistory((h) => ({ ...h, loading: true, error: null }));
      listAnalyses(50)
        .then((d) => setHistory({ data: d, loading: false, error: null }))
        .catch((e) => setHistory({ data: null, loading: false, error: String(e.message ?? e) }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  return (
    <>
      <header className="app-header">
        <div className="wrap">
          <h1>PortfolioQuant Engine</h1>
          <p>
            Cargá tus supuestos mínimos y el sistema te recomienda una cartera (con
            alternativas), la analiza, la proyecta y guarda todos los cálculos.
          </p>
        </div>
      </header>

      <div className="container grid grid-form">
        <form className="card" onSubmit={handleSubmit}>
          <h2>Tus datos</h2>
          <p className="sub">Solo lo esencial. El resto lo calcula el sistema.</p>

          <label>Capital inicial</label>
          <input type="number" value={capital} min={0} onChange={(e) => setCapital(+e.target.value)} />
          <label>Aporte mensual</label>
          <input type="number" value={monthly} min={0} onChange={(e) => setMonthly(+e.target.value)} />
          <label>Horizonte (años)</label>
          <input type="number" value={horizon} min={1} max={60} onChange={(e) => setHorizon(+e.target.value)} />
          <label>Moneda base</label>
          <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
          </select>
          <label>Perfil de riesgo</label>
          <select value={risk} onChange={(e) => setRisk(e.target.value as RiskProfile)}>
            {RISK_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
          </select>
          <label>Objetivo de patrimonio (opcional)</label>
          <input type="number" value={target} min={0}
            onChange={(e) => setTarget(e.target.value === "" ? "" : +e.target.value)} />
          <label>Universo de activos</label>
          <input value={universe} onChange={(e) => setUniverse(e.target.value)} />
          <div className="hint">Símbolos separados por coma (ej: VOO, QQQ, TLT, GLD)</div>
          <label>Tope máximo por activo (%)</label>
          <input type="number" value={maxWeight} min={1} max={100}
            onChange={(e) => setMaxWeight(e.target.value === "" ? "" : +e.target.value)} />

          <label>Método de simulación</label>
          <select value={method} onChange={(e) => setMethod(e.target.value as FormInputs["method"])}>
            <option value="gaussian">Gaussiano (normal)</option>
            <option value="student_t">t-Student (colas gordas)</option>
            <option value="bootstrap">Bootstrap histórico</option>
          </select>
          <label>Nº de simulaciones</label>
          <select value={nSims} onChange={(e) => setNSims(+e.target.value)}>
            <option value={10000}>10.000 (rápido)</option>
            <option value={50000}>50.000 (recomendado)</option>
            <option value={100000}>100.000 (preciso)</option>
            <option value={200000}>200.000 (máxima precisión)</option>
          </select>

          <button className="btn" type="submit" disabled={loading}>
            {loading ? (<><span className="spinner" />Analizando…</>) : "Analizar y recomendar"}
          </button>
          {error ? <div className="alert" style={{ marginTop: 14 }}>{error}</div> : null}
        </form>

        <div>
          {!results ? (
            <div className="card placeholder">
              {loading
                ? "Descargando datos de mercado y calculando… (la primera vez tarda un poco)"
                : "Completá tus datos y presioná “Analizar y recomendar”."}
            </div>
          ) : (
            <>
              <div className="tabs">
                {([
                  ["cartera", "Cartera + alternativas"],
                  ["riesgo", "Riesgo"],
                  ["proyeccion", "Proyección"],
                  ["factores", "Factores"],
                  ["robustez", "Robustez"],
                  ["historial", "Historial"],
                ] as [TabId, string][]).map(([id, label]) => (
                  <div key={id} className={`tab ${tab === id ? "active" : ""}`} onClick={() => setTab(id)}>
                    {label}
                  </div>
                ))}
              </div>

              {tab === "cartera" && <CarteraTab data={results.optimize} currency={currency} />}
              {tab === "riesgo" && <RiesgoTab data={results.risk} />}
              {tab === "proyeccion" && (
                <ProyeccionTab data={results.simulate} target={target === "" ? null : Number(target)} currency={currency} />
              )}
              {tab === "factores" && <FactoresTab a={factors} />}
              {tab === "robustez" && <RobustezTab a={robust} />}
              {tab === "historial" && <HistorialTab a={history} />}
            </>
          )}
        </div>
      </div>
    </>
  );
}

/* ============================ TABS ============================ */

function pesosInline(p: OptimizedPortfolio): string {
  return p.weights.map((w) => `${w.symbol} ${(w.weight * 100).toFixed(0)}%`).join(" · ");
}

function CarteraTab({ data, currency }: { data: OptimizeResponse; currency: string }) {
  const rec = data.recommended;
  const alts = [
    ...data.alternatives,
    ...Object.entries(data.reference_portfolios).map(([k, p]) => ({ ...p, label: labelStrategy(k) })),
  ];
  const c = data.calculations;
  return (
    <div className="card">
      <h2>Cartera recomendada para tu perfil</h2>
      <p className="sub">
        Tasa libre de riesgo: {fmtPct(data.risk_free_rate)} · Datos al {data.as_of ?? "—"}
        {data.analysis_id ? ` · Guardada como análisis #${data.analysis_id}` : ""}
      </p>

      <div className="stat-row">
        <div className="stat"><div className="k">Retorno esperado</div><div className="v accent">{fmtPct(rec.expected_return)}</div></div>
        <div className="stat"><div className="k">Volatilidad</div><div className="v">{fmtPct(rec.volatility)}</div></div>
        <div className="stat"><div className="k">Sharpe</div><div className="v">{fmtNum(rec.sharpe_ratio)}</div></div>
      </div>

      <div className="section-title">Composición</div>
      <WeightsPie weights={rec.weights} />

      <div className="section-title">Alternativas para comparar</div>
      <table>
        <thead><tr><th>Cartera</th><th className="num">Retorno</th><th className="num">Vol</th><th className="num">Sharpe</th><th>Composición</th></tr></thead>
        <tbody>
          <tr style={{ background: "#eef2ff" }}>
            <td><strong>{rec.label}</strong></td>
            <td className="num">{fmtPct(rec.expected_return)}</td>
            <td className="num">{fmtPct(rec.volatility)}</td>
            <td className="num">{fmtNum(rec.sharpe_ratio)}</td>
            <td>{pesosInline(rec)}</td>
          </tr>
          {alts.map((p, i) => (
            <tr key={i}>
              <td>{p.label}</td>
              <td className="num">{fmtPct(p.expected_return)}</td>
              <td className="num">{fmtPct(p.volatility)}</td>
              <td className="num">{fmtNum(p.sharpe_ratio)}</td>
              <td>{pesosInline(p)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="section-title">Frontera eficiente (tu cartera es la estrella)</div>
      <FrontierChart frontier={data.efficient_frontier} recommended={rec} />

      {c ? (
        <details className="details">
          <summary>Ver fórmulas y cálculos (para revisar)</summary>
          <div className="section-title">Retorno esperado y volatilidad por activo (anualizados)</div>
          <table>
            <thead><tr><th>Activo</th><th className="num">Retorno esp.</th><th className="num">Volatilidad</th></tr></thead>
            <tbody>
              {c.symbols.map((s) => (
                <tr key={s}><td>{s}</td><td className="num">{fmtPct(c.expected_returns[s])}</td><td className="num">{fmtPct(c.volatilities[s])}</td></tr>
              ))}
            </tbody>
          </table>
          <div className="section-title">Matriz de correlación</div>
          <table>
            <thead><tr><th></th>{c.symbols.map((s) => <th key={s} className="num">{s}</th>)}</tr></thead>
            <tbody>
              {c.symbols.map((r) => (
                <tr key={r}>
                  <th>{r}</th>
                  {c.symbols.map((cc) => <td key={cc} className="num">{fmtNum(c.correlation_matrix[r]?.[cc], 2)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="section-title">Fórmulas usadas</div>
          <ul className="notes">
            {Object.entries(data.formulas).map(([k, f]) => (
              <li key={k}><strong>{k}:</strong> <code>{f.formula}</code> — {f.descripcion}</li>
            ))}
          </ul>
        </details>
      ) : null}

      <ul className="notes">{data.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
    </div>
  );
}

function RiesgoTab({ data }: { data: RiskResponse }) {
  const v = data.value_at_risk;
  return (
    <div className="card">
      <h2>Análisis de riesgo</h2>
      <p className="sub">Cuánto podrías perder y de dónde viene el riesgo.</p>
      <div className="stat-row">
        <div className="stat"><div className="k">Volatilidad anual</div><div className="v">{fmtPct(data.annualized_volatility)}</div></div>
        <div className="stat"><div className="k">VaR diario (95%)</div><div className="v neg">{fmtPct(v.var_historical)}</div></div>
        <div className="stat"><div className="k">CVaR diario (95%)</div><div className="v neg">{fmtPct(v.cvar_historical)}</div></div>
        <div className="stat"><div className="k">Nº efectivo de activos</div><div className="v">{fmtNum(data.concentration.effective_num_assets, 1)}</div></div>
      </div>
      <div className="section-title">Peso vs. riesgo aportado por activo</div>
      <RiskContribChart data={data.risk_contributions} />
      {data.etf_overlap.length > 0 && (
        <>
          <div className="section-title">Solapamiento entre ETFs</div>
          <table><thead><tr><th>Par</th><th className="num">En común</th></tr></thead>
            <tbody>{data.etf_overlap.map((o, i) => (<tr key={i}><td>{o.symbol_a} ↔ {o.symbol_b}</td><td className="num">{fmtPct(o.weight_overlap, 1)}</td></tr>))}</tbody>
          </table>
        </>
      )}
      {data.lookthrough_top.length > 0 && (
        <>
          <div className="section-title">Exposición real a acciones (look-through) <span className="pill warn">cobertura {fmtPct(data.lookthrough_coverage, 0)}</span></div>
          <table><thead><tr><th>Símbolo</th><th>Nombre</th><th className="num">Exposición</th></tr></thead>
            <tbody>{data.lookthrough_top.filter((e) => e.symbol !== "_no_cubierto").slice(0, 8).map((e, i) => (<tr key={i}><td>{e.symbol}</td><td>{e.name ?? "—"}</td><td className="num">{fmtPct(e.exposure, 2)}</td></tr>))}</tbody>
          </table>
        </>
      )}
      <ul className="notes">{data.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
    </div>
  );
}

function ProyeccionTab({ data, target, currency }: { data: SimulateResponse; target: number | null; currency: string }) {
  const t = data.terminal;
  return (
    <div className="card">
      <h2>Proyección a {data.horizon_years} años</h2>
      <p className="sub">
        {data.n_simulations.toLocaleString("es-AR")} simulaciones ({methodLabel(data.method)}) · aportado en total: {fmtCurrency(data.total_contributed, currency)}
        {data.analysis_id ? ` · Análisis #${data.analysis_id}` : ""}
      </p>
      {t.prob_reaching_target !== null && target ? (
        <div className="goal-banner">
          <div className="pct">{fmtPct(t.prob_reaching_target, 1)}</div>
          <div className="lbl">de probabilidad de llegar a {fmtCurrency(target, currency)}</div>
        </div>
      ) : null}
      <div className="section-title">Evolución del patrimonio (banda p5–p95, línea = mediana)</div>
      <ProjectionChart bands={data.yearly_bands} target={target} currency={currency} />
      <div className="section-title">Patrimonio final proyectado</div>
      <div className="stat-row">
        <div className="stat"><div className="k">Pesimista (p5)</div><div className="v">{fmtCurrency(t.p5, currency)}</div></div>
        <div className="stat"><div className="k">Típico (mediana)</div><div className="v big accent">{fmtCurrency(t.p50, currency)}</div></div>
        <div className="stat"><div className="k">Optimista (p95)</div><div className="v">{fmtCurrency(t.p95, currency)}</div></div>
      </div>
      {data.historical_scenarios.length > 0 && (
        <>
          <div className="section-title">Stress test: crisis históricas reales</div>
          <table><thead><tr><th>Crisis</th><th className="num">Impacto en tu cartera</th></tr></thead>
            <tbody>{data.historical_scenarios.map((s, i) => (<tr key={i}><td>{s.name}</td><td className="num neg">{fmtPct(s.portfolio_return, 1)}</td></tr>))}</tbody>
          </table>
        </>
      )}
      <ul className="notes">{data.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
    </div>
  );
}

function FactoresTab({ a }: { a: Async<FactorResponse> }) {
  if (a.loading) return <div className="card placeholder"><span className="spinner" style={{ borderTopColor: "#4f46e5", borderColor: "#c7d2fe", borderTopWidth: 2 }} /> Calculando factores (descarga ETFs de referencia)…</div>;
  if (a.error) return <div className="card"><div className="alert">{a.error}</div></div>;
  if (!a.data) return <div className="card placeholder">—</div>;
  const d = a.data;
  return (
    <div className="card">
      <h2>Análisis de factores</h2>
      <p className="sub">A qué está expuesta tu cartera y si genera valor extra (alfa).</p>
      <div className="stat-row">
        <div className="stat"><div className="k">Alfa anual</div><div className={`v ${(d.portfolio.alpha_annualized ?? 0) >= 0 ? "pos" : "neg"}`}>{fmtPct(d.portfolio.alpha_annualized)}</div></div>
        <div className="stat"><div className="k">R² (ajuste)</div><div className="v">{fmtPct(d.portfolio.r_squared, 0)}</div></div>
      </div>
      <div className="section-title">Exposición de la cartera a cada factor (beta)</div>
      <table>
        <thead><tr><th>Factor</th><th className="num">Beta</th><th className="num">t-stat</th><th>Qué mide</th></tr></thead>
        <tbody>
          {d.portfolio.exposures.map((e) => (
            <tr key={e.factor}><td><strong>{e.factor}</strong></td><td className="num">{fmtNum(e.beta)}</td><td className="num">{fmtNum(e.t_stat, 1)}</td><td style={{ fontSize: 12, color: "var(--muted)" }}>{d.factor_legend[e.factor]}</td></tr>
          ))}
        </tbody>
      </table>
      <div className="section-title">Beta de mercado por activo</div>
      <table>
        <thead><tr><th>Activo</th><th className="num">Beta MKT</th><th className="num">R²</th></tr></thead>
        <tbody>
          {d.assets.map((asset) => {
            const mkt = asset.exposures.find((x) => x.factor === "MKT");
            return <tr key={asset.symbol}><td>{asset.symbol}</td><td className="num">{fmtNum(mkt?.beta ?? null)}</td><td className="num">{fmtPct(asset.r_squared, 0)}</td></tr>;
          })}
        </tbody>
      </table>
      <ul className="notes">{d.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
    </div>
  );
}

function RobustezTab({ a }: { a: Async<RobustnessResponse> }) {
  if (a.loading) return <div className="card placeholder"><span className="spinner" style={{ borderTopColor: "#4f46e5", borderColor: "#c7d2fe", borderTopWidth: 2 }} /> Calculando robustez (200 re-optimizaciones)… puede tardar.</div>;
  if (a.error) return <div className="card"><div className="alert">{a.error}</div></div>;
  if (!a.data) return <div className="card placeholder">—</div>;
  const d = a.data;
  return (
    <div className="card">
      <h2>Robustez y estabilidad</h2>
      <p className="sub">Retornos históricos vs. Black-Litterman, y qué tan estables son los pesos.</p>
      <div className="stat-row">
        <div className="stat"><div className="k">Inestabilidad</div><div className="v">{fmtNum(d.instability, 3)}</div></div>
        <div className="stat"><div className="k">Aversión al riesgo (δ)</div><div className="v">{fmtNum(d.risk_aversion)}</div></div>
        <div className="stat"><div className="k">Remuestreos</div><div className="v">{d.n_resamples}</div></div>
      </div>
      <div className="section-title">Retorno esperado: histórico vs. Black-Litterman</div>
      <table>
        <thead><tr><th>Activo</th><th className="num">Histórico</th><th className="num">Black-Litterman</th></tr></thead>
        <tbody>{d.expected_returns.map((e) => (<tr key={e.symbol}><td>{e.symbol}</td><td className="num">{fmtPct(e.historical)}</td><td className="num">{fmtPct(e.black_litterman)}</td></tr>))}</tbody>
      </table>
      <div className="section-title">Estabilidad de los pesos (menor desvío = más robusto)</div>
      <table>
        <thead><tr><th>Activo</th><th className="num">Recomendado</th><th className="num">Promedio</th><th className="num">Desvío</th></tr></thead>
        <tbody>{d.stability.map((s) => (<tr key={s.symbol}><td>{s.symbol}</td><td className="num">{fmtPct(s.recommended_weight, 1)}</td><td className="num">{fmtPct(s.mean_weight, 1)}</td><td className="num">±{fmtPct(s.std_weight, 1)}</td></tr>))}</tbody>
      </table>
      <ul className="notes">{d.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
    </div>
  );
}

function HistorialTab({ a }: { a: Async<AnalysisSummary[]> }) {
  const [detail, setDetail] = useState<AnalysisDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  async function open(id: number) {
    setLoadingDetail(true);
    try {
      setDetail(await getAnalysis(id));
    } catch {
      setDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  }

  if (a.loading) return <div className="card placeholder">Cargando historial…</div>;
  if (a.error) return <div className="card"><div className="alert">{a.error}</div></div>;
  const rows = a.data ?? [];
  return (
    <div className="card">
      <h2>Historial de análisis</h2>
      <p className="sub">Todos los análisis quedan guardados con sus cálculos y fórmulas.</p>
      <table>
        <thead><tr><th>#</th><th>Tipo</th><th>Perfil</th><th>Fecha</th><th></th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{kindLabel(r.kind)}</td>
              <td>{r.risk_profile ?? "—"}</td>
              <td>{new Date(r.created_at).toLocaleString("es-AR")}</td>
              <td><button className="linkbtn" onClick={() => open(r.id)}>ver</button></td>
            </tr>
          ))}
          {rows.length === 0 ? <tr><td colSpan={5} style={{ color: "var(--muted)" }}>Todavía no hay análisis guardados.</td></tr> : null}
        </tbody>
      </table>
      {loadingDetail ? <div className="notes">Cargando detalle…</div> : null}
      {detail ? (
        <>
          <div className="section-title">Detalle del análisis #{detail.id} ({kindLabel(detail.kind)})</div>
          <div className="section-title" style={{ marginTop: 8 }}>Inputs</div>
          <pre className="codeblock">{JSON.stringify(detail.inputs, null, 2)}</pre>
          <div className="section-title">Resultado (cálculos y fórmulas incluidos)</div>
          <pre className="codeblock">{JSON.stringify(detail.result, null, 2)}</pre>
        </>
      ) : null}
    </div>
  );
}

/* ============================ helpers ============================ */
function labelStrategy(k: string): string {
  return { min_variance: "Mínima varianza", max_sharpe: "Máximo Sharpe", risk_parity: "Paridad de riesgo" }[k] ?? k;
}
function methodLabel(m: string): string {
  return { gaussian: "gaussiano", student_t: "t-Student", bootstrap: "bootstrap histórico" }[m] ?? m;
}
function kindLabel(k: string): string {
  return {
    optimize: "Cartera", risk: "Riesgo", simulate: "Proyección",
    factors: "Factores", robustness: "Robustez",
  }[k] ?? k;
}
