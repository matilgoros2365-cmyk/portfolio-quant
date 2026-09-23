"""Tests de Black-Litterman."""
from __future__ import annotations

import numpy as np
import pytest

from app.quant.black_litterman import (
    black_litterman_returns,
    implied_equilibrium_returns,
    market_implied_risk_aversion,
)

COV = np.array([[0.04, 0.0], [0.0, 0.16]])


def test_implied_equilibrium_returns() -> None:
    # Π = 3 · Σ · [0.5, 0.5] = 3 · [0.02, 0.08] = [0.06, 0.24]
    pi = implied_equilibrium_returns(COV, np.array([0.5, 0.5]), risk_aversion=3.0)
    assert pi == pytest.approx([0.06, 0.24])


def test_black_litterman_no_views_returns_equilibrium() -> None:
    w = np.array([0.5, 0.5])
    pi = implied_equilibrium_returns(COV, w, 3.0)
    posterior = black_litterman_returns(COV, w, risk_aversion=3.0)
    assert posterior == pytest.approx(pi)


def test_black_litterman_view_pulls_toward_view() -> None:
    w = np.array([0.5, 0.5])
    pi = implied_equilibrium_returns(COV, w, 2.5)
    # View: el activo 1 rendirá 0.20 (mayor que su equilibrio).
    P = np.array([[1.0, 0.0]])
    Q = np.array([0.20])
    posterior = black_litterman_returns(COV, w, risk_aversion=2.5, P=P, Q=Q)
    # El posterior del activo 1 queda entre el equilibrio y la view.
    assert pi[0] < posterior[0] < 0.20


def test_black_litterman_uncertain_view_stays_near_equilibrium() -> None:
    w = np.array([0.5, 0.5])
    pi = implied_equilibrium_returns(COV, w, 2.5)
    P = np.array([[1.0, 0.0]])
    Q = np.array([0.20])
    # View muy incierta (omega enorme) -> apenas mueve el equilibrio.
    omega = np.array([[1e6]])
    posterior = black_litterman_returns(COV, w, 2.5, P=P, Q=Q, omega=omega)
    assert posterior[0] == pytest.approx(pi[0], abs=1e-3)


def test_market_implied_risk_aversion() -> None:
    # (0.08 - 0.02) / 0.03 = 2.0
    assert market_implied_risk_aversion(0.08, 0.03, 0.02) == pytest.approx(2.0)
