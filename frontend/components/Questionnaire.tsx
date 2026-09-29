"use client";

import { useMemo, useState } from "react";
import { QUESTIONS, visibleQuestions, withDontKnow, type Question } from "@/lib/questions";

export default function Questionnaire({
  userName,
  onComplete,
  onCancel,
  submitting,
}: {
  userName: string;
  onComplete: (answers: Record<string, any>) => void;
  onCancel: () => void;
  submitting: boolean;
}) {
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [currentId, setCurrentId] = useState<string>(QUESTIONS[0].id);
  const [started, setStarted] = useState(false);

  const visible = useMemo(() => visibleQuestions(answers), [answers]);
  const idx = Math.max(0, visible.findIndex((q) => q.id === currentId));
  const q = visible[idx] ?? visible[0];

  function set(key: string, value: any) {
    setAnswers((a) => ({ ...a, [key]: value }));
  }

  function toggleMulti(key: string, value: string) {
    setAnswers((a) => {
      const cur: string[] = Array.isArray(a[key]) ? a[key] : [];
      // "none" es exclusivo
      if (value === "none" || value === "dont_know") return { ...a, [key]: [value] };
      const next = cur.filter((v) => v !== "none" && v !== "dont_know");
      return { ...a, [key]: next.includes(value) ? next.filter((v) => v !== value) : [...next, value] };
    });
  }

  const currency = answers.currency === "ARS" ? "ARS" : "USD";

  function isAnswered(question: Question): boolean {
    if (question.kind === "money") {
      return !question.required || Number(answers[question.moneyField!]) > 0;
    }
    if (question.kind === "multi") {
      return Array.isArray(answers[question.id]) && answers[question.id].length > 0;
    }
    const chosen = answers[question.id];
    if (!chosen) return false;
    if (question.kind === "choice_money" && (question.amountFor ?? []).includes(chosen)) {
      return Number(answers[question.amountField!]) > 0;
    }
    return true;
  }

  function next() {
    const list = visibleQuestions(answers);
    const i = list.findIndex((x) => x.id === q.id);
    if (i >= list.length - 1) {
      onComplete(answers);
    } else {
      setCurrentId(list[i + 1].id);
    }
  }

  function prev() {
    const list = visibleQuestions(answers);
    const i = list.findIndex((x) => x.id === q.id);
    if (i <= 0) {
      onCancel();
    } else {
      setCurrentId(list[i - 1].id);
    }
  }

  if (!started) {
    return (
      <div className="q-wrap">
        <div className="q-card">
          <h2>Antes de empezar, queremos conocerte un poco</h2>
          <p className="q-intro">
            Hola {userName}. No necesitás saber nada de inversiones. Te vamos a hacer
            algunas preguntas sobre tus objetivos y tu situación; PortfolioQuant se
            encarga de todos los cálculos.
          </p>
          <button className="btn" onClick={() => setStarted(true)}>Empezar</button>
          <button className="linkbtn" style={{ marginTop: 12 }} onClick={onCancel}>Volver</button>
        </div>
      </div>
    );
  }

  const progress = Math.round(((idx + 1) / visible.length) * 100);

  return (
    <div className="q-wrap">
      <div className="q-card">
        <div className="q-progresswrap">
          <div className="q-progressbar"><div className="q-progressfill" style={{ width: `${progress}%` }} /></div>
          <div className="q-progresslabel">Pregunta {idx + 1} de {visible.length}</div>
        </div>

        <h2 className="q-title">{q.title}</h2>
        {q.why ? <p className="q-why">{q.why}</p> : null}
        {q.help ? <p className="q-help">{q.help}</p> : null}

        {/* choice / choice_money */}
        {(q.kind === "choice" || q.kind === "choice_money") && (
          <div className="q-options">
            {withDontKnow(q).map((o) => (
              <button
                key={o.value}
                className={`q-option ${answers[q.id] === o.value ? "selected" : ""}`}
                onClick={() => set(q.id, o.value)}
              >
                {o.label}
              </button>
            ))}
          </div>
        )}

        {/* nombre opcional del objetivo */}
        {q.nameField && (q.nameFor ?? []).includes(answers[q.id]) && (
          <div className="q-extra">
            <label>{q.nameLabel}</label>
            <input value={answers[q.nameField] ?? ""} onChange={(e) => set(q.nameField!, e.target.value)} />
          </div>
        )}

        {/* monto de choice_money */}
        {q.kind === "choice_money" && (q.amountFor ?? []).includes(answers[q.id]) && (
          <div className="q-extra">
            <label>{q.amountLabel}</label>
            <div className="q-money">
              <span className="q-cur">{currency}</span>
              <input type="number" min={0} value={answers[q.amountField!] ?? ""}
                onChange={(e) => set(q.amountField!, e.target.value === "" ? "" : +e.target.value)} />
            </div>
          </div>
        )}

        {/* money */}
        {q.kind === "money" && (
          <div className="q-extra">
            <div className="q-money">
              <span className="q-cur">{currency}</span>
              <input type="number" min={0} value={answers[q.moneyField!] ?? ""}
                onChange={(e) => set(q.moneyField!, e.target.value === "" ? "" : +e.target.value)} />
            </div>
          </div>
        )}

        {/* multi */}
        {q.kind === "multi" && (
          <div className="q-options">
            {withDontKnow(q).map((o) => {
              const arr: string[] = Array.isArray(answers[q.id]) ? answers[q.id] : [];
              return (
                <button key={o.value}
                  className={`q-option ${arr.includes(o.value) ? "selected" : ""}`}
                  onClick={() => toggleMulti(q.id, o.value)}>
                  {arr.includes(o.value) ? "✓ " : ""}{o.label}
                </button>
              );
            })}
          </div>
        )}

        <div className="q-nav">
          <button className="btn-secondary" onClick={prev} disabled={submitting}>Atrás</button>
          <button className="btn" onClick={next} disabled={!isAnswered(q) || submitting}>
            {submitting ? (<><span className="spinner" />Calculando…</>) : idx >= visible.length - 1 ? "Ver mi perfil" : "Siguiente"}
          </button>
        </div>
      </div>
    </div>
  );
}
