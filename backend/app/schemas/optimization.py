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
    expected_return: float
    volatility: float
    sharpe_ratio: float | None = None
    weights: list[ProposedWeight]


class FrontierPoint(BaseModel):
    expected_return: float
    volatility: float
    sharpe_ratio: float | None = None


class OptimizationResponse(BaseModel):
    base_currency: str
    risk_profile: RiskProfile
    risk_free_rate: float
    as_of: date | None = None
    n_assets: int
    # Cartera recomendada según el perfil de riesgo.
    recommended: OptimizedPortfolio
    # Carteras clásicas de referencia (mín. varianza, máx. Sharpe, risk parity).
    reference_portfolios: dict[str, OptimizedPortfolio]
    efficient_frontier: list[FrontierPoint]
    notes: list[str] = []
