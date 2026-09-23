"""Retornos esperados y matriz de covarianza para la optimización.

En la Fase 2 usamos el modelo **histórico**: el retorno esperado de cada
activo es su media anualizada y el riesgo, la covarianza anualizada de los
retornos. Modelos más ricos (CAPM, ensemble, Black-Litterman) llegan en
fases posteriores.

Convención: se trabaja con retornos SIMPLES por período (diarios).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.quant.returns import TRADING_DAYS_PER_YEAR


def historical_expected_returns(
    returns_df: pd.DataFrame,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
    method: str = "arithmetic",
) -> pd.Series:
    """Retorno esperado anualizado por activo.

    - "arithmetic": media aritmética × períodos (estándar en media-varianza).
    - "geometric":  (Π(1+r))^(ppy/n) - 1 (compuesto, más conservador).
    """
    if method == "geometric":
        growth = (1.0 + returns_df).prod()
        n = returns_df.count()
        return growth ** (periods_per_year / n) - 1.0
    return returns_df.mean() * periods_per_year


def annualized_covariance(
    returns_df: pd.DataFrame, periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> pd.DataFrame:
    """Matriz de covarianza anualizada (× períodos por año)."""
    return returns_df.cov() * periods_per_year


def align_returns(returns_map: dict[str, pd.Series]) -> pd.DataFrame:
    """Alinea varias series de retornos sobre las fechas en común (dropna)."""
    return pd.DataFrame(returns_map).dropna()
