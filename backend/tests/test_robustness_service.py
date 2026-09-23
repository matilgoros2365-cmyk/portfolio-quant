"""Test del RobustnessService con proveedores falsos (sin red)."""
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
from app.services.robustness import RobustnessService

_N = 300
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
def service() -> RobustnessService:
    db_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=db_engine)
    db = Session(bind=db_engine)
    mde = MarketDataEngine(
        db, price_provider=FakePriceProvider(), macro_provider=FakeMacroProvider()
    )
    return RobustnessService(db, engine=mde)


def test_robustness_analysis(service: RobustnessService) -> None:
    resp = service.analyze(
        ["AAA", "BBB", "CCC"], RiskProfile.MODERATE, n_resamples=25, seed=1
    )
    assert resp.n_resamples == 25
    assert 1.0 <= resp.risk_aversion <= 10.0
    assert resp.instability >= 0.0
    assert {e.symbol for e in resp.expected_returns} == {"AAA", "BBB", "CCC"}
    # Cada activo tiene retorno histórico y BL.
    for e in resp.expected_returns:
        assert isinstance(e.historical, float)
        assert isinstance(e.black_litterman, float)
    # Estabilidad reporta los 3 activos.
    assert len(resp.stability) == 3
    total_mean = sum(s.mean_weight for s in resp.stability)
    assert total_mean == pytest.approx(1.0, abs=0.05)
