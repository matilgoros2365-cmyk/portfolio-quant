"""Paquete de schemas Pydantic (contratos de entrada/salida de la API)."""
from app.schemas.asset import AssetBase, AssetCreate, AssetRead
from app.schemas.daily_price import (
    DailyPriceBase,
    DailyPriceCreate,
    DailyPriceRead,
)
from app.schemas.macro_series import (
    MacroSeriesBase,
    MacroSeriesCreate,
    MacroSeriesRead,
)
from app.schemas.portfolio import (
    PortfolioBase,
    PortfolioCreate,
    PortfolioRead,
)

__all__ = [
    "AssetBase",
    "AssetCreate",
    "AssetRead",
    "DailyPriceBase",
    "DailyPriceCreate",
    "DailyPriceRead",
    "MacroSeriesBase",
    "MacroSeriesCreate",
    "MacroSeriesRead",
    "PortfolioBase",
    "PortfolioCreate",
    "PortfolioRead",
]
