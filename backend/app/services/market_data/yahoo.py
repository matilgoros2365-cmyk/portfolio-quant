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

# Traducción de sectores de Yahoo a español.
_SECTOR_ES: dict[str, str] = {
    "technology": "Tecnología",
    "financial_services": "Servicios financieros",
    "financial": "Financiero",
    "healthcare": "Salud",
    "consumer_cyclical": "Consumo discrecional",
    "consumer_defensive": "Consumo básico",
    "communication_services": "Comunicaciones",
    "industrials": "Industria",
    "energy": "Energía",
    "utilities": "Servicios públicos",
    "real_estate": "Inmobiliario",
    "realestate": "Inmobiliario",
    "basic_materials": "Materiales",
}


def _sector_es(code: str) -> str:
    return _SECTOR_ES.get(code.lower().replace(" ", "_"), code.replace("_", " ").title())


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

    def get_quote(self, symbol: str) -> dict:
        """Último precio (diferido ~15 min) del activo."""
        ticker = yf.Ticker(symbol)
        price = prev = currency = None
        try:
            fi = ticker.fast_info
            price = getattr(fi, "last_price", None)
            prev = getattr(fi, "previous_close", None)
            currency = getattr(fi, "currency", None)
        except Exception:  # noqa: BLE001
            pass
        if price is None:
            try:
                hist = ticker.history(period="5d", auto_adjust=False)
                if hist is not None and not hist.empty:
                    price = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else None
            except Exception:  # noqa: BLE001
                pass
        change = None
        if price is not None and prev:
            try:
                change = float(price) / float(prev) - 1.0
            except (TypeError, ZeroDivisionError):
                change = None
        return {
            "price": float(price) if price is not None else None,
            "previous_close": float(prev) if prev is not None else None,
            "change_pct": change,
            "currency": currency or "USD",
        }

    def get_composition(self, symbol: str) -> dict:
        """Qué hay adentro: rubro, sectores y principales tenencias (o empresa)."""
        ticker = yf.Ticker(symbol)
        info: dict = {}
        try:
            info = ticker.info or {}
        except Exception:  # noqa: BLE001
            info = {}

        quote_type = str(info.get("quoteType", "")).upper()
        name = info.get("longName") or info.get("shortName")
        summary = info.get("longBusinessSummary")

        sector_weights: list[dict] = []
        top_holdings: list[dict] = []
        category = info.get("category")

        # Fondos/ETF: sectores + tenencias principales.
        try:
            funds = ticker.funds_data
            weightings = getattr(funds, "sector_weightings", None) or {}
            for code, w in weightings.items():
                try:
                    sector_weights.append({"sector": _sector_es(str(code)), "weight": float(w)})
                except (TypeError, ValueError):
                    continue
            sector_weights.sort(key=lambda x: x["weight"], reverse=True)

            top = getattr(funds, "top_holdings", None)
            if top is not None and len(top) > 0:
                for hsym, row in top.iterrows():
                    pct = row.get("Holding Percent")
                    if pct is None:
                        continue
                    top_holdings.append({
                        "symbol": str(hsym).upper(),
                        "name": str(row.get("Name")) if row.get("Name") is not None else None,
                        "weight": float(pct),
                    })
        except Exception:  # noqa: BLE001 - no es fondo o sin datos
            pass

        return {
            "kind": _QUOTE_TYPE_MAP.get(quote_type, AssetType.OTHER).value,
            "name": name,
            "category": category,
            "sector": info.get("sector"),      # para acciones individuales
            "industry": info.get("industry"),
            "country": info.get("country"),
            "summary": summary[:400] if isinstance(summary, str) else None,
            "sector_weights": sector_weights[:8],
            "top_holdings": top_holdings,
        }

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
