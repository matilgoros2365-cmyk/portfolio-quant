"""Escenarios de estrés: crisis históricas reales.

Calcula qué le habría pasado a la cartera (pesos fijos, buy & hold) durante
ventanas de crisis conocidas, usando precios ajustados reales.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

# Ventanas de crisis (pico -> valle aproximados).
HISTORICAL_CRISES: dict[str, tuple[date, date]] = {
    "Burbuja puntocom (2000-2002)": (date(2000, 3, 24), date(2002, 10, 9)),
    "Crisis financiera 2008": (date(2007, 10, 9), date(2009, 3, 9)),
    "Crash COVID-19 (2020)": (date(2020, 2, 19), date(2020, 3, 23)),
    "Mercado bajista 2022": (date(2022, 1, 3), date(2022, 10, 12)),
}


def window_return(prices: pd.Series, start: date, end: date) -> float | None:
    """Retorno de un activo entre `start` y `end` (None si no hay datos)."""
    sub = prices[(prices.index >= start) & (prices.index <= end)]
    if len(sub) < 2:
        return None
    return float(sub.iloc[-1] / sub.iloc[0] - 1.0)


def portfolio_scenario_return(
    price_frames: dict[str, pd.Series],
    weights: dict[str, float],
    start: date,
    end: date,
) -> tuple[float | None, float]:
    """Retorno de la cartera (buy & hold) en la ventana [start, end].

    Devuelve (retorno_ponderado, cobertura), donde cobertura es la fracción
    de la cartera con datos en esa ventana. Si es baja, el número no es
    representativo (activos que todavía no existían).
    """
    total = 0.0
    covered = 0.0
    for symbol, weight in weights.items():
        prices = price_frames.get(symbol)
        if prices is None:
            continue
        r = window_return(prices, start, end)
        if r is None:
            continue
        total += weight * r
        covered += weight
    if covered == 0:
        return None, 0.0
    # Reescalar por la cobertura para no subestimar por activos faltantes.
    return total / covered, covered
