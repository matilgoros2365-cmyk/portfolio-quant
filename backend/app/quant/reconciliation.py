"""Reconciliación del objetivo (Fase 5): palancas concretas y honestas.

Cuando la probabilidad de alcanzar la meta es baja, en vez de subir el riesgo
calculamos qué puede hacer el usuario con lo que SÍ controla:
  - aportar más por mes,
  - darle más años,
  - o ajustar la meta a algo alcanzable.

Todo con Monte Carlo gaussiano (semilla fija -> reproducible/auditable).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.quant.monte_carlo import simulate_gaussian

_SEED = 7
_NSIMS = 5000


def goal_probability(
    mu_annual: float, sigma_annual: float, initial: float, monthly: float,
    years: int, target: float, n_sims: int = _NSIMS, seed: int = _SEED,
) -> float:
    paths = simulate_gaussian(mu_annual, sigma_annual, initial, monthly, years,
                              n_sims=n_sims, seed=seed)
    return float(np.mean(paths[:, -1] >= target))


def achievable_target(
    mu_annual: float, sigma_annual: float, initial: float, monthly: float,
    years: int, prob: float, n_sims: int = _NSIMS, seed: int = _SEED,
) -> float:
    """Meta que se alcanza con probabilidad `prob` (dado el plan actual)."""
    paths = simulate_gaussian(mu_annual, sigma_annual, initial, monthly, years,
                              n_sims=n_sims, seed=seed)
    return float(np.quantile(paths[:, -1], 1.0 - prob))


def required_monthly(
    mu: float, sigma: float, initial: float, monthly: float, years: int,
    target: float, target_prob: float, max_multiple: float = 12.0,
) -> float | None:
    """Aporte mensual mínimo para llegar a `target_prob` (None si no alcanza)."""
    base = max(monthly, 1.0)
    hi = base * max_multiple + target / max(years * 12, 1)
    if goal_probability(mu, sigma, initial, hi, years, target) < target_prob:
        return None
    lo = float(monthly)
    for _ in range(20):
        mid = (lo + hi) / 2
        if goal_probability(mu, sigma, initial, mid, years, target) >= target_prob:
            hi = mid
        else:
            lo = mid
    return round(hi, 2)


def required_years(
    mu: float, sigma: float, initial: float, monthly: float, base_years: int,
    target: float, target_prob: float, max_extra: int = 25,
) -> int | None:
    """Años totales mínimos para llegar a `target_prob` (None si no alcanza)."""
    for extra in range(1, max_extra + 1):
        if goal_probability(mu, sigma, initial, monthly, base_years + extra, target) >= target_prob:
            return base_years + extra
    return None


@dataclass(slots=True)
class Reconciliation:
    current_prob: float
    target_prob: float
    needs_action: bool
    achievable_target: float | None = None
    monthly_needed: float | None = None
    extra_per_month: float | None = None
    years_needed: int | None = None
    extra_years: int | None = None


def reconcile(
    mu_annual: float, sigma_annual: float, initial: float, monthly: float,
    years: int, target: float, target_prob: float,
) -> Reconciliation:
    current = goal_probability(mu_annual, sigma_annual, initial, monthly, years, target)
    if current >= target_prob or target_prob <= 0:
        return Reconciliation(round(current, 4), round(target_prob, 4), needs_action=False)

    monthly_needed = required_monthly(mu_annual, sigma_annual, initial, monthly, years, target, target_prob)
    years_needed = required_years(mu_annual, sigma_annual, initial, monthly, years, target, target_prob)
    achievable = achievable_target(mu_annual, sigma_annual, initial, monthly, years, target_prob)

    return Reconciliation(
        current_prob=round(current, 4),
        target_prob=round(target_prob, 4),
        needs_action=True,
        achievable_target=round(achievable, 2),
        monthly_needed=monthly_needed,
        extra_per_month=round(monthly_needed - monthly, 2) if monthly_needed is not None else None,
        years_needed=years_needed,
        extra_years=(years_needed - years) if years_needed is not None else None,
    )
