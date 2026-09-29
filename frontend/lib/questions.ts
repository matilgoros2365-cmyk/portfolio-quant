// Definición del cuestionario. Los IDs coinciden con las claves del scoring del backend.

export type QKind = "choice" | "multi" | "money" | "choice_money";

export interface QOption {
  value: string;
  label: string;
}

export interface Question {
  id: string;
  kind: QKind;
  title: string;
  help?: string;
  why?: string; // por qué preguntamos esto
  options?: QOption[];
  allowDontKnow?: boolean;
  // choice_money:
  amountFor?: string[]; // opciones que muestran un monto
  amountField?: string; // dónde se guarda el monto
  amountLabel?: string;
  // money:
  moneyField?: string;
  required?: boolean;
  // goal name:
  nameField?: string;
  nameFor?: string[];
  nameLabel?: string;
  // branching:
  visible?: (a: Record<string, any>) => boolean;
}

const DONT_KNOW: QOption = { value: "dont_know", label: "No estoy seguro/a" };

export const QUESTIONS: Question[] = [
  {
    id: "currency",
    kind: "choice",
    title: "¿En qué moneda querés pensar tus objetivos?",
    why: "Para mostrarte todo en la moneda que te resulta natural.",
    help: "Se invierte en instrumentos en dólares; para alguien en Argentina eso funciona como una cobertura ante la inflación.",
    options: [
      { value: "USD", label: "Dólares (USD)" },
      { value: "ARS", label: "Pesos argentinos (ARS)" },
    ],
  },
  {
    id: "Q1",
    kind: "choice",
    title: "¿Qué te gustaría conseguir con este dinero?",
    why: "Para entender el propósito de tu inversión.",
    options: [
      { value: "grow", label: "Hacer crecer mis ahorros" },
      { value: "big_purchase", label: "Ahorrar para comprar algo importante" },
      { value: "house", label: "Comprar una casa" },
      { value: "retirement", label: "Prepararme para mi jubilación" },
      { value: "income", label: "Generar ingresos para usar más adelante" },
      { value: "no_goal", label: "Todavía no tengo un objetivo específico" },
      { value: "other", label: "Otro" },
    ],
    nameField: "goal_name",
    nameFor: ["big_purchase", "house", "retirement", "income", "other"],
    nameLabel: "Ponele un nombre (opcional). Ej: “Comprar departamento”",
  },
  {
    id: "Q2",
    kind: "choice_money",
    title: "¿Hay una cantidad a la que te gustaría llegar?",
    why: "Con esto podemos calcular la probabilidad de alcanzar tu meta. No lo usamos para subir el riesgo.",
    options: [
      { value: "yes", label: "Sí" },
      { value: "no", label: "No" },
      { value: "unsure", label: "Todavía no lo sé" },
    ],
    amountFor: ["yes"],
    amountField: "target_wealth",
    amountLabel: "¿A cuánto te gustaría llegar?",
  },
  {
    id: "Q3",
    kind: "choice",
    title: "¿Cuándo pensás que podrías necesitar este dinero?",
    why: "Cuanto antes puedas necesitarlo, menos conviene depender de inversiones que suben y bajan mucho.",
    options: [
      { value: "lt_1y", label: "En menos de 1 año" },
      { value: "y1_3", label: "Entre 1 y 3 años" },
      { value: "y3_5", label: "Entre 3 y 5 años" },
      { value: "y5_10", label: "Entre 5 y 10 años" },
      { value: "gt_10", label: "Dentro de más de 10 años" },
      { value: "no_date", label: "No tengo una fecha definida" },
    ],
  },
  {
    id: "Q4",
    kind: "choice",
    title: "Si mañana necesitaras este dinero para otra cosa, ¿qué tan complicado sería?",
    why: "Nos ayuda a entender cuánto podés arriesgar sin ponerte en aprietos.",
    options: [
      { value: "other_savings", label: "No sería un problema, tengo otros ahorros" },
      { value: "manageable", label: "Podría manejarlo" },
      { value: "complicated", label: "Me complicaría bastante" },
      { value: "need_for_expenses", label: "Lo necesitaría para cubrir gastos importantes" },
    ],
  },
  {
    id: "Q5",
    kind: "choice",
    title: "Si apareciera un gasto inesperado importante, ¿tenés dinero separado para cubrirlo sin tocar esta inversión?",
    why: "Tener un colchón para emergencias te permite invertir con más tranquilidad.",
    options: [
      { value: "several_months", label: "Sí, podría cubrir varios meses de gastos" },
      { value: "some", label: "Sí, pero no demasiado" },
      { value: "none", label: "No" },
      { value: "unsure", label: "No estoy seguro/a" },
    ],
  },
  {
    id: "Q6",
    kind: "money",
    title: "¿Con cuánto dinero querés empezar?",
    why: "Es el dinero que pensás destinar a invertir ahora.",
    moneyField: "initial_capital",
    required: true,
  },
  {
    id: "Q7",
    kind: "choice_money",
    title: "¿Pensás agregar dinero regularmente?",
    why: "Los aportes periódicos ayudan muchísimo por el interés compuesto.",
    options: [
      { value: "monthly", label: "Sí, todos los meses" },
      { value: "irregular", label: "Sí, pero no todos los meses" },
      { value: "none", label: "Por ahora no" },
      { value: "unsure", label: "No estoy seguro/a" },
    ],
    amountFor: ["monthly", "irregular"],
    amountField: "monthly_contribution",
    amountLabel: "¿Cuánto aproximadamente por mes?",
  },
  {
    id: "Q8",
    kind: "choice",
    title: "¿Qué tan seguro/a estás de poder mantener ese aporte en los próximos años?",
    why: "Para no dar por sentado aportes futuros demasiado optimistas.",
    options: [
      { value: "very_sure", label: "Muy seguro/a" },
      { value: "fairly_sure", label: "Bastante seguro/a" },
      { value: "may_vary", label: "Puede variar" },
      { value: "probably_not", label: "Probablemente no pueda mantenerlo siempre" },
    ],
    visible: (a) => a.Q7 === "monthly" || a.Q7 === "irregular",
  },
  {
    id: "Q9",
    kind: "choice",
    title: "Imaginá que invertís $10.000 y, tras un año complicado, ves $8.500. No necesitás el dinero en ese momento. ¿Qué harías probablemente?",
    why: "No hay respuesta correcta: buscamos entender cómo reaccionarías, no qué sabés.",
    options: [
      { value: "sell_all", label: "Me preocuparía mucho y sacaría el dinero" },
      { value: "sell_part", label: "Probablemente sacaría una parte" },
      { value: "wait", label: "Esperaría antes de hacer cambios" },
      { value: "hold", label: "Lo dejaría invertido y seguiría con mi plan" },
      { value: "add", label: "Probablemente aprovecharía para agregar más" },
    ],
    allowDontKnow: true,
  },
  {
    id: "Q10",
    kind: "choice",
    title: "Sobre esos $10.000: ¿a partir de qué caída empezarías a sentirte realmente incómodo/a y pensarías en sacar el dinero?",
    why: "Es una señal de tu tolerancia, no un límite exacto.",
    options: [
      { value: "at_5", label: "Si baja a $9.500 (−5%)" },
      { value: "at_10", label: "Si baja a $9.000 (−10%)" },
      { value: "at_20", label: "Si baja a $8.000 (−20%)" },
      { value: "at_30", label: "Si baja a $7.000 (−30%)" },
    ],
    allowDontKnow: true,
    visible: (a) => a.Q3 !== "lt_1y",
  },
  {
    id: "QB",
    kind: "choice",
    title: "¿Con cuál te sentirías más cómodo/a?",
    why: "Nos ayuda a ubicarte cuando las otras respuestas no fueron concluyentes.",
    help: "A: tu dinero cambia poco; en años buenos crece menos, pero las caídas son menores. B: puede crecer mucho más, pero también caer bastante por un tiempo.",
    options: [
      { value: "def_a", label: "Definitivamente A (más estable)" },
      { value: "prob_a", label: "Probablemente A" },
      { value: "unsure", label: "No estoy seguro/a" },
      { value: "prob_b", label: "Probablemente B" },
      { value: "def_b", label: "Definitivamente B (más variable)" },
    ],
    visible: (a) =>
      a.Q9 === "dont_know" && (a.Q3 === "lt_1y" || a.Q10 === "dont_know"),
  },
  {
    id: "Q11",
    kind: "choice",
    title: "¿Qué tan importante es alcanzar el objetivo que nos contaste?",
    why: "Influye en cómo evaluamos la probabilidad de cumplir la meta (no en tomar más riesgo).",
    options: [
      { value: "essential", label: "Es imprescindible" },
      { value: "very_important", label: "Es muy importante" },
      { value: "flexible", label: "Me gustaría, pero tengo flexibilidad" },
      { value: "just_growth", label: "Es solo una forma de hacer crecer mis ahorros" },
    ],
  },
  {
    id: "Q12",
    kind: "choice",
    title: "¿Alguna vez invertiste dinero antes?",
    why: "Para ajustar cuánto detalle te mostramos (no cambia tu recomendación).",
    options: [
      { value: "never", label: "Nunca" },
      { value: "very_little", label: "Sí, pero muy poco" },
      { value: "sometimes", label: "Sí, algunas veces" },
      { value: "regularly", label: "Sí, invierto regularmente" },
    ],
  },
  {
    id: "Q13",
    kind: "multi",
    title: "¿Hay algo que definitivamente NO quieras que aparezca en tu cartera?",
    why: "Respetamos tus preferencias al armar la cartera.",
    options: [
      { value: "crypto", label: "Criptomonedas" },
      { value: "individual_companies", label: "Empresas individuales" },
      { value: "sectors", label: "Ciertos sectores" },
      { value: "none", label: "No tengo restricciones" },
    ],
    allowDontKnow: true,
  },
];

export function withDontKnow(q: Question): QOption[] {
  const opts = [...(q.options ?? [])];
  if (q.allowDontKnow) opts.push({ value: "dont_know", label: "No sé" });
  return opts;
}

export function visibleQuestions(answers: Record<string, any>): Question[] {
  return QUESTIONS.filter((q) => !q.visible || q.visible(answers));
}
