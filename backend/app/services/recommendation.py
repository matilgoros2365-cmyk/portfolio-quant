"""RecommendationService: del perfil a la cartera, de punta a punta.

Toma el cuestionario vigente de un usuario, arma el universo automáticamente
(el principiante no elige tickers), y corre la optimización + la proyección
usando el nivel de riesgo continuo y los parámetros financieros derivados.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.profiling.universe import build_universe
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

    def resolve_inputs(self, assessment: Assessment) -> dict:
        """Traduce el cuestionario a los inputs concretos del motor."""
        d = assessment.derived
        universe = build_universe(
            preference=d.get("universe_preference", "global"),
            exclusions=d.get("exclusions", []),
        )
        monthly = d.get("monthly_contribution_effective")
        if monthly is None:
            monthly = d.get("monthly_contribution") or 0.0
        return {
            "symbols": universe,
            "risk_level": d.get("risk_level"),
            "risk_label": d.get("risk_label"),
            "max_weight": d.get("max_weight"),
            "base_currency": d.get("currency", "USD"),
            "initial_capital": d.get("initial_capital") or 0.0,
            "monthly_contribution": monthly,
            "investment_horizon_years": d.get("investment_horizon_years") or 10,
            "target_wealth": d.get("target_wealth"),
            "goal_alarm_prob": d.get("goal_alarm_prob"),
        }

    def recommend(
        self, user_id: str, assessment: Assessment, n_simulations: int = 50_000
    ) -> dict:
        inp = self.resolve_inputs(assessment)
        if len(inp["symbols"]) < 2:
            raise InsufficientDataError(
                "El universo quedó con menos de 2 activos tras aplicar las exclusiones."
            )

        opt = self.optimizer.optimize(
            inp["symbols"],
            risk_level=inp["risk_level"],
            base_currency=inp["base_currency"],
            max_weight=inp["max_weight"],
        )
        opt.analysis_id = save_analysis(
            self.db, "optimize", inp, opt.model_dump(mode="json"),
            risk_profile=opt.risk_profile.value, base_currency=inp["base_currency"],
            label=opt.recommended.label, user_id=user_id,
        )

        sim = self.simulator.simulate(
            inp["symbols"],
            risk_level=inp["risk_level"],
            initial_capital=inp["initial_capital"],
            monthly_contribution=inp["monthly_contribution"],
            years=inp["investment_horizon_years"],
            target_wealth=inp["target_wealth"],
            n_simulations=n_simulations,
            base_currency=inp["base_currency"],
            max_weight=inp["max_weight"],
            seed=42,
        )
        sim.analysis_id = save_analysis(
            self.db, "simulate", inp, sim.model_dump(mode="json"),
            risk_profile=sim.risk_profile.value, base_currency=inp["base_currency"],
            user_id=user_id,
        )

        return {
            "resolved_inputs": inp,
            "optimization": opt,
            "simulation": sim,
        }
