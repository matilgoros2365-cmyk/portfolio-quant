"""Tests de riesgo avanzado: VaR/CVaR, contribución, concentración, overlap."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.quant.concentration import (
    concentration_summary,
    effective_number_of_assets,
    herfindahl_index,
    look_through_exposures,
    top_n_concentration,
)
from app.quant.overlap import coverage, overlapping_holdings, weight_overlap
from app.quant.risk import (
    conditional_var_gaussian,
    conditional_var_historical,
    risk_contribution,
    value_at_risk_gaussian,
    value_at_risk_historical,
)


# ----------------------------------------------------------------- VaR/CVaR
def test_var_historical_positive_and_ordering() -> None:
    returns = pd.Series([-0.05, -0.03, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06])
    var = value_at_risk_historical(returns, confidence=0.90)
    cvar = conditional_var_historical(returns, confidence=0.90)
    assert var > 0
    # El CVaR (pérdida media en la cola) es siempre >= VaR.
    assert cvar >= var


def test_var_gaussian_symmetric() -> None:
    returns = pd.Series([-0.02, 0.02, -0.02, 0.02])
    # sigma = 0.02*sqrt(4/3) = 0.0230940 ; z95 = 1.6448536 ; VaR = 0.0379889
    assert value_at_risk_gaussian(returns, confidence=0.95) == pytest.approx(
        0.0379889, rel=1e-4
    )
    # CVaR gaussiano > VaR gaussiano.
    assert conditional_var_gaussian(returns, 0.95) > value_at_risk_gaussian(returns, 0.95)


# -------------------------------------------------------- risk contribution
def test_risk_contribution_sums_to_one() -> None:
    cov = np.array([[0.04, 0.0], [0.0, 0.16]])
    rc = risk_contribution(np.array([0.5, 0.5]), cov)
    # component=[0.01,0.04]; total 0.05 -> [0.2, 0.8]
    assert rc == pytest.approx([0.2, 0.8])
    assert rc.sum() == pytest.approx(1.0)


def test_risk_contribution_risk_parity_is_equal() -> None:
    cov = np.array([[0.04, 0.0], [0.0, 0.16]])
    rc = risk_contribution(np.array([2 / 3, 1 / 3]), cov)
    assert rc == pytest.approx([0.5, 0.5], abs=1e-9)


# --------------------------------------------------------- concentración
def test_herfindahl_and_effective() -> None:
    assert herfindahl_index(np.array([0.5, 0.5])) == pytest.approx(0.5)
    assert effective_number_of_assets(np.array([0.25, 0.25, 0.25, 0.25])) == pytest.approx(
        4.0
    )


def test_top_n_and_summary() -> None:
    w = np.array([0.5, 0.3, 0.2])
    assert top_n_concentration(w, 2) == pytest.approx(0.8)
    summary = concentration_summary(w)
    assert summary["max_weight"] == pytest.approx(0.5)
    assert summary["top3_weight"] == pytest.approx(1.0)


def test_look_through_exposures() -> None:
    portfolio = {"VOO": 0.5, "AAPL": 0.5}
    holdings = {"VOO": {"AAPL": 0.07, "MSFT": 0.06}}
    exposures, cov = look_through_exposures(portfolio, holdings)
    # AAPL: 0.5 directo + 0.5*0.07 vía VOO = 0.535
    assert exposures["AAPL"] == pytest.approx(0.535)
    assert exposures["MSFT"] == pytest.approx(0.03)
    assert exposures["_no_cubierto"] == pytest.approx(0.435)
    assert cov == pytest.approx(0.565)
    assert sum(exposures.values()) == pytest.approx(1.0)


# --------------------------------------------------------- overlap
def test_weight_overlap() -> None:
    a = {"AAPL": 0.07, "MSFT": 0.06, "AMZN": 0.03}
    b = {"AAPL": 0.10, "MSFT": 0.05, "GOOG": 0.04}
    # min(0.07,0.10) + min(0.06,0.05) = 0.07 + 0.05 = 0.12
    assert weight_overlap(a, b) == pytest.approx(0.12)
    rows = overlapping_holdings(a, b)
    assert [r[0] for r in rows] == ["AAPL", "MSFT"]
    assert coverage(a) == pytest.approx(0.16)
