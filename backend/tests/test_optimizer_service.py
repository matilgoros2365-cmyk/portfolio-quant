"""Test del PortfolioOptimizer con proveedores falsos (sin red)."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.asset import AssetType
from app.models.portfolio import RiskProfile
from app.services.market_data.base import (
    PRICE_COLUMNS,
    AssetMetadata,
    MacroProvider,
    PriceProvider,
)
from app.services.market_data.engine import MarketDataEngine
from app.services.optimizer import InsufficientDataError, PortfolioOptimizer

_N = 80
_DATES = [date(2023, 1, 1) + timedelta(days=i) for i in range(_N)]


def _price_path(seed: int, drift: float, vol: float) -> list[float]:
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, _N - 1)
    prices = [100.0]
    for r in rets:
        prices.append(prices[-1] * (1 + r))
    return prices


class FakePriceProvider(PriceProvider):
    name = "fake"

    _SERIES = {
        "AAA": _price_path(1, 0.0006, 0.010),
        "BBB": _price_path(2, 0.0004, 0.020),
        "CCC": _price_path(3, 0.0002, 0.006),
    }

    def get_historical_prices(self, symbol, start=None, end=None) -> pd.DataFrame:
        prices = self._SERIES.get(symbol.upper(), self._SERIES["AAA"])
        df = pd.DataFrame(
            {
                "open": prices,
                "high": prices,
                "low": prices,
                "close": prices,
                "adj_close": prices,
                "volume": [1000] * len(prices),
            },
            index=_DATES,
        )[PRICE_COLUMNS]
        if start is None:
            return df
        return df[[d >= start for d in df.index]]

    def get_asset_metadata(self, symbol) -> AssetMetadata:
        return AssetMetadata(symbol=symbol.upper(), name=f"Fake {symbol.upper()}",
                             asset_type=AssetType.ETF)


class FakeMacroProvider(MacroProvider):
    name = "fake-macro"

    def get_series(self, series_id, start=None) -> pd.DataFrame:
        df = pd.DataFrame({"value": [4.0] * _N}, index=_DATES)
        if start is None:
            return df
        return df[[d >= start for d in df.index]]


@pytest.fixture()
def optimizer() -> PortfolioOptimizer:
    db_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=db_engine)
    db = Session(bind=db_engine)
    mde = MarketDataEngine(
        db, price_provider=FakePriceProvider(), macro_provider=FakeMacroProvider()
    )
    return PortfolioOptimizer(db, engine=mde)


def test_optimize_returns_valid_recommendation(optimizer: PortfolioOptimizer) -> None:
    resp = optimizer.optimize(["AAA", "BBB", "CCC"], RiskProfile.MODERATE)
    assert resp.n_assets == 3
    assert resp.risk_free_rate == pytest.approx(0.04)
    # Los pesos recomendados suman ~1.
    total = sum(w.weight for w in resp.recommended.weights)
    assert total == pytest.approx(1.0, abs=0.02)
    # Están las 3 carteras de referencia y la frontera.
    assert set(resp.reference_portfolios) == {"min_variance", "max_sharpe", "risk_parity"}
    assert len(resp.efficient_frontier) >= 2


def test_conservative_has_lower_vol_than_aggressive(optimizer: PortfolioOptimizer) -> None:
    cons = optimizer.optimize(["AAA", "BBB", "CCC"], RiskProfile.VERY_CONSERVATIVE)
    aggr = optimizer.optimize(["AAA", "BBB", "CCC"], RiskProfile.VERY_AGGRESSIVE)
    assert cons.recommended.volatility <= aggr.recommended.volatility + 1e-9
    assert cons.recommended.expected_return <= aggr.recommended.expected_return + 1e-9


def test_needs_at_least_two_assets(optimizer: PortfolioOptimizer) -> None:
    with pytest.raises(InsufficientDataError):
        optimizer.optimize(["AAA"], RiskProfile.MODERATE)
