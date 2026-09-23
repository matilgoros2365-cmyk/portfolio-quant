"""Schemas del análisis de riesgo avanzado (Fase 3)."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.models.portfolio import RiskProfile
from app.schemas.optimization import OptimizeRequest, ProposedWeight


class RiskRequest(OptimizeRequest):
    """Inputs para el análisis de riesgo de la cartera recomendada."""

    confidence_level: float = Field(
        default=0.95, gt=0.5, lt=1.0, description="Nivel de confianza del VaR (0.5-1)."
    )


class ValueAtRisk(BaseModel):
    """VaR y CVaR diarios (pérdidas positivas en fracción)."""

    confidence_level: float
    var_historical: float | None = None
    cvar_historical: float | None = None
    var_gaussian: float | None = None
    cvar_gaussian: float | None = None


class RiskContributionItem(BaseModel):
    symbol: str
    weight: float
    risk_contribution: float  # fracción del riesgo total (suman ~1)


class ConcentrationMetrics(BaseModel):
    herfindahl_index: float
    effective_num_assets: float
    max_weight: float
    top3_weight: float


class ExposureItem(BaseModel):
    symbol: str
    name: str | None = None
    exposure: float


class OverlapItem(BaseModel):
    symbol_a: str
    symbol_b: str
    weight_overlap: float


class RiskAnalysisResponse(BaseModel):
    base_currency: str
    risk_profile: RiskProfile
    as_of: date | None = None
    n_assets: int
    weights: list[ProposedWeight]
    annualized_volatility: float
    value_at_risk: ValueAtRisk
    risk_contributions: list[RiskContributionItem]
    concentration: ConcentrationMetrics
    lookthrough_coverage: float  # fracción de la cartera desagregada en subyacentes
    lookthrough_top: list[ExposureItem]
    etf_overlap: list[OverlapItem]
    notes: list[str] = []
