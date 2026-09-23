"""Schemas de respuesta del análisis de carteras (Fase 1).

Los campos numéricos son opcionales: cuando una métrica no está definida
(p. ej. pocos datos) se devuelve `null` en lugar de NaN.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class AssetMetrics(BaseModel):
    """Métricas calculadas para un activo individual."""

    symbol: str
    name: str | None = None
    currency: str = "USD"
    n_observations: int
    start_date: date | None = None
    end_date: date | None = None
    last_adj_close: float | None = None

    cagr: float | None = None
    annualized_volatility: float | None = None
    downside_deviation: float | None = None
    max_drawdown: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None


class CorrelationAlert(BaseModel):
    """Par de activos con correlación alta (diversificación pobre)."""

    symbol_a: str
    symbol_b: str
    correlation: float


class EqualWeightPortfolio(BaseModel):
    """Métricas de la cartera de referencia con pesos iguales.

    En la Fase 1 no optimizamos: mostramos la cartera equiponderada como
    línea de base. La optimización llega en la Fase 2.
    """

    n_assets: int
    annualized_return: float | None = None
    annualized_volatility: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown: float | None = None


class PortfolioAnalysisResponse(BaseModel):
    base_currency: str
    risk_free_rate: float
    as_of: date | None = None
    n_assets: int
    assets: list[AssetMetrics]
    correlation_matrix: dict[str, dict[str, float | None]]
    high_correlation_alerts: list[CorrelationAlert]
    equal_weight_portfolio: EqualWeightPortfolio | None = None
    notes: list[str] = []
