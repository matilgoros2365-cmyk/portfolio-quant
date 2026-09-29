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


def test_value_history_empty_without_trades() -> None:
    svc, uid, _ = _setup()
    h = svc.value_history(uid)
    assert h.initial_cash == 100_000.0
    assert h.points == []


def test_value_history_reconstructs_curve() -> None:
    # Motor con histórico falso para reconstruir la curva sin red.
    from datetime import date, timedelta

    import pandas as pd
    from sqlalchemy import create_engine as _ce
    from sqlalchemy.orm import Session as _S

    from app.core.database import Base
    from app.models.asset import AssetType
    from app.services.market_data.base import PRICE_COLUMNS, AssetMetadata, PriceProvider
    from app.services.market_data.engine import MarketDataEngine
    from app.services.profile_service import ProfileService

    N = 20
    dates = [date.today() - timedelta(days=N - 1 - i) for i in range(N)]

    class HistProvider(PriceProvider):
        name = "hist"

        def get_historical_prices(self, symbol, start=None, end=None):
            base = 100.0 if symbol.upper() == "AAA" else 50.0
            prices = [base * (1 + 0.01 * i) for i in range(N)]  # sube 1% por día
            df = pd.DataFrame(
                {c: prices for c in ("open", "high", "low", "close", "adj_close")}
                | {"volume": [1] * N}, index=dates,
            )[PRICE_COLUMNS]
            if start is not None:
                df = df[[d >= start for d in df.index]]
            return df

        def get_asset_metadata(self, symbol):
            return AssetMetadata(symbol=symbol.upper(), name=symbol, asset_type=AssetType.ETF)

        def get_quote(self, symbol):
            return {"price": (100.0 if symbol.upper() == "AAA" else 50.0)}

    eng2 = _ce("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng2)
    db = _S(bind=eng2)
    user = ProfileService(db).create_user("Hist")
    mde = MarketDataEngine(db, price_provider=HistProvider())
    svc = PaperTradingService(db, provider=HistProvider())
    svc.buy(user.id, "AAA", 1000)  # 10 unidades a 100
    h = svc.value_history(user.id, engine=mde)
    # Comprando "hoy", la curva arranca hoy (1 punto); crece a medida que pasan días.
    assert len(h.points) >= 1
    # Valor reconstruido correcto: 99.000 efectivo + 10 unidades al precio actual (~119).
    assert h.points[-1].value == pytest.approx(100_190.0, abs=1.0)
