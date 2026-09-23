"use client";

import { useState } from "react";
import { analyzeRisk, optimize, simulate } from "@/lib/api";
import type {
  FormInputs,
  OptimizeResponse,
  RiskProfile,
  RiskResponse,
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

type Results = {
  optimize: OptimizeResponse;
  risk: RiskResponse;
  simulate: SimulateResponse;
};

export default function Home() {
  const [capital, setCapital] = useState(50000);
  const [monthly, setMonthly] = useState(1000);
  const [horizon, setHorizon] = useState(10);
  const [currency, setCurrency] = useState("USD");
  const [risk, setRisk] = useState<RiskProfile>("MODERATE");
  const [target, setTarget] = useState<number | "">(250000);
  const [universe, setUniverse] = useState("VOO, QQQ, TLT, GLD");
  const [maxWeight, setMaxWeight] = useState<number | "">(40);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<Results | null>(null);
  const [tab, setTab] = useState<"cartera" | "riesgo" | "proyeccion">("cartera");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const inputs: FormInputs = {
      initial_capital: capital,
      monthly_contribution: monthly,
      investment_horizon_years: horizon,
      base_currency: currency,
      risk_profile: risk,
      target_wealth: target === "" ? null : Number(target),
      custom_asset_universe: universe
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean),
      max_weight: maxWeight === "" ? null : Number(maxWeight) / 100,
    };
    try {
      const [o, r, s] = await Promise.all([
        optimize(inputs),
        analyzeRisk(inputs),
        simulate(inputs),
      ]);
      setResults({ optimize: o, risk: r, simulate: s });
      setTab("cartera");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="app-header">
        <div className="wrap">
          <h1>PortfolioQuant Engine</h1>
          <p>
            Cargá tus supuestos mínimos y el sistema te recomienda una cartera,
            la analiza y proyecta su futuro. La compra la hacés vos aparte.
          </p>
        </div>
      </header>

      <div className="container grid grid-form">
        {/* ---------------- Formulario ---------------- */}
        <form className="card" onSubmit={handleSubmit}>
          <h2>Tus datos</h2>
          <p className="sub">Solo lo esencial. El resto lo calcula el sistema.</p>

          <label>Capital inicial</label>
          <input type="number" value={capital} min={0}
            onChange={(e) => setCapital(+e.target.value)} />

          <label>Aporte mensual</label>
          <input type="number" value={monthly} min={0}
            onChange={(e) => setMonthly(+e.target.value)} />

          <label>Horizonte (años)</label>
          <input type="number" value={horizon} min={1} max={60}
            onChange={(e) => setHorizon(+e.target.value)} />

          <label>Moneda base</label>
          <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
          </select>

          <label>Perfil de riesgo</label>
          <select value={risk} onChange={(e) => setRisk(e.target.value as RiskProfile)}>
            {RISK_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
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

          <button className="btn" type="submit" disabled={loading}>
            {loading ? (<><span className="spinner" />Analizando…</>) : "Analizar y recomendar"}
          </button>
          {error ? <div className="alert" style={{ marginTop: 14 }}>{error}</div> : null}
        </form>

        {/* ---------------- Resultados ---------------- */}
        <div>
          {!results ? (
            <div className="card placeholder">
              {loading
                ? "Descargando datos de mercado y calculando… (la primera vez tarda un poco)"
                : "Completá tus datos y presioná “Analizar y recomendar” para ver la cartera, su riesgo y la proyección."}
            </div>
          ) : (
            <>
              <div className="tabs">
                <div className={`tab ${tab === "cartera" ? "active" : ""}`} onClick={() => setTab("cartera")}>Cartera recomendada</div>
                <div className={`tab ${tab === "riesgo" ? "active" : ""}`} onClick={() => setTab("riesgo")}>Riesgo</div>
                <div className={`tab ${tab === "proyeccion" ? "active" : ""}`} onClick={() => setTab("proyeccion")}>Proyección</div>
              </div>

              {tab === "cartera" && <CarteraTab data={results.optimize} currency={currency} />}
              {tab === "riesgo" && <RiesgoTab data={results.risk} />}
              {tab === "proyeccion" && (
                <ProyeccionTab data={results.simulate} target={target === "" ? null : Number(target)} currency={currency} />
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

/* ============================ TABS ============================ */

function CarteraTab({ data, currency }: { data: OptimizeResponse; currency: string }) {
  const rec = data.recommended;
  return (
    <div className="card">
      <h2>Cartera recomendada para tu perfil</h2>
      <p className="sub">
        Tasa libre de riesgo usada: {fmtPct(data.risk_free_rate)} · Datos al {data.as_of ?? "—"}
      </p>

      <div className="stat-row">
        <div className="stat"><div className="k">Retorno esperado</div><div className="v accent">{fmtPct(rec.expected_return)}</div></div>
        <div className="stat"><div className="k">Volatilidad</div><div className="v">{fmtPct(rec.volatility)}</div></div>
        <div className="stat"><div className="k">Sharpe</div><div className="v">{fmtNum(rec.sharpe_ratio)}</div></div>
      </div>

      <div className="section-title">Composición</div>
      <WeightsPie weights={rec.weights} />

      <div className="section-title">Frontera eficiente (tu cartera es la estrella)</div>
      <FrontierChart frontier={data.efficient_frontier} recommended={rec} />

      <div className="section-title">Estrategias de referencia</div>
      <table>
        <thead>
          <tr><th>Estrategia</th><th className="num">Retorno</th><th className="num">Volatilidad</th><th className="num">Sharpe</th></tr>
        </thead>
        <tbody>
          {Object.entries(data.reference_portfolios).map(([k, p]) => (
            <tr key={k}>
              <td>{labelStrategy(k)}</td>
              <td className="num">{fmtPct(p.expected_return)}</td>
              <td className="num">{fmtPct(p.volatility)}</td>
              <td className="num">{fmtNum(p.sharpe_ratio)}</td>
            </tr>
          ))}
        </tbody>
      </table>

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
          <table>
            <thead><tr><th>Par</th><th className="num">En común</th></tr></thead>
            <tbody>
              {data.etf_overlap.map((o, i) => (
                <tr key={i}><td>{o.symbol_a} ↔ {o.symbol_b}</td><td className="num">{fmtPct(o.weight_overlap, 1)}</td></tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {data.lookthrough_top.length > 0 && (
        <>
          <div className="section-title">
            Exposición real a acciones (look-through){" "}
            <span className="pill warn">cobertura {fmtPct(data.lookthrough_coverage, 0)}</span>
          </div>
          <table>
            <thead><tr><th>Símbolo</th><th>Nombre</th><th className="num">Exposición</th></tr></thead>
            <tbody>
              {data.lookthrough_top.filter((e) => e.symbol !== "_no_cubierto").slice(0, 8).map((e, i) => (
                <tr key={i}><td>{e.symbol}</td><td>{e.name ?? "—"}</td><td className="num">{fmtPct(e.exposure, 2)}</td></tr>
              ))}
            </tbody>
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
        {data.n_simulations.toLocaleString("es-AR")} simulaciones de Monte Carlo · aportado en total: {fmtCurrency(data.total_contributed, currency)}
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
          <table>
            <thead><tr><th>Crisis</th><th className="num">Impacto en tu cartera</th></tr></thead>
            <tbody>
              {data.historical_scenarios.map((s, i) => (
                <tr key={i}>
                  <td>{s.name}</td>
                  <td className="num neg">{fmtPct(s.portfolio_return, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <ul className="notes">{data.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
    </div>
  );
}

function labelStrategy(k: string): string {
  const map: Record<string, string> = {
    min_variance: "Mínima varianza",
    max_sharpe: "Máximo Sharpe",
    risk_parity: "Paridad de riesgo",
  };
  return map[k] ?? k;
}
