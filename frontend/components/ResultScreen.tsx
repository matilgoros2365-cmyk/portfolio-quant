"use client";

import type { AssessmentResult, Recommendation } from "@/lib/types";
import { fmtCurrency, fmtPct } from "@/lib/format";
import WeightsPie from "@/components/WeightsPie";

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
  const alarm = recommendation.resolved_inputs.goal_alarm_prob ?? 0;

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
      </div>

      <div className="card">
        <h2>Tu propuesta</h2>

        {prob !== null && target ? (
          <div className="goal-banner">
            <div className="pct">{fmtPct(prob, 0)}</div>
            <div className="lbl">de probabilidad de llegar a {fmtCurrency(target, currency)}</div>
          </div>
        ) : null}

        {prob !== null && target && prob < alarm ? (
          <div className="rs-lever">
            Para acercarte más a tu objetivo sin tomar más riesgo del que te conviene, podrías
            aportar un poco más por mes, darle más tiempo, o ajustar la meta. Lo vemos juntos cuando quieras.
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

        <div className="rs-actions">
          <button className="btn" onClick={onAdvanced}>Ver análisis avanzado</button>
          <button className="btn-secondary" onClick={onRedo}>¿Cambió algo? Rehacer cuestionario</button>
        </div>

        <p className="rs-disclaimer">
          Esto no es asesoramiento financiero personalizado. Rendimientos pasados no garantizan
          rendimientos futuros. Las compras las realizás vos por tu cuenta.
        </p>
      </div>
    </div>
  );
}
