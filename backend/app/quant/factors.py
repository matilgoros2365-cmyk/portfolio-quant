"""Análisis de factores: regresión de retornos contra factores de riesgo.

Estima, por mínimos cuadrados (OLS):
  - alfa: retorno que NO explican los factores (habilidad/valor agregado).
  - betas: sensibilidad a cada factor (p. ej. beta de mercado).
  - R²: qué proporción del movimiento explican los factores.

Funciones puras sobre pandas/numpy.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from app.quant.returns import TRADING_DAYS_PER_YEAR


@dataclass(slots=True)
class FactorRegressionResult:
    alpha_period: float                 # alfa por período
    alpha_annualized: float             # alfa anualizado
    betas: dict[str, float]             # beta por factor
    t_stats: dict[str, float]           # t-stat por factor (y 'alpha')
    r_squared: float
    n_obs: int
    factors: list[str] = field(default_factory=list)


def factor_regression(
    returns: pd.Series,
    factors: pd.DataFrame,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> FactorRegressionResult:
    """Regresa `returns` sobre `factors` (con intercepto = alfa).

    Alinea por fechas en común. Devuelve alfa, betas, t-stats y R².
    """
    data = pd.concat([returns.rename("y"), factors], axis=1).dropna()
    if len(data) < len(factors.columns) + 2:
        raise ValueError("Muy pocas observaciones para la regresión de factores.")

    y = data["y"].to_numpy()
    factor_names = list(factors.columns)
    X = data[factor_names].to_numpy()
    n, k = X.shape

    # Matriz de diseño con intercepto.
    design = np.column_stack([np.ones(n), X])
    coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
    alpha = float(coeffs[0])
    betas = {name: float(b) for name, b in zip(factor_names, coeffs[1:])}

    # Bondad de ajuste.
    fitted = design @ coeffs
    residuals = y - fitted
    ss_res = float(residuals @ residuals)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    # t-stats: se = sqrt(diag(sigma² (XᵀX)⁻¹)).
    dof = n - (k + 1)
    t_stats: dict[str, float] = {}
    if dof > 0:
        sigma2 = ss_res / dof
        try:
            xtx_inv = np.linalg.inv(design.T @ design)
            se = np.sqrt(np.diag(sigma2 * xtx_inv))
            names = ["alpha", *factor_names]
            for name, coef, s in zip(names, coeffs, se):
                t_stats[name] = float(coef / s) if s > 0 else float("inf")
        except np.linalg.LinAlgError:
            t_stats = {name: float("nan") for name in ["alpha", *factor_names]}

    return FactorRegressionResult(
        alpha_period=alpha,
        alpha_annualized=alpha * periods_per_year,
        betas=betas,
        t_stats=t_stats,
        r_squared=r_squared,
        n_obs=n,
        factors=factor_names,
    )
