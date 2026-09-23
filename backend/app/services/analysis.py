"""PortfolioAnalyzer: une la ingesta de datos con el motor cuantitativo.

Es la capa de servicio que consumen los endpoints. Baja/lee precios,
obtiene la tasa libre de riesgo (FRED) y calcula las métricas por activo
y de la cartera equiponderada de referencia.
"""
from __future__ import annotations

import math

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.quant.correlation import high_correlation_pairs
from app.quant.returns import (
    annualized_return,
    cagr,
    simple_returns,
)
from app.quant.risk import max_drawdown, sharpe_ratio, sortino_ratio
from app.quant.volatility import downside_deviation, volatility
from app.schemas.analysis import (
    AssetMetrics,
    CorrelationAlert,
    EqualWeightPortfolio,
    PortfolioAnalysisResponse,
)
from app.services.market_data.engine import MarketDataEngine
from app.services.market_data.fred import SERIES_10Y_TREASURY


def _clean(value: object) -> float | None:
    """Convierte a float; devuelve None si es NaN/inf/no numérico."""
    if value is None:
        return None
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


class PortfolioAnalyzer:
    def __init__(self, db: Session, engine: MarketDataEngine | None = None) -> None:
        self.db = db
        self.mde = engine or MarketDataEngine(db)

    # -------------------------------------------------------- risk-free rate
    def get_risk_free_rate(self) -> float:
        """Tasa libre de riesgo (Tesoro 10Y de FRED), en decimal.

        Si FRED no está disponible (sin API key, error de red), usa 0.0.
        """
        try:
            self.mde.sync_macro_series(SERIES_10Y_TREASURY)
            df = self.mde.get_macro_dataframe(SERIES_10Y_TREASURY)
            if not df.empty:
                return float(df["value"].iloc[-1]) / 100.0
        except Exception:  # noqa: BLE001 - degradar con elegancia
            pass
        return 0.0

    # --------------------------------------------------------- por activo
    def _asset_metrics(
        self, symbol: str, risk_free_rate: float, full_refresh: bool = False
    ) -> AssetMetrics | None:
        self.mde.sync_prices(symbol, full_refresh=full_refresh)
        prices_df = self.mde.get_price_dataframe(symbol)
        if prices_df.empty:
            return None

        asset = self.db.scalar(select(Asset).where(Asset.symbol == symbol.upper()))
        prices = prices_df["adj_close"]
        rets = simple_returns(prices)

        return AssetMetrics(
            symbol=symbol.upper(),
            name=asset.name if asset else None,
            currency=asset.currency if asset else "USD",
            n_observations=int(len(prices)),
            start_date=prices.index[0],
            end_date=prices.index[-1],
            last_adj_close=_clean(prices.iloc[-1]),
            cagr=_clean(cagr(prices)),
            annualized_volatility=_clean(volatility(rets)),
            downside_deviation=_clean(downside_deviation(rets)),
            max_drawdown=_clean(max_drawdown(rets)),
            sharpe_ratio=_clean(sharpe_ratio(rets, risk_free_rate)),
            sortino_ratio=_clean(sortino_ratio(rets, risk_free_rate)),
        )

    def analyze_symbol(
        self,
        symbol: str,
        risk_free_rate: float | None = None,
        full_refresh: bool = False,
    ) -> AssetMetrics | None:
        if risk_free_rate is None:
            risk_free_rate = self.get_risk_free_rate()
        return self._asset_metrics(symbol, risk_free_rate, full_refresh)

    # --------------------------------------------------------- cartera
    def analyze(
        self, symbols: list[str], base_currency: str = "USD"
    ) -> PortfolioAnalysisResponse:
        rf = self.get_risk_free_rate()
        metrics: list[AssetMetrics] = []
        returns_map: dict[str, pd.Series] = {}

        for symbol in symbols:
            m = self._asset_metrics(symbol, rf)
            if m is None:
                continue
            metrics.append(m)
            prices = self.mde.get_price_dataframe(symbol)["adj_close"]
            returns_map[symbol.upper()] = simple_returns(prices)

        notes: list[str] = []

        # Correlaciones y cartera equiponderada sobre fechas en común.
        corr_dict: dict[str, dict[str, float | None]] = {}
        alerts: list[CorrelationAlert] = []
        equal_weight: EqualWeightPortfolio | None = None

        if returns_map:
            aligned = pd.DataFrame(returns_map).dropna()
            if len(aligned.columns) >= 2 and len(aligned) >= 2:
                corr = aligned.corr()
                corr_dict = {
                    row: {col: _clean(corr.loc[row, col]) for col in corr.columns}
                    for row in corr.index
                }
                alerts = [
                    CorrelationAlert(symbol_a=a, symbol_b=b, correlation=c)
                    for a, b, c in high_correlation_pairs(aligned)
                ]
            if len(aligned.columns) >= 1 and len(aligned) >= 2:
                # Cartera equiponderada: promedio simple de los retornos.
                port_rets = aligned.mean(axis=1)
                equal_weight = EqualWeightPortfolio(
                    n_assets=len(aligned.columns),
                    annualized_return=_clean(annualized_return(port_rets)),
                    annualized_volatility=_clean(volatility(port_rets)),
                    sharpe_ratio=_clean(sharpe_ratio(port_rets, rf)),
                    sortino_ratio=_clean(sortino_ratio(port_rets, rf)),
                    max_drawdown=_clean(max_drawdown(port_rets)),
                )

        # Aviso de riesgo de moneda (FX): pendiente para más adelante.
        currencies = {m.currency for m in metrics}
        if len(currencies) > 1:
            notes.append(
                "Los activos están en distintas monedas "
                f"({', '.join(sorted(currencies))}). En la Fase 1 las métricas "
                "se calculan en la moneda nativa de cada activo; la conversión "
                f"a {base_currency} (riesgo FX) se implementa más adelante."
            )

        as_of = max((m.end_date for m in metrics if m.end_date), default=None)

        return PortfolioAnalysisResponse(
            base_currency=base_currency,
            risk_free_rate=rf,
            as_of=as_of,
            n_assets=len(metrics),
            assets=metrics,
            correlation_matrix=corr_dict,
            high_correlation_alerts=alerts,
            equal_weight_portfolio=equal_weight,
            notes=notes,
        )
