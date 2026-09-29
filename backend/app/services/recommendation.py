"""RecommendationService: del perfil a la cartera, con alternativas y reconciliación.

- Elige un modelo de cartera primario según el perfil (no siempre el mismo).
- Ofrece otros modelos como alternativas, con su lógica y riesgos.
- Si la meta es poco probable, calcula palancas concretas (Fase 5).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.profiling.model_portfolios import (
    available_models,
    model_tickers,
    select_primary,
)
from app.quant.reconciliation import reconcile
from app.schemas.recommendation import (
    GoalReconciliation,
    ModelInfo,
    ModelPortfolio,
)
from app.services.audit import save_analysis
from app.services.market_data.engine import MarketDataEngine
from app.services.optimizer import InsufficientDataError, PortfolioOptimizer
from app.services.simulation import SimulationService


class RecommendationService:
    def __init__(self, db: Session, engine: MarketDataEngine | None = None) -> None:
        self.db = db
        self.mde = engine or MarketDataEngine(db)
        self.optimizer = PortfolioOptimizer(db, engine=self.mde)
        self.simulator = SimulationService(db, engine=self.mde)

    def recommend(
        self, user_id: str, assessment: Assessment, n_simulations: int = 50_000
    ) -> dict:
        d = assessment.derived
        exclusions = d.get("exclusions", [])
        risk_level = d.get("risk_level")
        max_weight = d.get("max_weight")
        currency = d.get("currency", "USD")

        primary = select_primary(d.get("goal_type"), d.get("risk_label"))
        symbols = model_tickers(primary, exclusions)
        if len(symbols) < 2:
            symbols = ["VT", "BND", "GLD"]

        monthly = d.get("monthly_contribution_effective")
        if monthly is None:
            monthly = d.get("monthly_contribution") or 0.0
        initial = d.get("initial_capital") or 0.0
        years = d.get("investment_horizon_years") or 10
        target = d.get("target_wealth")

        inp = {
            "symbols": symbols,
            "risk_level": risk_level,
            "risk_label": d.get("risk_label"),
            "max_weight": max_weight,
            "base_currency": currency,
            "initial_capital": initial,
            "monthly_contribution": monthly,
            "investment_horizon_years": years,
            "target_wealth": target,
            "goal_alarm_prob": d.get("goal_alarm_prob"),
            "primary_model": primary.id,
        }

        opt = self.optimizer.optimize(
            symbols, risk_level=risk_level, base_currency=currency, max_weight=max_weight
        )
        opt.analysis_id = save_analysis(
            self.db, "optimize", inp, opt.model_dump(mode="json"),
            risk_profile=opt.risk_profile.value, base_currency=currency,
            label=opt.recommended.label, user_id=user_id,
        )

        sim = self.simulator.simulate(
            symbols, risk_level=risk_level, initial_capital=initial,
            monthly_contribution=monthly, years=years, target_wealth=target,
            n_simulations=n_simulations, base_currency=currency, max_weight=max_weight,
            seed=42,
        )
        sim.analysis_id = save_analysis(
            self.db, "simulate", inp, sim.model_dump(mode="json"),
            risk_profile=sim.risk_profile.value, base_currency=currency, user_id=user_id,
        )

        # --- Alternativas: otros modelos de cartera ---
        alternatives: list[ModelPortfolio] = []
        for m in available_models(exclusions):
            if m.id == primary.id:
                continue
            tk = model_tickers(m, exclusions)
            if len(tk) < 2:
                continue
            try:
                alt = self.optimizer.optimize(
                    tk, risk_level=risk_level, base_currency=currency, max_weight=max_weight
                )
            except InsufficientDataError:
                continue
            r = alt.recommended
            alternatives.append(ModelPortfolio(
                id=m.id, name=m.name, description=m.description,
                rationale=m.rationale, risks=m.risks,
                expected_return=r.expected_return, volatility=r.volatility,
                sharpe_ratio=r.sharpe_ratio, weights=r.weights,
            ))

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
            "primary_model": ModelInfo(
                id=primary.id, name=primary.name, description=primary.description,
                rationale=primary.rationale, risks=primary.risks,
            ),
            "optimization": opt,
            "simulation": sim,
            "alternatives": alternatives,
            "goal_reconciliation": reconciliation,
        }
