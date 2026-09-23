"""Schemas Pydantic para `MacroSeries`."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class MacroSeriesBase(BaseModel):
    series_id: str
    description: str | None = None
    date: date
    value: float


class MacroSeriesCreate(MacroSeriesBase):
    """Datos para insertar un punto de una serie macro."""


class MacroSeriesRead(MacroSeriesBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
