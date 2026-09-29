"""Schemas de detalle de activo (precio + qué hay adentro) y mercado argentino."""
from __future__ import annotations

from pydantic import BaseModel


class Quote(BaseModel):
    price: float | None = None
    previous_close: float | None = None
    change_pct: float | None = None
    currency: str = "USD"


class SectorWeight(BaseModel):
    sector: str
    weight: float


class HoldingItem(BaseModel):
    symbol: str
    name: str | None = None
    weight: float


class Composition(BaseModel):
    kind: str
    name: str | None = None
    category: str | None = None
    sector: str | None = None       # acciones individuales
    industry: str | None = None
    country: str | None = None
    summary: str | None = None
    sector_weights: list[SectorWeight] = []
    top_holdings: list[HoldingItem] = []


class AssetDetail(BaseModel):
    symbol: str
    quote: Quote
    composition: Composition


class DollarRate(BaseModel):
    name: str
    buy: float | None = None
    sell: float | None = None


class ArgentinaMarket(BaseModel):
    dollars: list[DollarRate] = []
    merval: Quote | None = None
    source: str
    note: str | None = None
