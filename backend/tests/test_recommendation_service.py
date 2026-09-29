"""Test del RecommendationService (perfil -> cartera) con proveedores falsos."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
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
from app.services.profile_service import ProfileService
from app.services.recommendation import RecommendationService

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
        "VT": _path(1, 0.0005, 0.011),
        "VOO": _path(2, 0.0006, 0.012),
        "QQQ": _path(3, 0.0007, 0.016),
        "BND": _path(4, 0.0002, 0.004),
        "TLT": _path(5, 0.0002, 0.009),
        "GLD": _path(6, 0.0003, 0.008),
        "ARGT": _path(7, 0.0004, 0.020),
    }

    def get_historical_prices(self, symbol, start=None, end=None) -> pd.DataFrame:
        prices = self._SERIES.get(symbol.upper(), self._SERIES["VT"])
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
def db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return Session(bind=engine)


def test_recommend_from_profile(db: Session) -> None:
    svc = ProfileService(db)
    user = svc.create_user("Matilda")
    assessment = svc.create_assessment(user.id, {
        "Q3": "gt_10", "Q4": "other_savings", "Q5": "several_months",
        "Q9": "hold", "Q10": "at_20", "Q8": "fairly_sure",
        "currency": "USD", "initial_capital": 50000, "monthly_contribution": 1000,
        "target_wealth": 250000, "Q1": "grow",
    })

    mde = MarketDataEngine(db, price_provider=FakePriceProvider(),
                           macro_provider=FakeMacroProvider())
    result = RecommendationService(db, engine=mde).recommend(
        user.id, assessment, n_simulations=2000
    )

    inp = result["resolved_inputs"]
    # Perfil agresivo con objetivo "grow" -> modelo de crecimiento (no siempre el mismo).
    assert result["primary_model"].id == "growth_tech"
    assert inp["symbols"] == ["QQQ", "VOO", "GLD"]
    assert inp["monthly_contribution"] == 900.0  # haircut 0.9 aplicado
    assert inp["investment_horizon_years"] == 15

    opt = result["optimization"]
    assert opt.analysis_id is not None
    assert abs(sum(w.weight for w in opt.recommended.weights) - 1.0) < 0.02

    sim = result["simulation"]
    assert sim.analysis_id is not None
    assert sim.terminal.prob_reaching_target is not None

    # Ofrece alternativas (otros modelos de cartera) con su lógica y riesgos.
    assert len(result["alternatives"]) >= 2
    alt = result["alternatives"][0]
    assert alt.rationale and alt.risks
    assert abs(sum(w.weight for w in alt.weights) - 1.0) < 0.02

    # Los análisis (primario) quedan asociados al usuario.
    from app.models.analysis_run import AnalysisRun
    from sqlalchemy import select
    runs = db.scalars(select(AnalysisRun).where(AnalysisRun.user_id == user.id)).all()
    assert len(runs) == 2
