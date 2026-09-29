"""Schemas del modo práctica (paper trading)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BuyRequest(BaseModel):
    symbol: str
    amount: float = Field(gt=0, description="Monto a invertir (en la moneda de práctica)")


class SellRequest(BaseModel):
    symbol: str
    amount: float | None = Field(default=None, gt=0)
    all: bool = False  # vender toda la posición


class Allocation(BaseModel):
    symbol: str
    weight: float


class BuyPortfolioRequest(BaseModel):
    allocations: list[Allocation]
    amount: float | None = Field(default=None, gt=0)  # None = usar todo el efectivo


class PositionOut(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    price: float | None
    market_value: float
    cost_basis: float
    pnl: float
    pnl_pct: float | None


class TransactionOut(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float
    amount: float
    created_at: datetime


class PaperSnapshot(BaseModel):
    base_currency: str
    cash: float
    initial_cash: float
    invested: float          # costo de las posiciones
    positions_value: float   # valor de mercado de las posiciones
    total_value: float       # cash + positions_value
    total_return: float      # total_value / initial_cash - 1
    positions: list[PositionOut]
    transactions: list[TransactionOut]


class HistoryPoint(BaseModel):
    date: str
    value: float


class PaperHistory(BaseModel):
    initial_cash: float
    base_currency: str
    points: list[HistoryPoint]
