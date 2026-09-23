"""Modelo Black-Litterman: retornos esperados más estables.

En vez de usar la media histórica (muy ruidosa), parte de los retornos de
"equilibrio" implícitos en los pesos de mercado (optimización inversa) y,
opcionalmente, los combina con "views" del inversor.

  - Retornos de equilibrio:  Π = δ · Σ · w_mkt
  - Posterior con views:      fórmula estándar de Black-Litterman.

Sin views, el posterior es simplemente Π (el equilibrio), que ya suele dar
carteras más estables que la media histórica.
"""
from __future__ import annotations

import numpy as np


def implied_equilibrium_returns(
    cov: np.ndarray, market_weights: np.ndarray, risk_aversion: float
) -> np.ndarray:
    """Retornos de equilibrio: Π = δ · Σ · w_mkt (optimización inversa)."""
    cov = np.asarray(cov, dtype=float)
    w = np.asarray(market_weights, dtype=float)
    return risk_aversion * (cov @ w)


def black_litterman_returns(
    cov: np.ndarray,
    market_weights: np.ndarray,
    risk_aversion: float = 2.5,
    tau: float = 0.05,
    P: np.ndarray | None = None,
    Q: np.ndarray | None = None,
    omega: np.ndarray | None = None,
) -> np.ndarray:
    """Retornos esperados posteriores de Black-Litterman.

    - `P`, `Q`: matriz de views y sus valores. Si son None, no hay views y
      el posterior es el equilibrio Π.
    - `omega`: incertidumbre de las views. Si None, se deriva de `tau·Σ`.
    """
    cov = np.asarray(cov, dtype=float)
    pi = implied_equilibrium_returns(cov, market_weights, risk_aversion)

    if P is None or Q is None:
        return pi

    P = np.atleast_2d(np.asarray(P, dtype=float))
    Q = np.asarray(Q, dtype=float).reshape(-1)
    tau_cov = tau * cov
    if omega is None:
        omega = np.diag(np.diag(P @ tau_cov @ P.T))
    omega = np.atleast_2d(np.asarray(omega, dtype=float))

    a_inv = np.linalg.inv(tau_cov)
    omega_inv = np.linalg.inv(omega)
    posterior_cov = np.linalg.inv(a_inv + P.T @ omega_inv @ P)
    posterior_mean = posterior_cov @ (a_inv @ pi + P.T @ omega_inv @ Q)
    return posterior_mean


def market_implied_risk_aversion(
    market_return: float, market_variance: float, risk_free_rate: float = 0.0
) -> float:
    """δ = (E[R_mkt] - Rf) / σ²_mkt. Aversión al riesgo implícita del mercado."""
    if market_variance <= 0:
        return 2.5  # valor por defecto razonable
    return float((market_return - risk_free_rate) / market_variance)
