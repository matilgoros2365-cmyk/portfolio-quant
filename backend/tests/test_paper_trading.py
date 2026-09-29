"""Tests del modo práctica (paper trading) con precios falsos."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.services.paper_trading import PaperError, PaperTradingService
from app.services.profile_service import ProfileService


class FakeQuoteProvider:
    def __init__(self) -> None:
        self.prices = {"AAPL": 100.0, "MSFT": 200.0, "BTC-USD": 50000.0}

    def get_quote(self, symbol: str) -> dict:
        return {"price": self.prices.get(symbol.upper())}


def _setup():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    db = Session(bind=engine)
    user = ProfileService(db).create_user("Player")
    provider = FakeQuoteProvider()
    svc = PaperTradingService(db, provider=provider)
    return svc, user.id, provider


def test_starts_with_100k() -> None:
    svc, uid, _ = _setup()
    snap = svc.snapshot(uid)
    assert snap.cash == 100_000.0
    assert snap.total_value == 100_000.0
    assert snap.total_return == 0.0
    assert snap.positions == []


def test_buy_and_average_cost() -> None:
    svc, uid, _ = _setup()
    svc.buy(uid, "AAPL", 1000)   # 10 acciones a 100
    svc.buy(uid, "AAPL", 1000)   # otras 10 a 100
    snap = svc.snapshot(uid)
    pos = snap.positions[0]
    assert pos.symbol == "AAPL"
    assert pos.quantity == pytest.approx(20.0)
    assert pos.avg_cost == pytest.approx(100.0)
    assert snap.cash == pytest.approx(98_000.0)
    assert snap.positions_value == pytest.approx(2000.0)


def test_pnl_moves_with_price() -> None:
    svc, uid, provider = _setup()
    svc.buy(uid, "AAPL", 1000)   # 10 a 100
    provider.prices["AAPL"] = 130.0  # +30%
    snap = svc.snapshot(uid)
    pos = snap.positions[0]
    assert pos.market_value == pytest.approx(1300.0)
    assert pos.pnl == pytest.approx(300.0)
    assert pos.pnl_pct == pytest.approx(0.30)
    assert snap.total_value == pytest.approx(100_300.0)
    assert snap.total_return == pytest.approx(0.003)


def test_insufficient_funds() -> None:
    svc, uid, _ = _setup()
    with pytest.raises(PaperError):
        svc.buy(uid, "AAPL", 200_000)


def test_unknown_symbol() -> None:
    svc, uid, _ = _setup()
    with pytest.raises(PaperError):
        svc.buy(uid, "NOEXISTE", 100)


def test_sell_all_returns_cash() -> None:
    svc, uid, provider = _setup()
    svc.buy(uid, "AAPL", 1000)
    provider.prices["AAPL"] = 120.0
    svc.sell(uid, "AAPL", sell_all=True)
    snap = svc.snapshot(uid)
    assert snap.positions == []
    assert snap.cash == pytest.approx(100_200.0)  # 99000 + 10*120


def test_buy_portfolio_splits_by_weight() -> None:
    svc, uid, _ = _setup()
    svc.buy_portfolio(uid, [{"symbol": "AAPL", "weight": 0.5}, {"symbol": "MSFT", "weight": 0.5}], amount=10_000)
    snap = svc.snapshot(uid)
    syms = {p.symbol: p for p in snap.positions}
    assert syms["AAPL"].cost_basis == pytest.approx(5000.0)
    assert syms["MSFT"].cost_basis == pytest.approx(5000.0)


def test_reset() -> None:
    svc, uid, _ = _setup()
    svc.buy(uid, "BTC-USD", 5000)
    svc.reset(uid)
    snap = svc.snapshot(uid)
    assert snap.cash == 100_000.0
    assert snap.positions == []
