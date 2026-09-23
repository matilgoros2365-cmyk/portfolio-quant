"""Métricas de riesgo: drawdown, Sharpe, Sortino, Calmar.

Todas las funciones operan sobre una serie de retornos por período. La
tasa libre de riesgo (`risk_free_rate`) se pasa en términos anuales y en
decimal (p. ej. 0.045 para 4,5%).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.quant.returns import TRADING_DAYS_PER_YEAR, annualized_return
from app.quant.volatility import downside_deviation


def wealth_index(returns: pd.Series, initial: float = 1.0) -> pd.Series:
    """Valor acumulado de 1 unidad invertida: initial · Π(1 + r)."""
    return initial * (1.0 + returns).cumprod()


def drawdown_series(returns: pd.Series) -> pd.Series:
    """Serie 'bajo el agua': caída relativa desde el máximo previo (<= 0)."""
    wealth = (1.0 + returns).cumprod()
    peak = wealth.cummax()
    return wealth / peak - 1.0


def max_drawdown(returns: pd.Series) -> float:
    """Peor caída acumulada (valor negativo, p. ej. -0.35 = -35%)."""
    dd = drawdown_series(returns.dropna())
    if len(dd) == 0:
        return float("nan")
    return float(dd.min())


@dataclass(slots=True)
class DrawdownInfo:
    max_drawdown: float
    peak_date: object | None
    trough_date: object | None
    recovery_date: object | None
    duration_periods: int | None  # de pico a recuperación (None si no recuperó)
    recovered: bool


def max_drawdown_details(returns: pd.Series) -> DrawdownInfo:
    """Detalle del máximo drawdown: pico, valle, recuperación y duración."""
    r = returns.dropna()
    if len(r) == 0:
        return DrawdownInfo(float("nan"), None, None, None, None, False)

    wealth = (1.0 + r).cumprod()
    peak = wealth.cummax()
    dd = wealth / peak - 1.0

    trough_date = dd.idxmin()
    max_dd = float(dd.min())
    trough_pos = wealth.index.get_loc(trough_date)

    # Pico: última fecha antes/igual al valle donde wealth == máximo previo.
    peak_value = float(peak.loc[trough_date])
    before = wealth.iloc[: trough_pos + 1]
    peak_date = before[before >= peak_value].index[0]
    peak_pos = wealth.index.get_loc(peak_date)

    # Recuperación: primera fecha posterior al valle que vuelve al pico.
    after = wealth.iloc[trough_pos:]
    recovered_points = after[after >= peak_value]
    if len(recovered_points) > 0:
        recovery_date = recovered_points.index[0]
        recovery_pos = wealth.index.get_loc(recovery_date)
        duration = int(recovery_pos - peak_pos)
        recovered = True
    else:
        recovery_date = None
        duration = None
        recovered = False

    return DrawdownInfo(
        max_drawdown=max_dd,
        peak_date=peak_date,
        trough_date=trough_date,
        recovery_date=recovery_date,
        duration_periods=duration,
        recovered=recovered,
    )


def sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """Ratio de Sharpe anualizado.

    Sharpe = media(exceso) / desvío(retornos) · sqrt(periods_per_year),
    con exceso = r - rf_por_período.
    """
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    rf_period = risk_free_rate / periods_per_year
    excess = r - rf_period
    sd = float(r.std(ddof=1))
    if sd == 0:
        return float("nan")
    return float(excess.mean() / sd * np.sqrt(periods_per_year))


def sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """Ratio de Sortino anualizado (usa desvío a la baja en el denominador)."""
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    rf_period = risk_free_rate / periods_per_year
    excess = r - rf_period
    dd = downside_deviation(
        excess, mar=0.0, annualize=True, periods_per_year=periods_per_year
    )
    if dd == 0 or np.isnan(dd):
        return float("nan")
    ann_excess = float(excess.mean()) * periods_per_year
    return float(ann_excess / dd)


def calmar_ratio(
    returns: pd.Series, periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> float:
    """Ratio de Calmar: retorno anualizado / |máximo drawdown|."""
    mdd = max_drawdown(returns)
    if np.isnan(mdd) or mdd == 0:
        return float("nan")
    ann = annualized_return(returns, periods_per_year)
    return float(ann / abs(mdd))
