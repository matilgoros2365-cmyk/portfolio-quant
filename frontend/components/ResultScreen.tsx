"use client";

import type { AssessmentResult, Recommendation } from "@/lib/types";
import { fmtCurrency, fmtNum, fmtPct } from "@/lib/format";
import WeightsPie from "@/components/WeightsPie";
import PortfolioComposition from "@/components/PortfolioComposition";
import ArgentinaPanel from "@/components/ArgentinaPanel";

const GOAL: Record<string, string> = {
  grow: "hacer crecer tus ahorros",
  big_purchase: "ahorrar para una compra importante",
  house: "comprar una casa",
  retirement: "prepararte para tu jubilación",
  income: "generar ingresos a futuro",
  no_goal: "hacer crecer tu dinero",
  other: "tu objetivo",
};

function horizonPhrase(q3: string): string {
  if (q3 === "gt_10" || q3 === "y5_10" || q3 === "no_date") return "no esperás necesitar este dinero pronto";
  if (q3 === "y3_5") return "podrías necesitarlo en unos años";
  return "podrías necesitarlo pronto";
}

function buildSummary(a: AssessmentResult): string[] {
  const ans = a.answers;
  const p = a.profile;
  const s: string[] = [];
  s.push(`Querés ${GOAL[ans.Q1] ?? "hacer crecer tu dinero"} y ${horizonPhrase(ans.Q3)}.`);
  if (ans.Q5 === "several_months") s.push("Además, contás con dinero separado para imprevistos, lo que te da margen.");
  else if (ans.Q5 === "none") s.push("Todavía no tenés un colchón separado para imprevistos, así que conviene ser prudente.");

  if (p.capacity_binding)
    s.push("Aunque las subidas y bajadas no parecen preocuparte demasiado, como podrías necesitar el dinero relativamente pronto, elegimos algo más estable.");
  else if (p.tolerance_binding)
    s.push("Podrías tomar algo más de riesgo por tu situación, pero preferís tranquilidad, así que lo respetamos.");
  else s.push(riskSentence(p.risk_label));
  return s;
}

function riskSentence(label: string): string {
  if (label === "VERY_CONSERVATIVE" || label === "CONSERVATIVE")
    return "Por tus respuestas, preferís evitar sobresaltos, así que priorizamos la estabilidad.";
  if (label === "MODERATE")
    return "Por tus respuestas, podrías tolerar algunas subidas y bajadas a cambio de más crecimiento.";
  return "Por tus respuestas, estás cómodo/a con las variaciones a cambio de más crecimiento a largo plazo.";
}

function objetivo(label: string): string {
  if (label === "VERY_CONSERVATIVE" || label === "CONSERVATIVE")
    return "Cuidar tu dinero y que crezca de forma estable, con pocas variaciones.";
  if (label === "MODERATE")
    return "Un equilibrio entre hacer crecer tu dinero y mantener el riesgo bajo control.";
  return "Hacer crecer tu dinero en el largo plazo, aceptando más variaciones en el camino.";
}

export default function ResultScreen({
  userName,
  assessment,
  recommendation,
  onAdvanced,
  onRedo,
  onSwitch,
}: {
  userName: string;
  assessment: AssessmentResult;
  recommendation: Recommendation;
  onAdvanced: () => void;
  onRedo: () => void;
  onSwitch: () => void;
}) {
  const rec = recommendation.optimization.recommended;
  const sim = recommendation.simulation;
  const currency = recommendation.resolved_inputs.base_currency || "USD";
  const target = recommendation.resolved_inputs.target_wealth as number | null;
  const worst = sim.historical_scenarios.length
    ? Math.min(...sim.historical_scenarios.map((x) => x.portfolio_return))
    : null;
  const prob = sim.terminal.prob_reaching_target;
  const recon = recommendation.goal_reconciliation;

  return (
    <div className="container rs">
      <div className="rs-head">
        <h1>Hola, {userName}</h1>
        <button className="linkbtn" onClick={onSwitch}>Cambiar de perfil</button>
      </div>

      <div className="card">
        <h2>Así entendemos tu situación</h2>
        {buildSummary(assessment).map((line, i) => <p key={i} className="rs-summary">{line}</p>)}
        <p className="rs-goal">
          PortfolioQuant va a buscar una cartera que priorice: <strong>{objetivo(rec.label ?? assessment.profile.risk_label)}</strong>
        </p>
        <p className="rs-summary" style={{ marginTop: 10 }}>
          Para vos elegimos la cartera <strong>«{recommendation.primary_model.name}»</strong>: {recommendation.primary_model.rationale}
          {recommendation.advisor === "ai" ? <span className="ai-badge">pensada con IA</span> : null}
        </p>
      </div>

      <div className="card">
        <h2>Tu propuesta</h2>

        {prob !== null && target ? (
          <div className="goal-banner">
            <div className="pct">{fmtPct(prob, 0)}</div>
            <div className="lbl">de probabilidad de llegar a {fmtCurrency(target, currency)}</div>
          </div>
        ) : null}

        {recon && recon.needs_action ? (
          <div className="rs-lever">
            <strong>Hoy tu objetivo es poco probable ({fmtPct(recon.current_prob, 0)}).</strong> Para
            acercarte a ~{fmtPct(recon.target_prob, 0)} sin tomar más riesgo del que te conviene, podrías:
            <ul>
              {recon.extra_per_month && recon.monthly_needed ? (
                <li>Aportar <strong>{fmtCurrency(recon.monthly_needed, currency)}/mes</strong> (unos {fmtCurrency(recon.extra_per_month, currency)} más que ahora).</li>
              ) : null}
              {recon.extra_years && recon.years_needed ? (
                <li>Darle <strong>{recon.extra_years} año{recon.extra_years > 1 ? "s" : ""} más</strong> (en total {recon.years_needed} años).</li>
              ) : null}
              {recon.achievable_target ? (
                <li>O ajustar la meta a <strong>{fmtCurrency(recon.achievable_target, currency)}</strong>, que sí alcanzás con ~{fmtPct(recon.target_prob, 0)} de probabilidad.</li>
              ) : null}
            </ul>
            No subimos el riesgo para "forzar" la meta: eso te expondría a caídas que no te convienen.
          </div>
        ) : null}

        <div className="rs-blocks">
          <div className="rs-block">
            <div className="rs-block-t">Qué buscamos</div>
            <p>{objetivo(rec.label ?? assessment.profile.risk_label)}</p>
          </div>
          <div className="rs-block">
            <div className="rs-block-t">Qué podría pasar</div>
            <p>
              En años normales, el valor sube y baja.
              {worst !== null
                ? ` En una crisis fuerte, una cartera así podría caer temporalmente alrededor de ${fmtPct(Math.abs(worst), 0)}.`
                : ` Las caídas dependen de cuánto riesgo tenga la cartera.`}
            </p>
          </div>
          <div className="rs-block">
            <div className="rs-block-t">Tu objetivo</div>
            <p>
              {prob !== null && target
                ? `Según nuestras simulaciones, esta estrategia alcanza o supera tu objetivo en el ${fmtPct(prob, 0)} de los escenarios.`
                : "No fijaste un objetivo puntual; te mostramos igual cómo podría evolucionar tu dinero."}
            </p>
          </div>
        </div>

        <div className="section-title">Tu cartera</div>
        <WeightsPie weights={rec.weights} />

        <div className="section-title">Qué hay adentro de tu cartera</div>
        <p className="sub" style={{ marginBottom: 12 }}>Cada fondo agrupa muchas empresas. Esto es lo que estás comprando, con su precio de hoy (diferido ~15 min).</p>
        <PortfolioComposition weights={rec.weights} />

        <div className="rs-actions">
          <button className="btn" onClick={onAdvanced}>Ver análisis avanzado</button>
          <button className="btn-secondary" onClick={onRedo}>¿Cambió algo? Rehacer cuestionario</button>
        </div>

        <p className="rs-disclaimer">
          Esto no es asesoramiento financiero personalizado. Rendimientos pasados no garantizan
          rendimientos futuros. Las compras las realizás vos por tu cuenta.
        </p>
      </div>

      {recommendation.alternatives.length > 0 ? (
        <div className="card">
          <h2>Otras carteras posibles (y sus riesgos)</h2>
          <p className="sub" style={{ marginBottom: 12 }}>
            No hay una sola forma de invertir. Estas son otras opciones para tu mismo nivel de
            riesgo, con por qué elegirlas y qué implican.
          </p>
          <div className="alt-list">
            {recommendation.alternatives.map((a) => (
              <div className="alt-card" key={a.id}>
                <div className="alt-head">
                  <strong>{a.name}</strong>
                  <span className="alt-metrics">
                    Retorno {fmtPct(a.expected_return)} · Vol {fmtPct(a.volatility)} · Sharpe {fmtNum(a.sharpe_ratio)}
                  </span>
                </div>
                <div className="alt-desc">{a.description}</div>
                <div className="alt-weights">
                  {a.weights.map((w) => `${w.symbol} ${(w.weight * 100).toFixed(0)}%`).join(" · ")}
                </div>
                <div className="alt-why"><span>Por qué elegirla:</span> {a.rationale}</div>
                <div className="alt-risk"><span>Riesgo de elegirla:</span> {a.risks}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="card">
        <h2>Referencias del mercado argentino</h2>
        <p className="sub" style={{ marginBottom: 12 }}>Para tener contexto local. Tu cartera está en dólares.</p>
        <ArgentinaPanel />
      </div>
    </div>
  );
}
