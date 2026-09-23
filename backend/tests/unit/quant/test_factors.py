"""Tests de la regresión de factores con relación exacta (sin ruido)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.quant.factors import factor_regression


def test_factor_regression_exact_relationship() -> None:
    rng = np.random.default_rng(0)
    n = 200
    f1 = rng.normal(0, 0.01, n)
    f2 = rng.normal(0, 0.01, n)
    # y = 0.001 + 1.5*f1 - 0.5*f2 (relación exacta, R²=1)
    y = 0.001 + 1.5 * f1 - 0.5 * f2

    factors = pd.DataFrame({"MKT": f1, "HML": f2})
    result = factor_regression(pd.Series(y), factors, periods_per_year=252)

    assert result.betas["MKT"] == pytest.approx(1.5, abs=1e-6)
    assert result.betas["HML"] == pytest.approx(-0.5, abs=1e-6)
    assert result.alpha_period == pytest.approx(0.001, abs=1e-6)
    assert result.alpha_annualized == pytest.approx(0.001 * 252, abs=1e-4)
    assert result.r_squared == pytest.approx(1.0, abs=1e-9)
    assert result.n_obs == n


def test_factor_regression_beta_one_market() -> None:
    rng = np.random.default_rng(1)
    mkt = rng.normal(0.0004, 0.01, 150)
    # El activo ES el mercado -> beta 1, alfa 0.
    factors = pd.DataFrame({"MKT": mkt})
    result = factor_regression(pd.Series(mkt), factors)
    assert result.betas["MKT"] == pytest.approx(1.0, abs=1e-9)
    assert result.alpha_period == pytest.approx(0.0, abs=1e-9)


def test_factor_regression_too_few_obs_raises() -> None:
    factors = pd.DataFrame({"MKT": [0.01, 0.02]})
    with pytest.raises(ValueError):
        factor_regression(pd.Series([0.01, 0.02]), factors)
