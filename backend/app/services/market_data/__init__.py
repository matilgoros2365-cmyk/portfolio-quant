"""Capa de datos de mercado: proveedores + motor de ingesta."""
from app.services.market_data.base import (
    AssetMetadata,
    MacroProvider,
    PriceProvider,
)
from app.services.market_data.engine import MarketDataEngine
from app.services.market_data.fred import (
    SERIES_3M_TREASURY,
    SERIES_10Y_TREASURY,
    SERIES_CPI,
    FredProvider,
)
from app.services.market_data.yahoo import YahooFinanceProvider

__all__ = [
    "AssetMetadata",
    "MacroProvider",
    "PriceProvider",
    "MarketDataEngine",
    "YahooFinanceProvider",
    "FredProvider",
    "SERIES_10Y_TREASURY",
    "SERIES_3M_TREASURY",
    "SERIES_CPI",
]
