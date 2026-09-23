"""Test de humo de la Tarea 1: la base se crea y los modelos funcionan.

No valida matemática (eso es la Tarea 4); solo confirma que el esquema
y el ORM están bien cableados. Usa una base SQLite en memoria.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Asset, AssetType, DailyPrice, MacroSeries, Portfolio, RiskProfile


def _in_memory_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return Session(bind=engine)


def test_create_all_tables_registers_four_tables() -> None:
    expected = {"assets", "daily_prices", "macro_series", "portfolios"}
    assert expected.issubset(set(Base.metadata.tables.keys()))


def test_asset_with_prices_roundtrip() -> None:
    session = _in_memory_session()
    asset = Asset(symbol="VOO", name="Vanguard S&P 500", asset_type=AssetType.ETF.value)
    asset.prices.append(DailyPrice(date=date(2024, 1, 2), adj_close=430.5))
    asset.prices.append(DailyPrice(date=date(2024, 1, 3), adj_close=432.1))
    session.add(asset)
    session.commit()

    loaded = session.scalar(select(Asset).where(Asset.symbol == "VOO"))
    assert loaded is not None
    assert loaded.id is not None
    assert loaded.created_at is not None  # el mixin puso el timestamp
    assert len(loaded.prices) == 2
    assert loaded.prices[0].adj_close == 430.5


def test_macro_series_roundtrip() -> None:
    session = _in_memory_session()
    session.add(
        MacroSeries(
            series_id="DGS10",
            description="US 10Y Treasury",
            date=date(2024, 1, 2),
            value=3.95,
        )
    )
    session.commit()
    row = session.scalar(select(MacroSeries).where(MacroSeries.series_id == "DGS10"))
    assert row is not None
    assert row.value == 3.95


def test_portfolio_roundtrip() -> None:
    session = _in_memory_session()
    p = Portfolio(
        name="Mi cartera",
        initial_capital=50000,
        monthly_contribution=1000,
        investment_horizon_years=10,
        base_currency="USD",
        risk_profile=RiskProfile.MODERATE.value,
        target_wealth=250000,
        custom_asset_universe=["VOO", "QQQ", "TLT", "GLD"],
    )
    session.add(p)
    session.commit()

    loaded = session.scalar(select(Portfolio))
    assert loaded is not None
    assert loaded.initial_capital == 50000
    assert loaded.custom_asset_universe == ["VOO", "QQQ", "TLT", "GLD"]
