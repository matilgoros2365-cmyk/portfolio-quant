"""Proveedor de series macro basado en FRED (`fredapi`).

Requiere una API key gratuita (variable de entorno FRED_API_KEY).
Series útiles para esta fase:
  - DGS10    -> Tasa del Tesoro EE.UU. a 10 años (risk-free largo)
  - DGS3MO   -> Tasa del Tesoro a 3 meses (risk-free corto)
  - CPIAUCSL -> Índice de Precios al Consumidor (inflación)
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from app.services.market_data.base import MacroProvider

# Identificadores de series y su descripción legible.
SERIES_10Y_TREASURY = "DGS10"
SERIES_3M_TREASURY = "DGS3MO"
SERIES_CPI = "CPIAUCSL"

SERIES_DESCRIPTIONS: dict[str, str] = {
    SERIES_10Y_TREASURY: "US 10-Year Treasury Yield",
    SERIES_3M_TREASURY: "US 3-Month Treasury Yield",
    SERIES_CPI: "US CPI (All Urban Consumers)",
}


class FredProvider(MacroProvider):
    name = "fred"

    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            raise ValueError(
                "Falta FRED_API_KEY. Conseguí una key gratuita en "
                "https://fredaccount.stlouisfed.org/apikeys y ponela en backend/.env"
            )
        # Import perezoso: solo se necesita fredapi si realmente se usa FRED.
        from fredapi import Fred

        self._fred = Fred(api_key=api_key)

    def get_series(self, series_id: str, start: date | None = None) -> pd.DataFrame:
        series = self._fred.get_series(
            series_id,
            observation_start=start.isoformat() if start else None,
        )
        if series is None or len(series) == 0:
            return pd.DataFrame(columns=["value"])

        df = series.dropna().to_frame(name="value")
        df.index = pd.DatetimeIndex(df.index).date
        df = df.sort_index()
        return df
