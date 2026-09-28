"""Schema de la recomendación por perfil (perfil -> cartera)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas.optimization import OptimizationResponse
from app.schemas.simulation import SimulationResponse


class RecommendationResponse(BaseModel):
    resolved_inputs: dict[str, Any]     # universo, nivel, capital, etc. derivados del perfil
    optimization: OptimizationResponse  # cartera recomendada + alternativas + frontera
    simulation: SimulationResponse      # proyección + probabilidad del objetivo
