"""Schemas del análisis de robustez: Black-Litterman + estabilidad (Fase 5)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.portfolio import RiskProfile
from app.schemas.optimization import OptimizeRequest, ProposedWeight


class RobustnessRequest(OptimizeRequest):
    n_resamples: int = Field(default=100, ge=20, le=500)
    random_seed: int | None = None


class ExpectedReturnComparison(BaseModel):
    symbol: str
    historical: float          # retorno esperado histórico anualizado
    black_litterman: float     # retorno esperado de equilibrio (BL)


class StabilityItem(BaseModel):
    symbol: str
    recommended_weight: float  # peso de la cartera recomendada (histórico)
    mean_weight: float         # peso promedio entre remuestreos
    std_weight: float          # dispersión del peso (menor = más estable)


class RobustnessResponse(BaseModel):
    base_currency: str
    risk_profile: RiskProfile
    risk_aversion: float
    instability: float         # dispersión media de pesos (0 = perfectamente estable)
    n_resamples: int
    expected_returns: list[ExpectedReturnComparison]
    historical_weights: list[ProposedWeight]
    black_litterman_weights: list[ProposedWeight]
    stability: list[StabilityItem]
    notes: list[str] = []
