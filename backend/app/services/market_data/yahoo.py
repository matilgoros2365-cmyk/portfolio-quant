"""Proveedor de precios basado en Yahoo Finance (`yfinance`).

No requiere API key. Los precios se piden con `auto_adjust=False` para
quedarnos tanto con el cierre crudo (`close`) como con el cierre ajustado
por dividendos y splits (`adj_close`), que es el que usa el motor quant.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

from app.models.asset import AssetType
from app.services.market_data.base import (
    PRICE_COLUMNS,
    AssetMetadata,
    PriceProvider,
)

# Mapeo del "quoteType" de Yahoo a nuestra clasificación interna.
_QUOTE_TYPE_MAP: dict[str, AssetType] = {
    "EQUITY": AssetType.EQUITY,
    "ETF": AssetType.ETF,
    "INDEX": AssetType.INDEX,
    "MUTUALFUND": AssetType.OTHER,
    "CURRENCY": AssetType.OTHER,
    "CRYPTOCURRENCY": AssetType.CRYPTO,
    "FUTURE": AssetType.COMMODITY,
}


class YahooFinanceProvider(PriceProvider):
    name = "yahoo"

    def get_historical_prices(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        if start is not None:
            raw = ticker.history(
                start=start.isoformat(),
                end=end.isoformat() if end else None,
                auto_adjust=False,
                actions=False,
            )
        else:
            raw = ticker.history(period="max", auto_adjust=False, actions=False)

        if raw is None or raw.empty:
            return pd.DataFrame(columns=PRICE_COLUMNS)

        df = raw.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )
        # Algunos instrumentos (índices) no traen 'Adj Close': usar 'close'.
        if "adj_close" not in df.columns:
            df["adj_close"] = df["close"]

        # Índice tz-aware -> datetime.date puro.
        df.index = pd.DatetimeIndex(df.index).tz_localize(None).date

        df = df.reindex(columns=PRICE_COLUMNS)
        df = df.dropna(subset=["adj_close"])
        df = df.sort_index()
        return df

    def get_asset_metadata(self, symbol: str) -> AssetMetadata:
        ticker = yf.Ticker(symbol)
        info: dict = {}
        try:
            info = ticker.info or {}
        except Exception:  # noqa: BLE001 - .info puede fallar/rate-limit
            info = {}

        quote_type = str(info.get("quoteType", "")).upper()
        return AssetMetadata(
            symbol=symbol.upper(),
            name=info.get("longName") or info.get("shortName"),
            asset_type=_QUOTE_TYPE_MAP.get(quote_type, AssetType.OTHER),
            currency=info.get("currency") or "USD",
            exchange=info.get("exchange"),
            sector=info.get("sector"),
        )

    def get_fund_holdings(self, symbol: str) -> dict[str, dict]:
        """Principales tenencias de un ETF/fondo.

        Devuelve {símbolo: {"weight": fracción, "name": str|None}}.
        Con datos gratuitos solo están las top-N; si el activo no es un
        fondo o no hay datos, devuelve {} (no es un error).
        """
        ticker = yf.Ticker(symbol)
        try:
            funds = ticker.funds_data
            top = funds.top_holdings
        except Exception:  # noqa: BLE001 - puede no ser fondo / rate-limit
            return {}

        if top is None or len(top) == 0:
            return {}

        result: dict[str, dict] = {}
        for holding_symbol, row in top.iterrows():
            pct = row.get("Holding Percent")
            if pct is None:
                continue
            try:
                weight = float(pct)
            except (TypeError, ValueError):
                continue
            name = row.get("Name")
            result[str(holding_symbol).upper()] = {
                "weight": weight,
                "name": str(name) if name is not None else None,
            }
        return result
