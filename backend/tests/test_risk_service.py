"""Test del RiskAnalyzer con proveedores falsos (sin red), incluidas tenencias."""
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
from app.services.risk_analysis import RiskAnalyzer

_N = 80
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
        "CCC": _path(3, 0.0002, 0.006),
    }
    _HOLDINGS = {
        "AAA": {"XXX": {"weight": 0.10, "name": "Empresa X"},
                "YYY": {"weight": 0.08, "name": "Empresa Y"},
                "ZZZ": {"weight": 0.05, "name": "Empresa Z"}},
        "BBB": {"XXX": {"weight": 0.09, "name": "Empresa X"},
                "WWW": {"weight": 0.07, "name": "Empresa W"}},
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

    def get_fund_holdings(self, symbol) -> dict[str, dict]:
        return self._HOLDINGS.get(symbol.upper(), {})


class FakeMacroProvider(MacroProvider):
    name = "fake-macro"

    def get_series(self, series_id, start=None) -> pd.DataFrame:
        df = pd.DataFrame({"value": [4.0] * _N}, index=_DATES)
        if start is None:
            return df
        return df[[d >= start for d in df.index]]


@pytest.fixture()
def analyzer() -> RiskAnalyzer:
    db_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=db_engine)
    db = Session(bind=db_engine)
    mde = MarketDataEngine(
        db, price_provider=FakePriceProvider(), macro_provider=FakeMacroProvider()
    )
    return RiskAnalyzer(db, engine=mde)


def test_risk_analysis_full(analyzer: RiskAnalyzer) -> None:
    resp = analyzer.analyze(["AAA", "BBB", "CCC"], RiskProfile.MODERATE, confidence=0.95)

    # VaR/CVaR presentes y coherentes.
    var = resp.value_at_risk
    assert var.var_historical is not None and var.var_historical >= 0
    assert var.cvar_historical >= var.var_historical
    assert var.cvar_gaussian >= var.var_gaussian

    # Contribución al riesgo suma ~1.
    total_rc = sum(rc.risk_contribution for rc in resp.risk_contributions)
    assert total_rc == pytest.approx(1.0, abs=0.05)

    # Concentración razonable.
    assert 1.0 <= resp.concentration.effective_num_assets <= 3.0

    # Solapamiento: AAA y BBB comparten XXX -> min(0.10, 0.09) = 0.09.
    assert len(resp.etf_overlap) == 1
    ov = resp.etf_overlap[0]
    assert {ov.symbol_a, ov.symbol_b} == {"AAA", "BBB"}
    assert ov.weight_overlap == pytest.approx(0.09, abs=1e-6)

    # Look-through: cobertura > 0 y aparece un subyacente (XXX).
    assert resp.lookthrough_coverage > 0
    assert any(e.symbol == "XXX" for e in resp.lookthrough_top)


def test_risk_analysis_no_holdings_still_works(analyzer: RiskAnalyzer) -> None:
    # CCC no tiene holdings; con solo CCC+AAA igual corre (AAA sí tiene).
    resp = analyzer.analyze(["AAA", "CCC"], RiskProfile.CONSERVATIVE)
    assert resp.n_assets == 2
    assert resp.annualized_volatility > 0
