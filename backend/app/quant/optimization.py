"""Optimización de carteras (media-varianza) con cvxpy.

Todas las funciones trabajan con:
  - `mu`  : vector de retornos esperados anualizados (numpy, shape (n,)).
  - `cov` : matriz de covarianza anualizada (numpy, shape (n, n)).

Restricciones por defecto: long-only (w >= 0), pesos suman 1, y un tope
opcional por activo (`max_weight`) para evitar concentración.

Los pesos se devuelven como numpy array (n,). El mapeo peso<->símbolo lo
hace la capa de servicio.
"""
from __future__ import annotations

import math

import cvxpy as cp
import numpy as np


# ------------------------------------------------------------------ helpers
def _clean_weights(weights: np.ndarray | None, tol: float = 1e-5) -> np.ndarray:
    """Limpia ruido numérico: recorta negativos chicos y renormaliza a 1."""
    if weights is None:
        raise OptimizationError("El solver no encontró solución.")
    w = np.asarray(weights, dtype=float).flatten()
    w[np.abs(w) < tol] = 0.0
    w[w < 0] = 0.0
    total = w.sum()
    if total <= 0:
        return np.ones_like(w) / len(w)
    return w / total


class OptimizationError(RuntimeError):
    """Error al resolver un problema de optimización."""


def portfolio_stats(
    weights: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    risk_free_rate: float = 0.0,
) -> dict[str, float]:
    """Retorno esperado, volatilidad y Sharpe de una cartera dada."""
    w = np.asarray(weights, dtype=float)
    ret = float(mu @ w)
    var = float(w @ cov @ w)
    vol = math.sqrt(var) if var > 0 else 0.0
    sharpe = (ret - risk_free_rate) / vol if vol > 0 else float("nan")
    return {"expected_return": ret, "volatility": vol, "sharpe_ratio": sharpe}


# --------------------------------------------------------- carteras óptimas
def _feasible_max_weight(max_weight: float | None, n: int) -> float | None:
    """Relaja el tope por activo si es infactible (debe ser >= 1/n para sumar 1)."""
    if max_weight is None:
        return None
    return max(max_weight, 1.0 / n)


def min_variance_weights(cov: np.ndarray, max_weight: float | None = None) -> np.ndarray:
    """Cartera de mínima varianza."""
    n = cov.shape[0]
    max_weight = _feasible_max_weight(max_weight, n)
    w = cp.Variable(n)
    constraints = [cp.sum(w) == 1, w >= 0]
    if max_weight is not None:
        constraints.append(w <= max_weight)
    prob = cp.Problem(cp.Minimize(cp.quad_form(w, cp.psd_wrap(cov))), constraints)
    prob.solve()
    return _clean_weights(w.value)


def max_sharpe_weights(
    mu: np.ndarray,
    cov: np.ndarray,
    risk_free_rate: float = 0.0,
    max_weight: float | None = None,
) -> np.ndarray:
    """Cartera de máximo Sharpe (tangente).

    Usa la reformulación convexa clásica (variables y, kappa) para poder
    incluir el tope por activo. Si ningún activo supera la tasa libre de
    riesgo, cae a mínima varianza.
    """
    mu = np.asarray(mu, dtype=float)
    n = len(mu)
    max_weight = _feasible_max_weight(max_weight, n)
    excess = mu - risk_free_rate
    if np.all(excess <= 0):
        return min_variance_weights(cov, max_weight)

    y = cp.Variable(n)
    kappa = cp.Variable(nonneg=True)
    constraints = [excess @ y == 1, cp.sum(y) == kappa, y >= 0]
    if max_weight is not None:
        constraints.append(y <= kappa * max_weight)
    prob = cp.Problem(cp.Minimize(cp.quad_form(y, cp.psd_wrap(cov))), constraints)
    prob.solve()

    if y.value is None or kappa.value is None or kappa.value <= 1e-12:
        return min_variance_weights(cov, max_weight)
    return _clean_weights(y.value / kappa.value)


def risk_parity_weights(cov: np.ndarray) -> np.ndarray:
    """Cartera de paridad de riesgo (igual contribución al riesgo).

    Formulación convexa de Spinu: minimizar 1/2·wᵀΣw - (1/n)·Σ log(wᵢ),
    luego normalizar. No admite tope por activo (surge naturalmente).
    """
    n = cov.shape[0]
    w = cp.Variable(n, nonneg=True)
    objective = 0.5 * cp.quad_form(w, cp.psd_wrap(cov)) - (1.0 / n) * cp.sum(cp.log(w))
    prob = cp.Problem(cp.Minimize(objective))
    prob.solve()
    if w.value is None:
        raise OptimizationError("Risk parity no convergió.")
    return _clean_weights(w.value)


def max_return_weights(mu: np.ndarray, max_weight: float | None = None) -> np.ndarray:
    """Cartera de máximo retorno esperado (extremo agresivo de la frontera)."""
    n = len(mu)
    max_weight = _feasible_max_weight(max_weight, n)
    w = cp.Variable(n)
    constraints = [cp.sum(w) == 1, w >= 0]
    if max_weight is not None:
        constraints.append(w <= max_weight)
    prob = cp.Problem(cp.Maximize(np.asarray(mu, dtype=float) @ w), constraints)
    prob.solve()
    return _clean_weights(w.value)


def min_variance_for_target(
    mu: np.ndarray,
    cov: np.ndarray,
    target_return: float,
    max_weight: float | None = None,
) -> np.ndarray | None:
    """Mínima varianza sujeta a un retorno esperado >= target."""
    n = len(mu)
    max_weight = _feasible_max_weight(max_weight, n)
    w = cp.Variable(n)
    constraints = [cp.sum(w) == 1, w >= 0, np.asarray(mu, float) @ w >= target_return]
    if max_weight is not None:
        constraints.append(w <= max_weight)
    prob = cp.Problem(cp.Minimize(cp.quad_form(w, cp.psd_wrap(cov))), constraints)
    prob.solve()
    if w.value is None:
        return None
    return _clean_weights(w.value)


# --------------------------------------------------------- frontera y perfil
def efficient_frontier(
    mu: np.ndarray,
    cov: np.ndarray,
    n_points: int = 20,
    max_weight: float | None = None,
    risk_free_rate: float = 0.0,
) -> list[dict]:
    """Traza la frontera eficiente entre mínima varianza y máximo retorno."""
    mu = np.asarray(mu, dtype=float)
    w_min = min_variance_weights(cov, max_weight)
    w_max = max_return_weights(mu, max_weight)
    r_min = float(mu @ w_min)
    r_max = float(mu @ w_max)

    points: list[dict] = []
    targets = (
        np.linspace(r_min, r_max, n_points) if r_max > r_min else np.array([r_min])
    )
    for target in targets:
        w = min_variance_for_target(mu, cov, float(target), max_weight)
        if w is None:
            continue
        stats = portfolio_stats(w, mu, cov, risk_free_rate)
        stats["weights"] = w
        points.append(stats)
    return points


def portfolio_for_risk_level(
    mu: np.ndarray,
    cov: np.ndarray,
    level: float,
    max_weight: float | None = None,
) -> np.ndarray:
    """Cartera para un nivel de riesgo en [0, 1] sobre la frontera eficiente.

    level=0 -> mínima volatilidad; level=1 -> máximo retorno; intermedios
    interpolan el retorno objetivo y minimizan la varianza para alcanzarlo.
    """
    mu = np.asarray(mu, dtype=float)
    level = min(max(level, 0.0), 1.0)
    w_min = min_variance_weights(cov, max_weight)
    if level == 0.0:
        return w_min
    w_max = max_return_weights(mu, max_weight)
    if level == 1.0:
        return w_max

    r_min = float(mu @ w_min)
    r_max = float(mu @ w_max)
    target = r_min + level * (r_max - r_min)
    w = min_variance_for_target(mu, cov, target, max_weight)
    return w if w is not None else w_min
