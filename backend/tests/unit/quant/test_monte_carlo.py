"""Tests de Monte Carlo con casos deterministas (sigma=0) verificables."""
from __future__ import annotations

import numpy as np
import pytest

from app.quant.monte_carlo import (
    simulate_bootstrap,
    simulate_gaussian,
    summarize_terminal,
    yearly_bands,
)


def test_gaussian_zero_vol_zero_return_is_deterministic() -> None:
    # Sin volatilidad ni retorno: patrimonio = inicial + aportes.
    paths = simulate_gaussian(
        mu_annual=0.0, sigma_annual=0.0, initial=1000, monthly_contribution=100,
        years=1, n_sims=50, seed=1,
    )
    terminal = paths[:, -1]
    # 1000 + 100*12 = 2200
    assert terminal == pytest.approx(np.full(50, 2200.0))


def test_gaussian_zero_vol_with_return_all_equal() -> None:
    # Sin volatilidad: todas las trayectorias son idénticas (std ~ 0).
    paths = simulate_gaussian(
        mu_annual=0.12, sigma_annual=0.0, initial=1000, monthly_contribution=0,
        years=1, n_sims=30, seed=2,
    )
    terminal = paths[:, -1]
    assert terminal.std() == pytest.approx(0.0, abs=1e-9)
    # 1000 * (1.01)^12 con mu_step = 0.12/12 = 0.01
    assert terminal[0] == pytest.approx(1000 * (1.01**12), rel=1e-9)


def test_summarize_terminal_and_target_probability() -> None:
    paths = simulate_gaussian(
        mu_annual=0.0, sigma_annual=0.0, initial=1000, monthly_contribution=100,
        years=1, n_sims=100, seed=3,
    )
    # Terminal determinista = 2200.
    s_low = summarize_terminal(paths, target=2000)
    s_high = summarize_terminal(paths, target=3000)
    assert s_low["p50"] == pytest.approx(2200.0)
    assert s_low["prob_reaching_target"] == pytest.approx(1.0)
    assert s_high["prob_reaching_target"] == pytest.approx(0.0)


def test_percentiles_are_ordered() -> None:
    paths = simulate_gaussian(0.08, 0.15, 10000, 500, 10, n_sims=2000, seed=42)
    s = summarize_terminal(paths)
    assert s["p5"] <= s["p25"] <= s["p50"] <= s["p75"] <= s["p95"]


def test_yearly_bands_length() -> None:
    paths = simulate_gaussian(0.08, 0.15, 10000, 0, 5, n_sims=500, seed=7)
    bands = yearly_bands(paths)
    assert [b["year"] for b in bands] == [1, 2, 3, 4, 5]


def test_bootstrap_constant_history_is_deterministic() -> None:
    # Historia con un único retorno 0 -> patrimonio = inicial + aportes.
    paths = simulate_bootstrap(
        np.array([0.0]), initial=1000, monthly_contribution=100, years=1,
        n_sims=20, seed=5,
    )
    assert paths[:, -1] == pytest.approx(np.full(20, 2200.0))


def test_bootstrap_empty_history_raises() -> None:
    with pytest.raises(ValueError):
        simulate_bootstrap(np.array([]), 1000, 100, 1, n_sims=10)
