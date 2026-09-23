"""Matrices de correlación / covarianza y detección de pares muy correlacionados."""
from __future__ import annotations

import pandas as pd

from app.quant.returns import TRADING_DAYS_PER_YEAR

# Umbral por defecto para alertar correlaciones altas (diversificación pobre).
HIGH_CORRELATION_THRESHOLD: float = 0.85


def correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """Matriz de correlación de Pearson entre columnas de retornos."""
    return returns_df.corr()


def covariance_matrix(
    returns_df: pd.DataFrame,
    annualize: bool = False,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> pd.DataFrame:
    """Matriz de covarianza. Opcionalmente anualizada (×periods_per_year)."""
    cov = returns_df.cov()
    return cov * periods_per_year if annualize else cov


def high_correlation_pairs(
    returns_df: pd.DataFrame,
    threshold: float = HIGH_CORRELATION_THRESHOLD,
) -> list[tuple[str, str, float]]:
    """Pares de activos con |correlación| >= threshold.

    Devuelve [(activo_a, activo_b, correlación), ...] ordenado de mayor a
    menor correlación absoluta. Útil para alertar falta de diversificación.
    """
    corr = returns_df.corr()
    cols = list(corr.columns)
    pairs: list[tuple[str, str, float]] = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            value = corr.iloc[i, j]
            if pd.notna(value) and abs(value) >= threshold:
                pairs.append((str(cols[i]), str(cols[j]), float(value)))
    pairs.sort(key=lambda item: abs(item[2]), reverse=True)
    return pairs
