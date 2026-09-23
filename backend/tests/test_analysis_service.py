"""Test del PortfolioAnalyzer con proveedores falsos (sin red)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.asset import AssetType
from app.services.analysis import PortfolioAnalyzer
from app.services.market_data.base import (
    PRICE_COLUMNS,
    AssetMetadata,
    MacroProvider,
    PriceProvider,
)
from app.services.market_data.engine import MarketDataEngine

_DATES = [date(2024, 1, i) for i in range(2, 12)]  # 10 días hábiles ficticios


class FakePriceProvider(PriceProvider):
    name = "fake"

    # Dos trayectorias de precios distintas por símbolo.
    _SERIES = {
        "AAA": [100, 101, 102, 101, 103, 104, 103, 105, 106, 107],
        "BBB": [50, 49, 51, 52, 50, 53, 54, 52, 55, 56],
    }

    def get_historical_prices(self, symbol, start=None, end=None) -> pd.DataFrame:
        prices = self._SERIES.get(symbol.upper(), self._SERIES["AAA"])
        df = pd.DataFrame(
            {
                "open": prices,
                "high": prices,
                "low": prices,
                "close": prices,
                "adj_close": [float(p) for p in prices],
                "volume": [1000] * len(prices),
            },
            index=_DATES,
        )[PRICE_COLUMNS]
        if start is None:
            return df
        return df[[d >= start for d in df.index]]

    def get_asset_metadata(self, symbol) -> AssetMetadata:
        return AssetMetadata(
            symbol=symbol.upper(), name=f"Fake {symbol.upper()}", asset_type=AssetType.ETF
        )


class FakeMacroProvider(MacroProvider):
    name = "fake-macro"

    def get_series(self, series_id, start=None) -> pd.DataFrame:
        # Tasa 10Y ficticia constante en 4.0 (%).
        df = pd.DataFrame({"value": [4.0] * len(_DATES)}, index=_DATES)
        if start is None:
            return df
        return df[[d >= start for d in df.index]]


@pytest.fixture()
def analyzer() -> PortfolioAnalyzer:
    db_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=db_engine)
    db = Session(bind=db_engine)
    mde = MarketDataEngine(
        db, price_provider=FakePriceProvider(), macro_provider=FakeMacroProvider()
    )
    return PortfolioAnalyzer(db, engine=mde)


def test_risk_free_rate_from_macro(analyzer: PortfolioAnalyzer) -> None:
    # 4.0% -> 0.04 en decimal.
    assert analyzer.get_risk_free_rate() == pytest.approx(0.04)


def test_analyze_symbol(analyzer: PortfolioAnalyzer) -> None:
    m = analyzer.analyze_symbol("AAA")
    assert m is not None
    assert m.symbol == "AAA"
    assert m.n_observations == 10
    assert m.last_adj_close == pytest.approx(107.0)
    assert m.annualized_volatility is not None
    assert m.max_drawdown is not None and m.max_drawdown <= 0


def test_analyze_portfolio(analyzer: PortfolioAnalyzer) -> None:
    resp = analyzer.analyze(["AAA", "BBB"], base_currency="USD")
    assert resp.n_assets == 2
    assert resp.risk_free_rate == pytest.approx(0.04)
    assert {a.symbol for a in resp.assets} == {"AAA", "BBB"}
    # Matriz de correlación 2x2 con diagonal 1.
    assert resp.correlation_matrix["AAA"]["AAA"] == pytest.approx(1.0)
    # Cartera equiponderada calculada.
    assert resp.equal_weight_portfolio is not None
    assert resp.equal_weight_portfolio.n_assets == 2
