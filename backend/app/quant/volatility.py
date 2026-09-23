"""Cálculo de volatilidad y desvío a la baja (downside deviation)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.quant.returns import TRADING_DAYS_PER_YEAR


def volatility(
    returns: pd.Series,
    annualize: bool = True,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """Desvío estándar de los retornos (muestral, ddof=1).

    Si `annualize=True`, escala por sqrt(periods_per_year).
    """
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    vol = float(r.std(ddof=1))
    return vol * np.sqrt(periods_per_year) if annualize else vol


def downside_deviation(
    returns: pd.Series,
    mar: float = 0.0,
    annualize: bool = True,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """Desvío a la baja respecto de un retorno mínimo aceptable (MAR).

    Solo penaliza los retornos por debajo del MAR:
        sqrt( mean( min(0, r - mar)^2 ) )
    El promedio se toma sobre TODAS las observaciones (convención estándar
    para el ratio de Sortino).
    """
    r = returns.dropna()
    if len(r) == 0:
        return float("nan")
    downside = np.minimum(r.to_numpy() - mar, 0.0)
    dd = float(np.sqrt(np.mean(downside**2)))
    return dd * np.sqrt(periods_per_year) if annualize else dd


def rolling_volatility(
    returns: pd.Series,
    window: int = 21,
    annualize: bool = True,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> pd.Series:
    """Volatilidad móvil (ventana en cantidad de períodos)."""
    vol = returns.rolling(window).std(ddof=1)
    return vol * np.sqrt(periods_per_year) if annualize else vol
