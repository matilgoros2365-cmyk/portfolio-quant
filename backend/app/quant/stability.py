"""Estabilidad de la optimización (remuestreo tipo Michaud).

La optimización media-varianza es famosa por ser inestable: pequeños
cambios en los datos mueven mucho los pesos. Para medirlo, remuestreamos
los retornos (bootstrap), re-optimizamos muchas veces y miramos cuánto
varían los pesos. Poca dispersión = cartera robusta.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.quant.expected import annualized_covariance, historical_expected_returns
from app.quant.optimization import portfolio_for_risk_level


@dataclass(slots=True)
class StabilityResult:
    symbols: list[str]
    mean_weights: np.ndarray  # peso promedio por activo entre remuestreos
    std_weights: np.ndarray   # dispersión del peso por activo
    instability: float        # dispersión media (0 = perfectamente estable)
    n_resamples: int


def resampled_optimization(
    returns_df: pd.DataFrame,
    level: float,
    n_resamples: int = 100,
    max_weight: float | None = None,
    seed: int | None = None,
) -> StabilityResult:
    """Re-optimiza sobre `n_resamples` bootstraps y mide la dispersión de pesos."""
    rng = np.random.default_rng(seed)
    symbols = list(returns_df.columns)
    n = len(returns_df)
    values = returns_df.to_numpy()
    samples: list[np.ndarray] = []

    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        sample = pd.DataFrame(values[idx], columns=symbols)
        mu = historical_expected_returns(sample).to_numpy()
        cov = annualized_covariance(sample).to_numpy()
        weights = portfolio_for_risk_level(mu, cov, level, max_weight)
        samples.append(weights)

    stacked = np.array(samples)
    mean_weights = stacked.mean(axis=0)
    std_weights = stacked.std(axis=0)
    instability = float(std_weights.mean())

    return StabilityResult(
        symbols=symbols,
        mean_weights=mean_weights,
        std_weights=std_weights,
        instability=instability,
        n_resamples=n_resamples,
    )
