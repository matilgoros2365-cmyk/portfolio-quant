"""Test del SimulationService con proveedores falsos (sin red)."""
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
from app.services.simulation import SimulationService

_N = 400
_DATES = [date(2023, 1, 1) + timedelta(days=i) for i in range(_N)]


def _path(seed: int, drift: float, vol: float) -> list[float]:
    rng = np.random.default_rng(seed)
    prices = [100.0]
    for r in rng.normal(drift, vol, _N - 1):
        prices.append(prices[-1] * (1 + r))
    return prices


class FakePriceProvider(PriceProvider):
    name = "fake"
    _SERIES = {
        "AAA": _path(1, 0.0006, 0.010),
        "BBB": _path(2, 0.0004, 0.020),
        "CCC": _path(3, 0.0003, 0.006),
    }

    def get_historical_prices(self, symbol, start=None, end=None) -> pd.DataFrame:
        prices = self._SERIES.get(symbol.upper(), self._SERIES["AAA"])
        df = pd.DataFrame(
            {c: prices for c in ("open", "high", "low", "close", "adj_close")}
            | {"volume": [1000] * len(prices)},
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
def service() -> SimulationService:
    db_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=db_engine)
    db = Session(bind=db_engine)
    mde = MarketDataEngine(
        db, price_provider=FakePriceProvider(), macro_provider=FakeMacroProvider()
    )
    return SimulationService(db, engine=mde)


def test_simulate_gaussian(service: SimulationService) -> None:
    resp = service.simulate(
        ["AAA", "BBB", "CCC"], RiskProfile.MODERATE,
        initial_capital=10000, monthly_contribution=500, years=5,
        target_wealth=100000, method="gaussian", n_simulations=2000, seed=1,
    )
    assert resp.method == "gaussian"
    assert resp.total_contributed == pytest.approx(10000 + 500 * 60)
    assert len(resp.yearly_bands) == 5
    t = resp.terminal
    assert t.p5 <= t.p50 <= t.p95
    assert 0.0 <= t.prob_reaching_target <= 1.0
    assert sum(w.weight for w in resp.weights) == pytest.approx(1.0, abs=0.02)
    # Datos ficticios de 2023: las crisis históricas se omiten.
    assert resp.historical_scenarios == []


def test_simulate_bootstrap_runs(service: SimulationService) -> None:
    resp = service.simulate(
        ["AAA", "BBB"], RiskProfile.AGGRESSIVE,
        initial_capital=5000, monthly_contribution=100, years=3,
        target_wealth=None, method="bootstrap", n_simulations=1000, seed=9,
    )
    assert resp.method == "bootstrap"
    assert resp.terminal.prob_reaching_target is None  # sin target
