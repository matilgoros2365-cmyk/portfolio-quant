"""MarketDataEngine: orquesta la ingesta de datos y usa la DB como caché.

Estrategia de caché (sin Redis en el arranque liviano):
  - Los precios/series ya guardados NO se vuelven a descargar.
  - En cada sync solo se pide al proveedor lo que falta (desde la última
    fecha almacenada en adelante).

El motor recibe los proveedores por inyección, así los tests pueden usar
proveedores falsos sin tocar la red.
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.asset import Asset
from app.models.daily_price import DailyPrice
from app.models.macro_series import MacroSeries
from app.services.market_data.base import MacroProvider, PriceProvider
from app.services.market_data.fred import SERIES_DESCRIPTIONS, FredProvider
from app.services.market_data.yahoo import YahooFinanceProvider


class MarketDataEngine:
    def __init__(
        self,
        db: Session,
        price_provider: PriceProvider | None = None,
        macro_provider: MacroProvider | None = None,
    ) -> None:
        self.db = db
        self.price_provider = price_provider or YahooFinanceProvider()
        # El proveedor macro se crea perezosamente (necesita API key).
        self._macro_provider = macro_provider

    # ---------------------------------------------------------------- macro
    @property
    def macro_provider(self) -> MacroProvider:
        if self._macro_provider is None:
            self._macro_provider = FredProvider(api_key=settings.fred_api_key)
        return self._macro_provider

    # --------------------------------------------------------------- assets
    def get_or_create_asset(self, symbol: str) -> Asset:
        """Devuelve el activo; si no existe, lo crea pidiendo metadatos."""
        symbol = symbol.upper()
        asset = self.db.scalar(select(Asset).where(Asset.symbol == symbol))
        if asset is not None:
            return asset

        meta = self.price_provider.get_asset_metadata(symbol)
        asset = Asset(
            symbol=symbol,
            name=meta.name,
            asset_type=meta.asset_type.value,
            currency=meta.currency,
            exchange=meta.exchange,
            sector=meta.sector,
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    # --------------------------------------------------------------- precios
    def _last_price_date(self, asset_id: int) -> date | None:
        return self.db.scalar(
            select(func.max(DailyPrice.date)).where(DailyPrice.asset_id == asset_id)
        )

    def sync_prices(self, symbol: str, full_refresh: bool = False) -> int:
        """Descarga e inserta los precios que falten. Devuelve cuántos insertó."""
        asset = self.get_or_create_asset(symbol)

        start: date | None = None
        if not full_refresh:
            last = self._last_price_date(asset.id)
            if last is not None:
                start = last + timedelta(days=1)
                if start > date.today():
                    return 0  # ya está al día

        df = self.price_provider.get_historical_prices(symbol, start=start)
        if df.empty:
            return 0

        # Evitar duplicados: qué fechas ya tenemos en el rango descargado.
        existing = set(
            self.db.scalars(
                select(DailyPrice.date).where(
                    DailyPrice.asset_id == asset.id,
                    DailyPrice.date >= df.index.min(),
                )
            ).all()
        )

        rows: list[DailyPrice] = []
        for day, row in df.iterrows():
            if day in existing:
                continue
            rows.append(
                DailyPrice(
                    asset_id=asset.id,
                    date=day,
                    open=_num(row.get("open")),
                    high=_num(row.get("high")),
                    low=_num(row.get("low")),
                    close=_num(row.get("close")),
                    adj_close=float(row["adj_close"]),
                    volume=_num(row.get("volume")),
                )
            )

        if rows:
            self.db.add_all(rows)
            self.db.commit()
        return len(rows)

    def get_price_dataframe(self, symbol: str) -> pd.DataFrame:
        """Lee de la DB los precios de un símbolo como DataFrame ordenado."""
        symbol = symbol.upper()
        asset = self.db.scalar(select(Asset).where(Asset.symbol == symbol))
        if asset is None:
            return pd.DataFrame(columns=["adj_close"])

        rows = self.db.scalars(
            select(DailyPrice)
            .where(DailyPrice.asset_id == asset.id)
            .order_by(DailyPrice.date)
        ).all()
        if not rows:
            return pd.DataFrame(columns=["adj_close"])

        data = {
            "open": [r.open for r in rows],
            "high": [r.high for r in rows],
            "low": [r.low for r in rows],
            "close": [r.close for r in rows],
            "adj_close": [r.adj_close for r in rows],
            "volume": [r.volume for r in rows],
        }
        return pd.DataFrame(data, index=[r.date for r in rows])

    # ----------------------------------------------------------------- macro
    def sync_macro_series(self, series_id: str, full_refresh: bool = False) -> int:
        """Descarga e inserta los puntos que falten de una serie macro."""
        start: date | None = None
        if not full_refresh:
            last = self.db.scalar(
                select(func.max(MacroSeries.date)).where(
                    MacroSeries.series_id == series_id
                )
            )
            if last is not None:
                start = last + timedelta(days=1)
                if start > date.today():
                    return 0

        df = self.macro_provider.get_series(series_id, start=start)
        if df.empty:
            return 0

        existing = set(
            self.db.scalars(
                select(MacroSeries.date).where(
                    MacroSeries.series_id == series_id,
                    MacroSeries.date >= df.index.min(),
                )
            ).all()
        )
        description = SERIES_DESCRIPTIONS.get(series_id)

        rows = [
            MacroSeries(
                series_id=series_id,
                description=description,
                date=day,
                value=float(row["value"]),
            )
            for day, row in df.iterrows()
            if day not in existing
        ]
        if rows:
            self.db.add_all(rows)
            self.db.commit()
        return len(rows)

    def get_macro_dataframe(self, series_id: str) -> pd.DataFrame:
        rows = self.db.scalars(
            select(MacroSeries)
            .where(MacroSeries.series_id == series_id)
            .order_by(MacroSeries.date)
        ).all()
        if not rows:
            return pd.DataFrame(columns=["value"])
        return pd.DataFrame(
            {"value": [r.value for r in rows]}, index=[r.date for r in rows]
        )


def _num(value: object) -> float | None:
    """Convierte a float, tolerando NaN/None."""
    if value is None:
        return None
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f
