"""Schemas Pydantic para `Portfolio` (inputs mínimos del usuario)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.portfolio import RiskProfile


class PortfolioBase(BaseModel):
    name: str | None = None
    initial_capital: float = Field(gt=0, description="Capital inicial (> 0)")
    monthly_contribution: float = Field(
        default=0.0, ge=0, description="Aporte mensual (>= 0)"
    )
    investment_horizon_years: int = Field(
        gt=0, le=100, description="Horizonte en años (1-100)"
    )
    base_currency: str = "USD"
    risk_profile: RiskProfile
    target_wealth: float | None = Field(
        default=None, gt=0, description="Objetivo de patrimonio final (opcional)"
    )
    custom_asset_universe: list[str] | None = Field(
        default=None, description='Universo opcional, p. ej. ["VOO", "QQQ", "TLT"]'
    )


class PortfolioCreate(PortfolioBase):
    """Datos para crear/analizar una cartera."""


class PortfolioRead(PortfolioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
