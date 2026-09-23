"""Cálculo de retornos.

Funciones puras sobre `pandas.Series`. Convención:
  - `prices`  : serie de precios (usar cierre ajustado).
  - `returns` : serie de retornos por período (p. ej. diarios).
  - Anualización con 252 días hábiles por defecto.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR: int = 252


def simple_returns(prices: pd.Series) -> pd.Series:
    """Retornos simples: P_t / P_{t-1} - 1."""
    return prices.pct_change().dropna()


def log_returns(prices: pd.Series) -> pd.Series:
    """Retornos logarítmicos: ln(P_t / P_{t-1})."""
    return np.log(prices / prices.shift(1)).dropna()


def total_return(prices: pd.Series) -> float:
    """Retorno acumulado total del período: P_fin / P_ini - 1."""
    p = prices.dropna()
    if len(p) < 2:
        return float("nan")
    return float(p.iloc[-1] / p.iloc[0] - 1.0)


def cumulative_returns(returns: pd.Series) -> pd.Series:
    """Serie de retorno acumulado a partir de retornos por período."""
    return (1.0 + returns).cumprod() - 1.0


def geometric_mean_return(returns: pd.Series) -> float:
    """Media geométrica por período: (Π(1+r))^(1/n) - 1."""
    r = returns.dropna()
    if len(r) == 0:
        return float("nan")
    growth = np.prod(1.0 + r.to_numpy())
    if growth <= 0:
        return float("nan")
    return float(growth ** (1.0 / len(r)) - 1.0)


def annualized_return(
    returns: pd.Series, periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> float:
    """Retorno anualizado (geométrico) a partir de retornos por período."""
    r = returns.dropna()
    if len(r) == 0:
        return float("nan")
    growth = np.prod(1.0 + r.to_numpy())
    if growth <= 0:
        return float("nan")
    return float(growth ** (periods_per_year / len(r)) - 1.0)


def cagr(prices: pd.Series, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    """Tasa de crecimiento anual compuesta a partir de precios.

    Usa la cantidad de períodos entre observaciones para estimar los años.
    """
    p = prices.dropna()
    if len(p) < 2:
        return float("nan")
    n_periods = len(p) - 1
    years = n_periods / periods_per_year
    if years <= 0 or p.iloc[0] <= 0:
        return float("nan")
    return float((p.iloc[-1] / p.iloc[0]) ** (1.0 / years) - 1.0)
