"""PortfolioOptimizer: genera la cartera recomendada según el perfil de riesgo.

Une la ingesta de datos, los retornos esperados y el motor de optimización
(cvxpy). Es la capa que consume el endpoint /portfolio/optimize.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.portfolio import RiskProfile
from app.quant.expected import (
    align_returns,
    annualized_covariance,
    historical_expected_returns,
)
from app.quant.formulas import formulas_subset
from app.quant.optimization import (
    efficient_frontier,
    max_sharpe_weights,
    min_variance_weights,
    portfolio_for_risk_level,
    portfolio_stats,
    risk_parity_weights,
)
from app.quant.returns import simple_returns
from app.schemas.optimization import (
    FrontierPoint,
    OptimizationCalculations,
    OptimizationResponse,
    OptimizedPortfolio,
    ProposedWeight,
)
from app.services.analysis import PortfolioAnalyzer
from app.services.market_data.engine import MarketDataEngine

# Traducción de perfil de riesgo -> nivel [0,1] sobre la frontera eficiente.
RISK_PROFILE_LEVELS: dict[RiskProfile, float] = {
    RiskProfile.VERY_CONSERVATIVE: 0.0,
    RiskProfile.CONSERVATIVE: 0.25,
    RiskProfile.MODERATE: 0.50,
    RiskProfile.AGGRESSIVE: 0.75,
    RiskProfile.VERY_AGGRESSIVE: 1.0,
}

# Etiqueta legible por perfil (para nombrar alternativas).
RISK_PROFILE_LABELS: dict[RiskProfile, str] = {
    RiskProfile.VERY_CONSERVATIVE: "Muy conservadora",
    RiskProfile.CONSERVATIVE: "Conservadora",
    RiskProfile.MODERATE: "Moderada",
    RiskProfile.AGGRESSIVE: "Agresiva",
    RiskProfile.VERY_AGGRESSIVE: "Muy agresiva",
}

# Mínimo de observaciones en común para optimizar con sentido.
MIN_COMMON_OBSERVATIONS = 30


class InsufficientDataError(ValueError):
    """No hay datos suficientes para optimizar."""


def _clean(value: float) -> float | None:
    if value is None:
        return None
    f = float(value)
    return None if (math.isnan(f) or math.isinf(f)) else f


class PortfolioOptimizer:
    def __init__(self, db: Session, engine: MarketDataEngine | None = None) -> None:
        self.db = db
        self.mde = engine or MarketDataEngine(db)

    # ------------------------------------------------------------ datos
    def _load_aligned_returns(
        self, symbols: list[str]
    ) -> tuple[pd.DataFrame, dict[str, str | None], set[str]]:
        returns_map: dict[str, pd.Series] = {}
        names: dict[str, str | None] = {}
        currencies: set[str] = set()

        for symbol in symbols:
            self.mde.sync_prices(symbol)
            prices_df = self.mde.get_price_dataframe(symbol)
            if prices_df.empty:
                continue
            sym = symbol.upper()
            returns_map[sym] = simple_returns(prices_df["adj_close"])
            asset = self.db.scalar(select(Asset).where(Asset.symbol == sym))
            names[sym] = asset.name if asset else None
            currencies.add(asset.currency if asset else "USD")

        aligned = align_returns(returns_map)
        return aligned, names, currencies

    # ------------------------------------------------------------ helpers
    def _weights_to_list(
        self,
        weights,
        symbols: list[str],
        names: dict[str, str | None],
        min_weight: float = 5e-4,
    ) -> list[ProposedWeight]:
        out = [
            ProposedWeight(symbol=sym, name=names.get(sym), weight=round(float(w), 4))
            for sym, w in zip(symbols, weights)
            if w >= min_weight
        ]
        out.sort(key=lambda p: p.weight, reverse=True)
        return out

    def _make_portfolio(
        self, strategy, weights, mu, cov, rf, symbols, names, label=None
    ) -> OptimizedPortfolio:
        stats = portfolio_stats(weights, mu, cov, rf)
        return OptimizedPortfolio(
            strategy=strategy,
            label=label,
            expected_return=stats["expected_return"],
            volatility=stats["volatility"],
            sharpe_ratio=_clean(stats["sharpe_ratio"]),
            weights=self._weights_to_list(weights, symbols, names),
        )

    def _matrix_dict(self, df: pd.DataFrame) -> dict[str, dict[str, float | None]]:
        return {
            str(row): {str(col): _clean(df.loc[row, col]) for col in df.columns}
            for row in df.index
        }

    # ------------------------------------------------------------ optimize
    def optimize(
        self,
        symbols: list[str],
        risk_profile: RiskProfile,
        base_currency: str = "USD",
        max_weight: float | None = None,
    ) -> OptimizationResponse:
        analyzer = PortfolioAnalyzer(self.db, engine=self.mde)
        rf = analyzer.get_risk_free_rate()

        aligned, names, currencies = self._load_aligned_returns(symbols)
        if len(aligned.columns) < 2:
            raise InsufficientDataError(
                "Se necesitan al menos 2 activos con datos para optimizar."
            )
        if len(aligned) < MIN_COMMON_OBSERVATIONS:
            raise InsufficientDataError(
                f"Muy pocas fechas en común ({len(aligned)}); se necesitan al "
                f"menos {MIN_COMMON_OBSERVATIONS}."
            )

        ordered_symbols = list(aligned.columns)
        mu = historical_expected_returns(aligned).to_numpy()
        cov = annualized_covariance(aligned).to_numpy()

        level = RISK_PROFILE_LEVELS[risk_profile]
        recommended_w = portfolio_for_risk_level(mu, cov, level, max_weight)
        recommended = self._make_portfolio(
            f"risk_profile:{risk_profile.value}",
            recommended_w,
            mu,
            cov,
            rf,
            ordered_symbols,
            names,
            label=f"Recomendada ({RISK_PROFILE_LABELS[risk_profile]})",
        )

        # Alternativas: un paso más conservadora y un paso más agresiva.
        alternatives: list[OptimizedPortfolio] = []
        for delta, lbl in ((-0.25, "Más conservadora"), (0.25, "Más agresiva")):
            alt_level = level + delta
            if 0.0 <= alt_level <= 1.0:
                alt_w = portfolio_for_risk_level(mu, cov, alt_level, max_weight)
                alternatives.append(
                    self._make_portfolio(
                        f"risk_level:{alt_level:.2f}", alt_w, mu, cov, rf,
                        ordered_symbols, names, label=lbl,
                    )
                )

        references = {
            "min_variance": self._make_portfolio(
                "min_variance",
                min_variance_weights(cov, max_weight),
                mu,
                cov,
                rf,
                ordered_symbols,
                names,
            ),
            "max_sharpe": self._make_portfolio(
                "max_sharpe",
                max_sharpe_weights(mu, cov, rf, max_weight),
                mu,
                cov,
                rf,
                ordered_symbols,
                names,
            ),
            "risk_parity": self._make_portfolio(
                "risk_parity",
                risk_parity_weights(cov),
                mu,
                cov,
                rf,
                ordered_symbols,
                names,
            ),
        }

        frontier = [
            FrontierPoint(
                expected_return=p["expected_return"],
                volatility=p["volatility"],
                sharpe_ratio=_clean(p["sharpe_ratio"]),
            )
            for p in efficient_frontier(mu, cov, n_points=25, max_weight=max_weight,
                                        risk_free_rate=rf)
        ]

        notes: list[str] = []
        if len(currencies) > 1:
            notes.append(
                "Los activos están en distintas monedas "
                f"({', '.join(sorted(currencies))}). En esta fase se optimiza "
                "sobre retornos en moneda nativa; la conversión FX a "
                f"{base_currency} se implementa más adelante."
            )
        notes.append(
            "Retornos esperados estimados con el histórico (media anualizada). "
            "Son un supuesto, no una garantía de rendimiento futuro."
        )

        as_of = None
        prices_index = self.mde.get_price_dataframe(ordered_symbols[0])
        if not prices_index.empty:
            as_of = prices_index.index[-1]

        # --- Cálculos intermedios (para revisar/auditar) ---
        cov_df = annualized_covariance(aligned)
        corr_df = aligned.corr()
        calculations = OptimizationCalculations(
            risk_free_rate=round(rf, 6),
            symbols=ordered_symbols,
            expected_returns={s: round(float(mu[i]), 4) for i, s in enumerate(ordered_symbols)},
            volatilities={
                s: round(float(np.sqrt(cov_df.loc[s, s])), 4) for s in ordered_symbols
            },
            correlation_matrix=self._matrix_dict(corr_df.round(4)),
            covariance_matrix=self._matrix_dict(cov_df.round(6)),
        )
        formulas = formulas_subset([
            "retorno_esperado", "volatilidad", "covarianza", "correlacion",
            "sharpe", "min_varianza", "max_sharpe", "risk_parity",
            "frontera_eficiente",
        ])

        return OptimizationResponse(
            base_currency=base_currency,
            risk_profile=risk_profile,
            risk_free_rate=rf,
            as_of=as_of,
            n_assets=len(ordered_symbols),
            recommended=recommended,
            alternatives=alternatives,
            reference_portfolios=references,
            efficient_frontier=frontier,
            calculations=calculations,
            formulas=formulas,
            notes=notes,
        )
