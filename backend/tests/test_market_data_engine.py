"""Tests del MarketDataEngine con proveedores falsos (sin red).

Validan la lógica de ingesta y de caché (no volver a bajar lo existente).
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.asset import AssetType
from app.services.market_data.base import (
    PRICE_COLUMNS,
    AssetMetadata,
    MacroProvider,
    PriceProvider,
)
from app.services.market_data.engine import MarketDataEngine


class FakePriceProvider(PriceProvider):
    """Proveedor de precios controlado, sin red."""

    name = "fake"

    def __init__(self) -> None:
        self.calls: list[date | None] = []

    def get_historical_prices(self, symbol, start=None, end=None) -> pd.DataFrame:
        self.calls.append(start)
        full = pd.DataFrame(
            {
                "open": [10.0, 11.0, 12.0],
                "high": [10.5, 11.5, 12.5],
                "low": [9.5, 10.5, 11.5],
                "close": [10.2, 11.2, 12.2],
                "adj_close": [10.2, 11.2, 12.2],
                "volume": [1000, 1100, 1200],
            },
            index=[date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)],
        )[PRICE_COLUMNS]
        if start is None:
            return full
        return full[[d >= start for d in full.index]]

    def get_asset_metadata(self, symbol) -> AssetMetadata:
        return AssetMetadata(symbol=symbol.upper(), name="Fake", asset_type=AssetType.ETF)


class FakeMacroProvider(MacroProvider):
    name = "fake-macro"

    def get_series(self, series_id, start=None) -> pd.DataFrame:
        full = pd.DataFrame(
            {"value": [3.9, 4.0, 4.1]},
            index=[date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)],
        )
        if start is None:
            return full
        return full[[d >= start for d in full.index]]


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return Session(bind=engine)


def test_sync_prices_creates_asset_and_rows(db: Session) -> None:
    provider = FakePriceProvider()
    eng = MarketDataEngine(db, price_provider=provider)

    inserted = eng.sync_prices("voo")
    assert inserted == 3

    df = eng.get_price_dataframe("VOO")
    assert list(df.index) == [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    assert df["adj_close"].tolist() == [10.2, 11.2, 12.2]


def test_sync_prices_is_idempotent(db: Session) -> None:
    provider = FakePriceProvider()
    eng = MarketDataEngine(db, price_provider=provider)

    assert eng.sync_prices("VOO") == 3
    # Segunda corrida: no debe duplicar nada.
    assert eng.sync_prices("VOO") == 0
    assert len(eng.get_price_dataframe("VOO")) == 3
    # Y la segunda vez pidió incrementalmente (start != None).
    assert provider.calls[0] is None
    assert provider.calls[1] is not None


def test_get_price_dataframe_empty_for_unknown(db: Session) -> None:
    eng = MarketDataEngine(db, price_provider=FakePriceProvider())
    df = eng.get_price_dataframe("NOPE")
    assert df.empty


def test_sync_macro_series(db: Session) -> None:
    eng = MarketDataEngine(db, price_provider=FakePriceProvider(), macro_provider=FakeMacroProvider())
    assert eng.sync_macro_series("DGS10") == 3
    assert eng.sync_macro_series("DGS10") == 0  # idempotente
    df = eng.get_macro_dataframe("DGS10")
    assert df["value"].tolist() == [3.9, 4.0, 4.1]
