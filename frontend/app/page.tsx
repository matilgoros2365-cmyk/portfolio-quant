"use client";

import { useEffect, useState } from "react";
import {
  createAssessment,
  createUser,
  getCurrentAssessment,
  getRecommendation,
  listUsers,
} from "@/lib/api";
import type {
  AppUser,
  AssessmentResult,
  FormInputs,
  Recommendation,
} from "@/lib/types";
import ProfileSelector from "@/components/ProfileSelector";
import Questionnaire from "@/components/Questionnaire";
import ResultScreen from "@/components/ResultScreen";
import AdvancedDashboard from "@/components/AdvancedDashboard";
import PaperScreen from "@/components/PaperScreen";

type View = "profiles" | "home" | "questionnaire" | "result" | "advanced" | "practica";

export default function Home() {
  const [view, setView] = useState<View>("profiles");
  const [users, setUsers] = useState<AppUser[]>([]);
  const [user, setUser] = useState<AppUser | null>(null);
  const [assessment, setAssessment] = useState<AssessmentResult | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);

  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listUsers().then(setUsers).catch(() => setUsers([]));
  }, []);

  function fail(e: unknown) {
    setError(e instanceof Error ? e.message : "Error desconocido");
    setBusy(false);
    setStatus(null);
  }

  async function loadRecommendation(u: AppUser, a: AssessmentResult) {
    setStatus("Armando tu propuesta con datos de mercado… (puede tardar la primera vez)");
    const rec = await getRecommendation(u.id);
    setAssessment(a);
    setRecommendation(rec);
    setView("result");
    setBusy(false);
    setStatus(null);
  }

  async function handleSelect(u: AppUser) {
    setError(null);
    setBusy(true);
    setUser(u);
    setRecommendation(null);
    try {
      const current = await getCurrentAssessment(u.id);
      setAssessment(current);
      setView("home");
      setBusy(false);
    } catch (e) {
      fail(e);
    }
  }

  async function handleCreate(name: string) {
    setError(null);
    setBusy(true);
    try {
      const u = await createUser(name);
      setUsers((prev) => [...prev, u]);
      setUser(u);
      setAssessment(null);
      setRecommendation(null);
      setView("home");
      setBusy(false);
    } catch (e) {
      fail(e);
    }
  }

  async function showRecommendation() {
    if (!user) return;
    if (!assessment) {
      setView("questionnaire");
      return;
    }
    setBusy(true);
    try {
      await loadRecommendation(user, assessment);
    } catch (e) {
      fail(e);
    }
  }

  async function handleQuestionnaireComplete(answers: Record<string, any>) {
    if (!user) return;
    setError(null);
    setBusy(true);
    try {
      const a = await createAssessment(user.id, answers);
      await loadRecommendation(user, a);
    } catch (e) {
      fail(e);
    }
  }

  function advancedInputs(): FormInputs | null {
    if (!recommendation) return null;
    const ri = recommendation.resolved_inputs;
    return {
      initial_capital: ri.initial_capital ?? 0,
      monthly_contribution: ri.monthly_contribution ?? 0,
      investment_horizon_years: ri.investment_horizon_years ?? 10,
      base_currency: ri.base_currency ?? "USD",
      risk_profile: recommendation.optimization.risk_profile,
      target_wealth: ri.target_wealth ?? null,
      custom_asset_universe: ri.symbols ?? [],
      max_weight: ri.max_weight ?? null,
      method: "gaussian",
      n_simulations: 50000,
    };
  }

  function resetToProfiles() {
    setUser(null);
    setAssessment(null);
    setRecommendation(null);
    setError(null);
    setView("profiles");
  }

  return (
    <>
      <header className="app-header">
        <div className="wrap">
          <h1>PortfolioQuant</h1>
          <p>Vos contás tu situación; nosotros hacemos los cálculos y te proponemos una cartera.</p>
        </div>
      </header>

      {error ? <div className="container"><div className="alert">{error}</div></div> : null}

      {busy && status ? (
        <div className="container">
          <div className="card placeholder"><span className="spinner" style={{ borderColor: "#c7d2fe", borderTopColor: "#4f46e5" }} /> {status}</div>
        </div>
      ) : null}

      {!busy || !status ? (
        <>
          {view === "profiles" && (
            <ProfileSelector users={users} onSelect={handleSelect} onCreate={handleCreate} busy={busy} />
          )}
          {view === "home" && user && (
            <div className="container" style={{ maxWidth: 720 }}>
              <div className="rs-head">
                <h1>Hola, {user.name}</h1>
                <button className="linkbtn" onClick={resetToProfiles}>Cambiar de perfil</button>
              </div>
              <div className="home-grid">
                <button className="home-card" onClick={showRecommendation}>
                  <div className="home-t">Ver mi propuesta de cartera</div>
                  <div className="home-d">
                    {assessment
                      ? "Tu recomendación personalizada, con análisis y proyección."
                      : "Respondé unas preguntas y te armamos una cartera a medida."}
                  </div>
                </button>
                <button className="home-card" onClick={() => setView("practica")}>
                  <div className="home-t">Jugar (modo práctica)</div>
                  <div className="home-d">
                    Invertí con $100.000 de plata ficticia y precios reales. Sin riesgo.
                  </div>
                </button>
              </div>
              {assessment ? (
                <div style={{ textAlign: "center", marginTop: 16 }}>
                  <button className="linkbtn" onClick={() => setView("questionnaire")}>¿Cambió tu situación? Rehacer cuestionario</button>
                </div>
              ) : null}
            </div>
          )}
          {view === "questionnaire" && user && (
            <Questionnaire
              userName={user.name}
              submitting={busy}
              onComplete={handleQuestionnaireComplete}
              onCancel={resetToProfiles}
            />
          )}
          {view === "result" && user && assessment && recommendation && (
            <ResultScreen
              userName={user.name}
              assessment={assessment}
              recommendation={recommendation}
              onAdvanced={() => setView("advanced")}
              onRedo={() => setView("questionnaire")}
              onSwitch={resetToProfiles}
              onPractice={() => setView("practica")}
            />
          )}
          {view === "advanced" && (
            <AdvancedDashboard initialInputs={advancedInputs()} onBack={() => setView("result")} />
          )}
          {view === "practica" && user && (
            <PaperScreen
              userId={user.id}
              userName={user.name}
              recommended={recommendation?.optimization.recommended.weights}
              onBack={() => setView("home")}
            />
          )}
        </>
      ) : null}
    </>
  );
}
