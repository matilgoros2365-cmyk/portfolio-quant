"""Tests de volatilidad y downside deviation con valores a mano."""
from __future__ import annotations

import math

import pandas as pd
import pytest

from app.quant.volatility import downside_deviation, volatility


def test_volatility_not_annualized() -> None:
    returns = pd.Series([0.1, -0.1, 0.1, -0.1])
    # media 0; var muestral = 0.04/3; desvío = 0.1154700538...
    assert volatility(returns, annualize=False) == pytest.approx(0.11547005, rel=1e-6)


def test_volatility_annualized() -> None:
    returns = pd.Series([0.1, -0.1, 0.1, -0.1])
    # 0.11547005 * sqrt(4) = 0.2309401
    assert volatility(returns, annualize=True, periods_per_year=4) == pytest.approx(
        0.23094011, rel=1e-6
    )


def test_downside_deviation() -> None:
    returns = pd.Series([0.1, -0.2, 0.1, -0.2])
    # downside = [0, -0.2, 0, -0.2]; mean(sq)=0.08/4=0.02; sqrt=0.14142136
    assert downside_deviation(returns, mar=0.0, annualize=False) == pytest.approx(
        0.14142136, rel=1e-6
    )


def test_downside_deviation_no_downside_is_zero() -> None:
    returns = pd.Series([0.1, 0.2, 0.3])
    assert downside_deviation(returns, mar=0.0, annualize=False) == pytest.approx(0.0)


def test_volatility_single_value_is_nan() -> None:
    assert math.isnan(volatility(pd.Series([0.1])))
