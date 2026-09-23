"""RobustnessService: Black-Litterman + estabilidad de la optimización (Fase 5)."""
from __future__ import annotations

import numpy as np
from sqlalchemy.orm import Session

from app.models.portfolio import RiskProfile
from app.quant.black_litterman import (
    black_litterman_returns,
    market_implied_risk_aversion,
)
from app.quant.expected import annualized_covariance, historical_expected_returns
from app.quant.optimization import portfolio_for_risk_level
from app.quant.stability import resampled_optimization
from app.schemas.optimization import ProposedWeight
from app.schemas.robustness import (
    ExpectedReturnComparison,
    RobustnessResponse,
    StabilityItem,
)
from app.services.analysis import PortfolioAnalyzer
from app.services.market_data.engine import MarketDataEngine
from app.services.optimizer import (
    RISK_PROFILE_LEVELS,
    InsufficientDataError,
    PortfolioOptimizer,
)


def _weights_list(symbols, weights, names, min_w=5e-4):
    out = [
        ProposedWeight(symbol=s, name=names.get(s), weight=round(float(w), 4))
        for s, w in zip(symbols, weights)
        if w >= min_w
    ]
    out.sort(key=lambda p: p.weight, reverse=True)
    return out


class RobustnessService:
    def __init__(self, db: Session, engine: MarketDataEngine | None = None) -> None:
        self.db = db
        self.mde = engine or MarketDataEngine(db)
        self.optimizer = PortfolioOptimizer(db, engine=self.mde)

    def analyze(
        self,
        symbols: list[str],
        risk_profile: RiskProfile,
        base_currency: str = "USD",
        max_weight: float | None = None,
        n_resamples: int = 100,
        seed: int | None = None,
    ) -> RobustnessResponse:
        aligned, names, _ = self.optimizer._load_aligned_returns(symbols)
        if len(aligned.columns) < 2:
            raise InsufficientDataError(
                "Se necesitan al menos 2 activos con datos para el análisis de robustez."
            )

        ordered = list(aligned.columns)
        n = len(ordered)
        mu_hist = historical_expected_returns(aligned).to_numpy()
        cov = annualized_covariance(aligned).to_numpy()
        rf = PortfolioAnalyzer(self.db, engine=self.mde).get_risk_free_rate()
        level = RISK_PROFILE_LEVELS[risk_profile]

        # --- Black-Litterman: prior de mercado = pesos iguales (sin caps) ---
        w_market = np.full(n, 1.0 / n)
        market_return = float(mu_hist @ w_market)
        market_var = float(w_market @ cov @ w_market)
        delta = market_implied_risk_aversion(market_return, market_var, rf)
        delta = float(min(max(delta, 1.0), 10.0))  # acotar a un rango sensato
        mu_bl = black_litterman_returns(cov, w_market, risk_aversion=delta)

        expected_returns = [
            ExpectedReturnComparison(
                symbol=s,
                historical=round(float(mu_hist[i]), 4),
                black_litterman=round(float(mu_bl[i]), 4),
            )
            for i, s in enumerate(ordered)
        ]

        # --- Carteras: histórica vs Black-Litterman ---
        w_hist = portfolio_for_risk_level(mu_hist, cov, level, max_weight)
        w_bl = portfolio_for_risk_level(mu_bl, cov, level, max_weight)

        # --- Estabilidad por remuestreo ---
        stab = resampled_optimization(
            aligned, level, n_resamples=n_resamples, max_weight=max_weight, seed=seed
        )
        stability = [
            StabilityItem(
                symbol=s,
                recommended_weight=round(float(w_hist[i]), 4),
                mean_weight=round(float(stab.mean_weights[i]), 4),
                std_weight=round(float(stab.std_weights[i]), 4),
            )
            for i, s in enumerate(ordered)
        ]

        notes = [
            "Black-Litterman parte de un prior de mercado con pesos iguales "
            "(no usamos capitalización de mercado por ahora); da retornos de "
            "equilibrio más suaves que la media histórica.",
            "La 'inestabilidad' es la dispersión media de los pesos al "
            "remuestrear los datos: más baja = cartera más robusta.",
        ]

        return RobustnessResponse(
            base_currency=base_currency,
            risk_profile=risk_profile,
            risk_aversion=round(delta, 3),
            instability=round(stab.instability, 4),
            n_resamples=n_resamples,
            expected_returns=expected_returns,
            historical_weights=_weights_list(ordered, w_hist, names),
            black_litterman_weights=_weights_list(ordered, w_bl, names),
            stability=stability,
            notes=notes,
        )
