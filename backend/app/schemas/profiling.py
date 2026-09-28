"""Schemas del perfilado: usuarios, cuestionario y perfil inferido."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# --- Usuarios (perfiles locales) ---
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    avatar_color: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    avatar_color: str | None = None
    created_at: datetime


# --- Cuestionario / perfil ---
class AssessmentCreate(BaseModel):
    # Respuestas categóricas + montos (ej: {"Q3": "y5_10", "Q9": "hold",
    # "initial_capital": 10000, "monthly_contribution": 200, "currency": "USD"}).
    answers: dict[str, Any]


class DimensionOut(BaseModel):
    name: str
    score: float
    confidence: float
    evidence_count: int
    contributions: list[dict]


class ProfileOut(BaseModel):
    risk_level: float
    risk_label: str
    max_weight: float
    techo_capacidad: float
    tolerancia: float
    capacity_binding: bool
    tolerance_binding: bool
    overall_confidence: float
    horizon_years: int | None = None
    mc_contribution_factor: float
    goal_priority: str | None = None
    goal_alarm_prob: float
    exclusions: list[str]
    dimensions: list[DimensionOut]


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: str
    created_at: datetime
    is_current: bool
    answers: dict
    profile: dict
    derived: dict
