"""Schemas del análisis de factores (Fase 5)."""
from __future__ import annotations

from pydantic import BaseModel

from app.models.portfolio import RiskProfile
from app.schemas.optimization import OptimizeRequest


class FactorRequest(OptimizeRequest):
    """Inputs para el análisis de factores (usa la cartera del perfil)."""


class FactorExposure(BaseModel):
    factor: str
    beta: float
    t_stat: float | None = None


class FactorProfile(BaseModel):
    symbol: str
    name: str | None = None
    alpha_annualized: float | None = None
    r_squared: float | None = None
    n_obs: int
    exposures: list[FactorExposure]


class FactorResponse(BaseModel):
    base_currency: str
    risk_profile: RiskProfile
    analysis_id: int | None = None
    factors: list[str]
    factor_legend: dict[str, str]
    portfolio: FactorProfile
    assets: list[FactorProfile]
    notes: list[str] = []
