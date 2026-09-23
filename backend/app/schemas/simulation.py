"""Schemas de la simulación de Monte Carlo (Fase 4)."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.models.portfolio import RiskProfile
from app.schemas.optimization import OptimizeRequest, ProposedWeight


class SimulateRequest(OptimizeRequest):
    method: Literal["gaussian", "student_t", "bootstrap"] = "gaussian"
    n_simulations: int = Field(default=10_000, ge=100, le=50_000)
    student_t_df: int = Field(default=5, ge=3, le=30, description="Grados de libertad (t-Student).")
    random_seed: int | None = None


class TerminalDistribution(BaseModel):
    p5: float
    p25: float
    p50: float  # mediana (escenario típico)
    p75: float
    p95: float
    mean: float
    prob_reaching_target: float | None = None


class YearBand(BaseModel):
    year: int
    p5: float
    p25: float
    p50: float
    p75: float
    p95: float


class ScenarioImpact(BaseModel):
    name: str
    start: date
    end: date
    portfolio_return: float  # retorno de la cartera en la crisis (negativo = caída)


class SimulationResponse(BaseModel):
    base_currency: str
    risk_profile: RiskProfile
    method: str
    n_simulations: int
    horizon_years: int
    initial_capital: float
    monthly_contribution: float
    total_contributed: float
    expected_annual_return: float
    annual_volatility: float
    weights: list[ProposedWeight]
    terminal: TerminalDistribution
    yearly_bands: list[YearBand]
    historical_scenarios: list[ScenarioImpact]
    notes: list[str] = []
