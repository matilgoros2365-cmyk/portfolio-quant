"""Schemas Pydantic para `DailyPrice`."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class DailyPriceBase(BaseModel):
    date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    adj_close: float
    volume: float | None = None


class DailyPriceCreate(DailyPriceBase):
    asset_id: int


class DailyPriceRead(DailyPriceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
