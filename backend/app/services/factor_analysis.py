"""FactorAnalysisService: exposición de la cartera a factores de riesgo.

Construye factores con ETFs proxy (aproximación a Fama-French):
  - MKT (mercado):        SPY
  - SMB (tamaño):         IWM - SPY   (small caps menos mercado)
  - HML (valor):          IWD - IWF   (valor menos growth)
  - BND (bonos/tasas):    AGG
"""
from __future__ import annotations

import math

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.portfolio import RiskProfile
from app.quant.expected import annualized_covariance, historical_expected_returns
from app.quant.factors import factor_regression
from app.quant.optimization import portfolio_for_risk_level
from app.quant.returns import simple_returns
from app.schemas.factors import FactorExposure, FactorProfile, FactorResponse
from app.services.market_data.engine import MarketDataEngine
from app.services.optimizer import (
    RISK_PROFILE_LEVELS,
    InsufficientDataError,
    PortfolioOptimizer,
)

# ETFs proxy que hay que descargar para armar los factores.
_PROXY_TICKERS = ["SPY", "IWM", "IWD", "IWF", "AGG"]

FACTOR_LEGEND = {
    "MKT": "Mercado (SPY): exposición general a acciones de EE.UU.",
    "SMB": "Tamaño (small caps vs mercado): >0 se inclina a empresas chicas.",
    "HML": "Valor vs growth (IWD-IWF): >0 se inclina a acciones 'valor'.",
    "BND": "Bonos (AGG): exposición a renta fija / tasas.",
}


def _clean(value: float) -> float | None:
    if value is None:
        return None
    f = float(value)
    return None if (math.isnan(f) or math.isinf(f)) else f


class FactorAnalysisService:
    def __init__(self, db: Session, engine: MarketDataEngine | None = None) -> None:
        self.db = db
        self.mde = engine or MarketDataEngine(db)
        self.optimizer = PortfolioOptimizer(db, engine=self.mde)

    def _proxy_returns(self, ticker: str) -> pd.Series:
        self.mde.sync_prices(ticker)
        prices = self.mde.get_price_dataframe(ticker)
        if prices.empty:
            return pd.Series(dtype=float)
        return simple_returns(prices["adj_close"])

    def _build_factors(self) -> pd.DataFrame:
        r = {t: self._proxy_returns(t) for t in _PROXY_TICKERS}
        factors: dict[str, pd.Series] = {}
        if not r["SPY"].empty:
            factors["MKT"] = r["SPY"]
        if not r["IWM"].empty and not r["SPY"].empty:
            factors["SMB"] = r["IWM"] - r["SPY"]
        if not r["IWD"].empty and not r["IWF"].empty:
            factors["HML"] = r["IWD"] - r["IWF"]
        if not r["AGG"].empty:
            factors["BND"] = r["AGG"]
        return pd.DataFrame(factors).dropna()

    def _profile(self, symbol: str, name: str | None, returns: pd.Series,
                 factors: pd.DataFrame) -> FactorProfile | None:
        try:
            res = factor_regression(returns, factors)
        except ValueError:
            return None
        exposures = [
            FactorExposure(
                factor=f, beta=round(res.betas[f], 4),
                t_stat=_clean(res.t_stats.get(f)),
            )
            for f in res.factors
        ]
        return FactorProfile(
            symbol=symbol,
            name=name,
            alpha_annualized=_clean(res.alpha_annualized),
            r_squared=_clean(res.r_squared),
            n_obs=res.n_obs,
            exposures=exposures,
        )

    def analyze(
        self,
        symbols: list[str],
        risk_profile: RiskProfile,
        base_currency: str = "USD",
        max_weight: float | None = None,
    ) -> FactorResponse:
        aligned, names, _ = self.optimizer._load_aligned_returns(symbols)
        if len(aligned.columns) < 2:
            raise InsufficientDataError(
                "Se necesitan al menos 2 activos con datos para el análisis de factores."
            )

        ordered = list(aligned.columns)
        mu = historical_expected_returns(aligned).to_numpy()
        cov = annualized_covariance(aligned).to_numpy()
        weights = portfolio_for_risk_level(
            mu, cov, RISK_PROFILE_LEVELS[risk_profile], max_weight
        )
        port_returns = pd.Series(aligned.to_numpy() @ weights, index=aligned.index)

        factors = self._build_factors()
        if factors.empty or len(factors.columns) == 0:
            raise InsufficientDataError(
                "No se pudieron construir los factores (datos de proxies no disponibles)."
            )

        portfolio_profile = self._profile("PORTFOLIO", None, port_returns, factors)
        if portfolio_profile is None:
            raise InsufficientDataError(
                "Muy pocas fechas en común entre la cartera y los factores."
            )

        asset_profiles: list[FactorProfile] = []
        for symbol in ordered:
            asset = self.db.scalar(select(Asset).where(Asset.symbol == symbol))
            asset_returns = simple_returns(
                self.mde.get_price_dataframe(symbol)["adj_close"]
            )
            prof = self._profile(
                symbol, names.get(symbol), asset_returns, factors
            )
            if prof is not None:
                asset_profiles.append(prof)

        notes = [
            "Factores construidos con ETFs proxy (SPY/IWM/IWD/IWF/AGG), una "
            "aproximación a Fama-French. El alfa y las betas son estimaciones "
            "sobre datos históricos.",
        ]

        return FactorResponse(
            base_currency=base_currency,
            risk_profile=risk_profile,
            factors=list(factors.columns),
            factor_legend={k: FACTOR_LEGEND[k] for k in factors.columns},
            portfolio=portfolio_profile,
            assets=asset_profiles,
            notes=notes,
        )
