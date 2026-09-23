"""Tests de los escenarios de estrés (retornos de ventana)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from app.quant.scenarios import portfolio_scenario_return, window_return


def _series(values: list[float], dates: list[date]) -> pd.Series:
    return pd.Series(values, index=dates)


def test_window_return() -> None:
    dates = [date(2020, 1, 1), date(2020, 1, 15), date(2020, 2, 1)]
    prices = _series([100.0, 90.0, 80.0], dates)
    # 80/100 - 1 = -0.20
    assert window_return(prices, date(2020, 1, 1), date(2020, 2, 1)) == pytest.approx(-0.2)


def test_window_return_none_when_no_data() -> None:
    prices = _series([100.0], [date(2020, 1, 1)])
    assert window_return(prices, date(2019, 1, 1), date(2019, 6, 1)) is None


def test_portfolio_scenario_return_weighted() -> None:
    dates = [date(2008, 1, 1), date(2009, 1, 1)]
    frames = {
        "AAA": _series([100.0, 60.0], dates),   # -40%
        "BBB": _series([100.0, 110.0], dates),  # +10%
    }
    weights = {"AAA": 0.5, "BBB": 0.5}
    ret, coverage = portfolio_scenario_return(
        frames, weights, date(2008, 1, 1), date(2009, 1, 1)
    )
    # 0.5*(-0.4) + 0.5*(0.1) = -0.15 ; cobertura 100%
    assert ret == pytest.approx(-0.15)
    assert coverage == pytest.approx(1.0)


def test_portfolio_scenario_rescales_by_coverage() -> None:
    dates = [date(2008, 1, 1), date(2009, 1, 1)]
    frames = {"AAA": _series([100.0, 60.0], dates)}  # solo un activo con datos
    weights = {"AAA": 0.5, "BBB": 0.5}  # BBB sin datos en la ventana
    ret, coverage = portfolio_scenario_return(
        frames, weights, date(2008, 1, 1), date(2009, 1, 1)
    )
    # Solo AAA cubre (0.5). Reescalado: (0.5*-0.4)/0.5 = -0.40
    assert ret == pytest.approx(-0.40)
    assert coverage == pytest.approx(0.5)
