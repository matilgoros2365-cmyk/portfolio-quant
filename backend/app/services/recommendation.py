"""RecommendationService: del perfil a la cartera.

- Un asesor de IA (OpenRouter) propone universos a medida del perfil; si no hay
  key o falla, se usa el fallback: los modelos de cartera curados.
- El motor cuantitativo optimiza y simula cada propuesta con datos reales.
- Si la meta es poco probable, calcula palancas concretas (Fase 5).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.profiling.model_portfolios import (
    available_models,
    select_primary,
)
from app.profiling.universe import filter_tickers
from app.quant.reconciliation import reconcile
from app.schemas.recommendation import (
    GoalReconciliation,
    ModelInfo,
    ModelPortfolio,
)
from app.services.ai_advisor import ALLOWLIST, Candidate, build_advisor
from app.services.audit import save_analysis
from app.services.market_data.engine import MarketDataEngine
from app.services.optimizer import InsufficientDataError, PortfolioOptimizer
from app.services.simulation import SimulationService

_AUTO = object()


class RecommendationService:
    def __init__(
        self, db: Session, engine: MarketDataEngine | None = None, advisor=_AUTO
    ) -> None:
        self.db = db
        self.mde = engine or MarketDataEngine(db)
        self.optimizer = PortfolioOptimizer(db, engine=self.mde)
        self.simulator = SimulationService(db, engine=self.mde)
        self.advisor = build_advisor() if advisor is _AUTO else advisor

    # ------------------------------------------------------------ candidatos
    def _curated_candidates(self, d: dict) -> list[Candidate]:
        primary = select_primary(d.get("goal_type"), d.get("risk_label"))
        exclusions = d.get("exclusions", [])
        models = [primary] + [
            m for m in available_models(exclusions) if m.id != primary.id
        ]
        return [
            Candidate(m.id, m.name, m.tickers, m.description, m.rationale, m.risks)
            for m in models
        ]

    def _candidates(self, d: dict) -> tuple[list[Candidate], str]:
        """Devuelve (candidatos, fuente): IA si se pudo, si no curados."""
        if self.advisor is not None:
            context = {
                "goal_type": d.get("goal_type"),
                "horizon_years": d.get("investment_horizon_years"),
                "risk_label": d.get("risk_label"),
                "short_horizon": (d.get("investment_horizon_years") or 10) <= 3,
                "currency": d.get("currency", "USD"),
                "exclusions": d.get("exclusions", []),
            }
            try:
                cands = self.advisor.suggest(context, ALLOWLIST)
            except Exception:  # noqa: BLE001
                cands = None
            if cands:
                return cands, "ai"
        return self._curated_candidates(d), "curated"

    # ------------------------------------------------------------ recomendar
    def recommend(
        self, user_id: str, assessment: Assessment, n_simulations: int = 50_000
    ) -> dict:
        d = assessment.derived
        exclusions = d.get("exclusions", [])
        risk_level = d.get("risk_level")
        max_weight = d.get("max_weight")
        currency = d.get("currency", "USD")

        candidates, source = self._candidates(d)

        # Elegir el primer candidato que optimice bien -> primario; el resto -> alternativas.
        primary_c: Candidate | None = None
        primary_opt = None
        alternatives: list[ModelPortfolio] = []
        for c in candidates:
            tk = filter_tickers([t for t in c.tickers if t in ALLOWLIST], exclusions) \
                if source == "ai" else filter_tickers(c.tickers, exclusions)
            if len(tk) < 2:
                continue
            try:
                opt = self.optimizer.optimize(
                    tk, risk_level=risk_level, base_currency=currency, max_weight=max_weight
                )
            except InsufficientDataError:
                continue
            if primary_c is None:
                primary_c, primary_opt, primary_tk = c, opt, tk
            else:
                r = opt.recommended
                alternatives.append(ModelPortfolio(
                    id=c.id, name=c.name, description=c.description,
                    rationale=c.rationale, risks=c.risks,
                    expected_return=r.expected_return, volatility=r.volatility,
                    sharpe_ratio=r.sharpe_ratio, weights=r.weights,
                ))

        # Fallback último: cartera global diversificada.
        if primary_c is None:
            primary_tk = ["VT", "BND", "GLD"]
            primary_opt = self.optimizer.optimize(
                primary_tk, risk_level=risk_level, base_currency=currency, max_weight=max_weight
            )
            primary_c = Candidate(
                "global_div", "Global diversificada", primary_tk,
                "Acciones del mundo, bonos y oro.",
                "La más diversificada y simple.",
                "Crece más lento que una apuesta concentrada; igual cae en crisis globales.",
            )
            source = "curated"

        monthly = d.get("monthly_contribution_effective")
        if monthly is None:
            monthly = d.get("monthly_contribution") or 0.0
        initial = d.get("initial_capital") or 0.0
        years = d.get("investment_horizon_years") or 10
        target = d.get("target_wealth")

        inp = {
            "symbols": primary_tk,
            "risk_level": risk_level,
            "risk_label": d.get("risk_label"),
            "max_weight": max_weight,
            "base_currency": currency,
            "initial_capital": initial,
            "monthly_contribution": monthly,
            "investment_horizon_years": years,
            "target_wealth": target,
            "goal_alarm_prob": d.get("goal_alarm_prob"),
            "primary_model": primary_c.id,
            "advisor": source,
        }

        primary_opt.analysis_id = save_analysis(
            self.db, "optimize", inp, primary_opt.model_dump(mode="json"),
            risk_profile=primary_opt.risk_profile.value, base_currency=currency,
            label=primary_opt.recommended.label, user_id=user_id,
        )

        sim = self.simulator.simulate(
            primary_tk, risk_level=risk_level, initial_capital=initial,
            monthly_contribution=monthly, years=years, target_wealth=target,
            n_simulations=n_simulations, base_currency=currency, max_weight=max_weight,
            seed=42,
        )
        sim.analysis_id = save_analysis(
            self.db, "simulate", inp, sim.model_dump(mode="json"),
            risk_profile=sim.risk_profile.value, base_currency=currency, user_id=user_id,
        )

        # --- Reconciliación del objetivo (Fase 5) ---
        reconciliation = None
        prob = sim.terminal.prob_reaching_target
        alarm = d.get("goal_alarm_prob") or 0.0
        if target and prob is not None and prob < alarm:
            rec = reconcile(
                sim.expected_annual_return, sim.annual_volatility, initial,
                monthly, years, float(target), float(alarm),
            )
            reconciliation = GoalReconciliation(
                current_prob=rec.current_prob, target_prob=rec.target_prob,
                needs_action=rec.needs_action, achievable_target=rec.achievable_target,
                monthly_needed=rec.monthly_needed, extra_per_month=rec.extra_per_month,
                years_needed=rec.years_needed, extra_years=rec.extra_years,
            )

        return {
            "resolved_inputs": inp,
            "advisor": source,
            "primary_model": ModelInfo(
                id=primary_c.id, name=primary_c.name, description=primary_c.description,
                rationale=primary_c.rationale, risks=primary_c.risks,
            ),
            "optimization": primary_opt,
            "simulation": sim,
            "alternatives": alternatives,
            "goal_reconciliation": reconciliation,
        }
