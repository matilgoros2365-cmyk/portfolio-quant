"""Tests del motor de optimización con soluciones analíticas conocidas.

Para dos activos NO correlacionados hay fórmulas cerradas:
  - Mínima varianza: w_i ∝ 1/σ_i²  (proporción inversa a la varianza).
  - Risk parity:     w_i ∝ 1/σ_i   (proporción inversa al desvío).
"""
from __future__ import annotations

import numpy as np
import pytest

from app.quant.optimization import (
    efficient_frontier,
    max_sharpe_weights,
    min_variance_weights,
    portfolio_for_risk_level,
    portfolio_stats,
    risk_parity_weights,
)

# Dos activos independientes: vols 0.2 y 0.4 -> varianzas 0.04 y 0.16.
COV = np.array([[0.04, 0.0], [0.0, 0.16]])
MU = np.array([0.10, 0.20])


def test_min_variance_closed_form() -> None:
    # w1 = σ2²/(σ1²+σ2²) = 0.16/0.20 = 0.8 ; w2 = 0.2
    w = min_variance_weights(COV)
    assert w == pytest.approx([0.8, 0.2], abs=1e-3)


def test_min_variance_respects_max_weight() -> None:
    # Con tope 0.5, el peso de mínima varianza (0.8) queda limitado a 0.5.
    w = min_variance_weights(COV, max_weight=0.5)
    assert w == pytest.approx([0.5, 0.5], abs=1e-3)


def test_risk_parity_closed_form() -> None:
    # w ∝ 1/σ = [1/0.2, 1/0.4] = [5, 2.5] -> normalizado [2/3, 1/3]
    w = risk_parity_weights(COV)
    assert w == pytest.approx([2 / 3, 1 / 3], abs=1e-2)


def test_risk_parity_equal_variances_is_equal_weight() -> None:
    cov = np.array([[0.04, 0.0], [0.0, 0.04]])
    w = risk_parity_weights(cov)
    assert w == pytest.approx([0.5, 0.5], abs=1e-3)


def test_weights_are_valid_simplex() -> None:
    for w in (
        min_variance_weights(COV),
        max_sharpe_weights(MU, COV, risk_free_rate=0.02),
        risk_parity_weights(COV),
    ):
        assert w.sum() == pytest.approx(1.0, abs=1e-4)
        assert (w >= -1e-6).all()


def test_risk_level_extremes() -> None:
    # level 0 -> mínima varianza ; level 1 -> máximo retorno (todo al de mayor mu)
    w0 = portfolio_for_risk_level(MU, COV, 0.0)
    assert w0 == pytest.approx(min_variance_weights(COV), abs=1e-3)

    w1 = portfolio_for_risk_level(MU, COV, 1.0)
    assert w1 == pytest.approx([0.0, 1.0], abs=1e-3)


def test_risk_level_monotonic_return() -> None:
    # A mayor nivel de riesgo, mayor retorno esperado.
    returns = [float(MU @ portfolio_for_risk_level(MU, COV, lvl)) for lvl in (0.0, 0.5, 1.0)]
    assert returns[0] <= returns[1] <= returns[2] + 1e-9


def test_portfolio_stats() -> None:
    stats = portfolio_stats(np.array([1.0, 0.0]), MU, COV, risk_free_rate=0.0)
    assert stats["expected_return"] == pytest.approx(0.10)
    assert stats["volatility"] == pytest.approx(0.20)
    assert stats["sharpe_ratio"] == pytest.approx(0.5)


def test_efficient_frontier_is_ordered() -> None:
    frontier = efficient_frontier(MU, COV, n_points=10)
    assert len(frontier) >= 2
    rets = [p["expected_return"] for p in frontier]
    vols = [p["volatility"] for p in frontier]
    assert rets == sorted(rets)
    assert vols == sorted(vols)  # frontera: más retorno => más riesgo
