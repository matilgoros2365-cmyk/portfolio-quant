"""Capa de abstracción de proveedores de datos.

Define interfaces (clases base abstractas) para que el resto del sistema
no dependa de un proveedor concreto. Hoy usamos Yahoo Finance y FRED, pero
mañana se puede sumar Polygon/Alpha Vantage implementando estas mismas
interfaces, sin tocar el motor ni la API.

Contrato de los DataFrame devueltos:
  - Precios: índice = `datetime.date` (ascendente); columnas
    ['open', 'high', 'low', 'close', 'adj_close', 'volume'].
  - Macro:   índice = `datetime.date` (ascendente); columna ['value'].
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

import pandas as pd

from app.models.asset import AssetType

PRICE_COLUMNS = ["open", "high", "low", "close", "adj_close", "volume"]


@dataclass(slots=True)
class AssetMetadata:
    """Metadatos de un activo obtenidos del proveedor."""

    symbol: str
    name: str | None = None
    asset_type: AssetType = AssetType.OTHER
    currency: str = "USD"
    exchange: str | None = None
    sector: str | None = None


class PriceProvider(ABC):
    """Proveedor de precios históricos de activos."""

    name: str = "abstract"

    @abstractmethod
    def get_historical_prices(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        """Devuelve precios diarios en el rango [start, end].

        Si `start` es None, trae todo el historial disponible.
        Debe respetar el contrato de columnas (ver PRICE_COLUMNS) y usar
        `datetime.date` en el índice. Si no hay datos, DataFrame vacío con
        las columnas correctas.
        """

    @abstractmethod
    def get_asset_metadata(self, symbol: str) -> AssetMetadata:
        """Devuelve metadatos del activo (nombre, tipo, moneda, etc.)."""


class MacroProvider(ABC):
    """Proveedor de series macroeconómicas (tasas, inflación, etc.)."""

    name: str = "abstract"

    @abstractmethod
    def get_series(self, series_id: str, start: date | None = None) -> pd.DataFrame:
        """Devuelve una serie temporal con una única columna 'value'."""
