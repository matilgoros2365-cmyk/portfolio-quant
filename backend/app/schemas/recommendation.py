"""Schema de la recomendación por perfil (perfil -> cartera + alternativas)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas.optimization import OptimizationResponse, ProposedWeight
from app.schemas.simulation import SimulationResponse


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    rationale: str
    risks: str


class ModelPortfolio(ModelInfo):
    """Una cartera alternativa (otro conjunto de activos), con su lógica y riesgos."""

    expected_return: float
    volatility: float
    sharpe_ratio: float | None = None
    weights: list[ProposedWeight]


class GoalReconciliation(BaseModel):
    current_prob: float
    target_prob: float
    needs_action: bool
    achievable_target: float | None = None
    monthly_needed: float | None = None
    extra_per_month: float | None = None
    years_needed: int | None = None
    extra_years: int | None = None


class RecommendationResponse(BaseModel):
    resolved_inputs: dict[str, Any]
    primary_model: ModelInfo               # qué modelo se eligió y por qué
    optimization: OptimizationResponse     # cartera recomendada + frontera
    simulation: SimulationResponse         # proyección + probabilidad del objetivo
    alternatives: list[ModelPortfolio] = []  # otras carteras posibles
    goal_reconciliation: GoalReconciliation | None = None
