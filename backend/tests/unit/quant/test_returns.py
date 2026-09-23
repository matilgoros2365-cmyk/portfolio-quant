"""Tests de retornos con valores calculados a mano."""
from __future__ import annotations

import math

import pandas as pd
import pytest

from app.quant.returns import (
    annualized_return,
    cagr,
    cumulative_returns,
    geometric_mean_return,
    log_returns,
    simple_returns,
    total_return,
)


def test_simple_returns() -> None:
    prices = pd.Series([100.0, 110.0, 121.0])
    result = simple_returns(prices).tolist()
    assert result == pytest.approx([0.1, 0.1])


def test_log_returns() -> None:
    prices = pd.Series([100.0, 110.0])
    result = log_returns(prices).iloc[0]
    assert result == pytest.approx(math.log(1.1))  # 0.0953101798...


def test_total_return() -> None:
    prices = pd.Series([100.0, 150.0, 121.0])
    assert total_return(prices) == pytest.approx(0.21)


def test_cumulative_returns() -> None:
    returns = pd.Series([0.1, 0.1])
    assert cumulative_returns(returns).tolist() == pytest.approx([0.1, 0.21])


def test_geometric_mean_return() -> None:
    returns = pd.Series([0.1, 0.1])
    # (1.1 * 1.1)^(1/2) - 1 = 0.1
    assert geometric_mean_return(returns) == pytest.approx(0.1)


def test_annualized_return() -> None:
    returns = pd.Series([0.1, 0.1])
    # (1.21)^(2/2) - 1 = 0.21  (con 2 períodos por año)
    assert annualized_return(returns, periods_per_year=2) == pytest.approx(0.21)


def test_cagr() -> None:
    prices = pd.Series([100.0, 110.0, 121.0])
    # 2 períodos, 2 por año => 1 año => (121/100)^1 - 1 = 0.21
    assert cagr(prices, periods_per_year=2) == pytest.approx(0.21)


def test_edge_cases_return_nan() -> None:
    assert math.isnan(total_return(pd.Series([100.0])))
    assert math.isnan(cagr(pd.Series([100.0]), periods_per_year=2))
    assert math.isnan(geometric_mean_return(pd.Series([], dtype=float)))
