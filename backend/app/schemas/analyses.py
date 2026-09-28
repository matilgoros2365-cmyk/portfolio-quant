"""Schemas del historial de análisis guardados."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    created_at: datetime
    risk_profile: str | None = None
    base_currency: str | None = None
    label: str | None = None


class AnalysisDetail(AnalysisSummary):
    inputs: dict
    result: dict
