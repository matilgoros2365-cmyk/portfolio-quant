"""Simulación de Monte Carlo de la evolución del patrimonio.

Simula la cartera paso a paso (mensual) partiendo del capital inicial y
sumando el aporte mensual. Tres motores:
  - gaussiano:  retornos normales (mu, sigma anuales).
  - t-Student:  colas más gordas (eventos extremos más probables).
  - bootstrap:  remuestrea retornos históricos reales.

Convención: `mu_annual` y `sigma_annual` en decimal (0.10 = 10%).
"""
from __future__ import annotations

import numpy as np

STEPS_PER_YEAR = 12  # pasos mensuales


def _simulate_paths(
    step_returns: np.ndarray, initial: float, contribution: float
) -> np.ndarray:
    """Construye las trayectorias de patrimonio a partir de retornos por paso.

    W_{t+1} = W_t · (1 + r_t) + aporte. Devuelve matriz (n_sims, n_steps+1).
    """
    n_sims, n_steps = step_returns.shape
    paths = np.empty((n_sims, n_steps + 1))
    wealth = np.full(n_sims, float(initial))
    paths[:, 0] = wealth
    for t in range(n_steps):
        wealth = wealth * (1.0 + step_returns[:, t]) + contribution
        paths[:, t + 1] = wealth
    return paths


def simulate_gaussian(
    mu_annual: float,
    sigma_annual: float,
    initial: float,
    monthly_contribution: float,
    years: int,
    n_sims: int = 10_000,
    seed: int | None = None,
    steps_per_year: int = STEPS_PER_YEAR,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n_steps = int(years * steps_per_year)
    mu_step = mu_annual / steps_per_year
    sigma_step = sigma_annual / np.sqrt(steps_per_year)
    step_returns = rng.normal(mu_step, sigma_step, size=(n_sims, n_steps))
    return _simulate_paths(step_returns, initial, monthly_contribution)


def simulate_student_t(
    mu_annual: float,
    sigma_annual: float,
    initial: float,
    monthly_contribution: float,
    years: int,
    n_sims: int = 10_000,
    df: int = 5,
    seed: int | None = None,
    steps_per_year: int = STEPS_PER_YEAR,
) -> np.ndarray:
    """Monte Carlo con t-Student (colas gordas). `df` = grados de libertad."""
    rng = np.random.default_rng(seed)
    n_steps = int(years * steps_per_year)
    mu_step = mu_annual / steps_per_year
    sigma_step = sigma_annual / np.sqrt(steps_per_year)
    # Escalar la t para que su desvío coincida con sigma_step.
    scale = sigma_step / np.sqrt(df / (df - 2)) if df > 2 else sigma_step
    samples = rng.standard_t(df, size=(n_sims, n_steps))
    step_returns = mu_step + scale * samples
    return _simulate_paths(step_returns, initial, monthly_contribution)


def simulate_bootstrap(
    historical_step_returns: np.ndarray,
    initial: float,
    monthly_contribution: float,
    years: int,
    n_sims: int = 10_000,
    seed: int | None = None,
    steps_per_year: int = STEPS_PER_YEAR,
) -> np.ndarray:
    """Monte Carlo por bootstrap: remuestrea retornos históricos (con reemplazo)."""
    hist = np.asarray(historical_step_returns, dtype=float)
    hist = hist[~np.isnan(hist)]
    if len(hist) == 0:
        raise ValueError("No hay retornos históricos para el bootstrap.")
    rng = np.random.default_rng(seed)
    n_steps = int(years * steps_per_year)
    idx = rng.integers(0, len(hist), size=(n_sims, n_steps))
    step_returns = hist[idx]
    return _simulate_paths(step_returns, initial, monthly_contribution)


# ------------------------------------------------------------ resúmenes
def summarize_terminal(paths: np.ndarray, target: float | None = None) -> dict:
    """Distribución del patrimonio final: percentiles, media y prob. de meta."""
    terminal = paths[:, -1]
    p5, p25, p50, p75, p95 = np.percentile(terminal, [5, 25, 50, 75, 95])
    summary = {
        "p5": float(p5),
        "p25": float(p25),
        "p50": float(p50),
        "p75": float(p75),
        "p95": float(p95),
        "mean": float(terminal.mean()),
    }
    if target is not None:
        summary["prob_reaching_target"] = float(np.mean(terminal >= target))
    return summary


def yearly_bands(paths: np.ndarray, steps_per_year: int = STEPS_PER_YEAR) -> list[dict]:
    """Percentiles del patrimonio al cierre de cada año (para graficar bandas)."""
    n_steps = paths.shape[1] - 1
    bands: list[dict] = []
    for year in range(1, n_steps // steps_per_year + 1):
        col = paths[:, year * steps_per_year]
        p5, p25, p50, p75, p95 = np.percentile(col, [5, 25, 50, 75, 95])
        bands.append(
            {
                "year": year,
                "p5": float(p5),
                "p25": float(p25),
                "p50": float(p50),
                "p75": float(p75),
                "p95": float(p95),
            }
        )
    return bands
