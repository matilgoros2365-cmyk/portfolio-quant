"""Tests de la reconciliación del objetivo (palancas)."""
from __future__ import annotations

from app.quant.reconciliation import (
    achievable_target,
    goal_probability,
    reconcile,
)

MU, SIGMA = 0.08, 0.15
INITIAL, MONTHLY, YEARS = 10000.0, 100.0, 10


def test_goal_probability_increases_with_contribution() -> None:
    low = goal_probability(MU, SIGMA, INITIAL, 50, YEARS, 60000)
    high = goal_probability(MU, SIGMA, INITIAL, 1000, YEARS, 60000)
    assert 0.0 <= low <= 1.0
    assert high >= low


def test_achievable_target_higher_prob_means_lower_target() -> None:
    # Pedir más probabilidad -> la meta alcanzable es más baja.
    at_50 = achievable_target(MU, SIGMA, INITIAL, MONTHLY, YEARS, 0.50)
    at_90 = achievable_target(MU, SIGMA, INITIAL, MONTHLY, YEARS, 0.90)
    assert at_90 < at_50


def test_reconcile_easy_target_no_action() -> None:
    r = reconcile(MU, SIGMA, INITIAL, MONTHLY, YEARS, target=1000.0, target_prob=0.7)
    assert r.needs_action is False
    assert r.current_prob >= 0.7


def test_reconcile_hard_target_gives_levers() -> None:
    r = reconcile(MU, SIGMA, INITIAL, MONTHLY, YEARS, target=1_000_000.0, target_prob=0.7)
    assert r.needs_action is True
    assert r.current_prob < 0.7
    # Siempre puede decir a qué meta sí se llega con 70% de probabilidad.
    assert r.achievable_target is not None and r.achievable_target > 0
