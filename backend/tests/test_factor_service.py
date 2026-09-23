"""Test del FactorAnalysisService con proveedores falsos (sin red)."""
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
from app.services.factor_analysis import FactorAnalysisService
from app.services.market_data.base import (
    PRICE_COLUMNS,
    AssetMetadata,
    PriceProvider,
)
from app.services.market_data.engine import MarketDataEngine

_N = 300
_DATES = [date(2023, 1, 1) + timedelta(days=i) for i in range(_N)]


def _path(seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    prices = [100.0]
    for r in rng.normal(0.0004, 0.012, _N - 1):
        prices.append(prices[-1] * (1 + r))
    return prices


class FakePriceProvider(PriceProvider):
    name = "fake"
    _SERIES = {t: _path(i) for i, t in enumerate(
        ["AAA", "BBB", "SPY", "IWM", "IWD", "IWF", "AGG"], start=1
    )}

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


@pytest.fixture()
def service() -> FactorAnalysisService:
    db_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=db_engine)
    db = Session(bind=db_engine)
    mde = MarketDataEngine(db, price_provider=FakePriceProvider())
    return FactorAnalysisService(db, engine=mde)


def test_factor_analysis(service: FactorAnalysisService) -> None:
    resp = service.analyze(["AAA", "BBB"], RiskProfile.MODERATE)
    assert set(resp.factors) == {"MKT", "SMB", "HML", "BND"}
    assert resp.portfolio.n_obs > 50
    assert len(resp.portfolio.exposures) == 4
    assert {a.symbol for a in resp.assets} == {"AAA", "BBB"}
    # R² es un número válido en [algo, 1].
    assert resp.portfolio.r_squared is not None
