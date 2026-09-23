"""Tests de métricas de riesgo con valores calculados a mano."""
from __future__ import annotations

import pandas as pd
import pytest

from app.quant.risk import (
    calmar_ratio,
    max_drawdown,
    max_drawdown_details,
    sharpe_ratio,
    sortino_ratio,
)


def test_max_drawdown() -> None:
    # wealth: 1.5, 0.75, 1.125 ; peak 1.5 ; dd min = 0.75/1.5 - 1 = -0.5
    returns = pd.Series([0.5, -0.5, 0.5])
    assert max_drawdown(returns) == pytest.approx(-0.5)


def test_max_drawdown_details_not_recovered() -> None:
    returns = pd.Series([0.5, -0.5, -0.2, 0.6, 0.3])
    # wealth: 1.5, 0.75, 0.6, 0.96, 1.248 ; dd min = 0.6/1.5-1 = -0.6 en pos 2
    info = max_drawdown_details(returns)
    assert info.max_drawdown == pytest.approx(-0.6)
    assert info.peak_date == 0
    assert info.trough_date == 2
    assert info.recovered is False
    assert info.recovery_date is None
    assert info.duration_periods is None


def test_max_drawdown_details_recovered() -> None:
    returns = pd.Series([0.5, -0.5, 1.5])
    # wealth: 1.5, 0.75, 1.875 ; cae a 0.75 (pos1) y recupera el pico en pos2
    info = max_drawdown_details(returns)
    assert info.max_drawdown == pytest.approx(-0.5)
    assert info.peak_date == 0
    assert info.trough_date == 1
    assert info.recovered is True
    assert info.recovery_date == 2
    assert info.duration_periods == 2


def test_sharpe_ratio() -> None:
    returns = pd.Series([0.02, 0.01, 0.03, 0.02])
    # mean=0.02 ; std muestral=0.00816497 ; sharpe (ppy=1, rf=0)=2.4494897
    result = sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=1)
    assert result == pytest.approx(2.4494897, rel=1e-6)


def test_sortino_ratio() -> None:
    returns = pd.Series([0.02, -0.01, 0.03, -0.02])
    # mean=0.005 ; downside dev=0.0111803 ; sortino (ppy=1)=0.4472136
    result = sortino_ratio(returns, risk_free_rate=0.0, periods_per_year=1)
    assert result == pytest.approx(0.4472136, rel=1e-6)


def test_calmar_ratio() -> None:
    returns = pd.Series([0.5, -0.5, 0.5])
    # annualized (ppy=3): (1.125)^(3/3)-1 = 0.125 ; maxDD=-0.5 ; calmar=0.25
    assert calmar_ratio(returns, periods_per_year=3) == pytest.approx(0.25)
