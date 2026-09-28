"""Schemas de la optimización de carteras (Fase 2)."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.models.portfolio import RiskProfile
from app.schemas.portfolio import PortfolioCreate


class OptimizeRequest(PortfolioCreate):
    """Inputs para optimizar: los del portfolio + tope opcional por activo."""

    max_weight: float | None = Field(
        default=None,
        gt=0,
        le=1,
        description="Tope máximo por activo (0-1). Ej: 0.4 = 40% máximo.",
    )


class ProposedWeight(BaseModel):
    symbol: str
    name: str | None = None
    weight: float  # fracción 0-1


class OptimizedPortfolio(BaseModel):
    strategy: str
    label: str | None = None
    expected_return: float
    volatility: float
    sharpe_ratio: float | None = None
    weights: list[ProposedWeight]


class FrontierPoint(BaseModel):
    expected_return: float
    volatility: float
    sharpe_ratio: float | None = None


class OptimizationCalculations(BaseModel):
    """Cálculos intermedios (para revisar/auditar)."""

    risk_free_rate: float
    symbols: list[str]
    expected_returns: dict[str, float]      # anualizado por activo
    volatilities: dict[str, float]          # anualizado por activo
    correlation_matrix: dict[str, dict[str, float | None]]
    covariance_matrix: dict[str, dict[str, float | None]]


class OptimizationResponse(BaseModel):
    base_currency: str
    risk_profile: RiskProfile
    risk_free_rate: float
    as_of: date | None = None
    n_assets: int
    analysis_id: int | None = None
    # Cartera recomendada según el perfil de riesgo.
    recommended: OptimizedPortfolio
    # Alternativas (más conservadora / más agresiva) para comparar.
    alternatives: list[OptimizedPortfolio] = []
    # Carteras clásicas de referencia (mín. varianza, máx. Sharpe, risk parity).
    reference_portfolios: dict[str, OptimizedPortfolio]
    efficient_frontier: list[FrontierPoint]
    calculations: OptimizationCalculations | None = None
    formulas: dict[str, dict[str, str]] = {}
    notes: list[str] = []
