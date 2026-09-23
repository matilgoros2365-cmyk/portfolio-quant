"""Tests de correlación / covarianza y detección de pares altos."""
from __future__ import annotations

import pandas as pd
import pytest

from app.quant.correlation import (
    correlation_matrix,
    covariance_matrix,
    high_correlation_pairs,
)


def test_correlation_perfect_positive() -> None:
    df = pd.DataFrame({"A": [0.1, -0.1, 0.1, -0.1], "B": [0.2, -0.2, 0.2, -0.2]})
    corr = correlation_matrix(df)
    assert corr.loc["A", "B"] == pytest.approx(1.0)


def test_high_correlation_pairs_detects_pair() -> None:
    df = pd.DataFrame({"A": [0.1, -0.1, 0.1, -0.1], "B": [0.2, -0.2, 0.2, -0.2]})
    pairs = high_correlation_pairs(df, threshold=0.85)
    assert len(pairs) == 1
    a, b, c = pairs[0]
    assert {a, b} == {"A", "B"}
    assert c == pytest.approx(1.0)


def test_high_correlation_pairs_none_when_uncorrelated() -> None:
    # A y B tienen correlación exactamente 0.
    df = pd.DataFrame({"A": [1.0, -1.0, 1.0, -1.0], "B": [1.0, 1.0, -1.0, -1.0]})
    assert high_correlation_pairs(df, threshold=0.85) == []


def test_covariance_annualized() -> None:
    df = pd.DataFrame({"A": [0.1, -0.1, 0.1, -0.1]})
    # var muestral = 0.04/3 = 0.0133333; anualizada x4 = 0.0533333
    cov = covariance_matrix(df, annualize=True, periods_per_year=4)
    assert cov.loc["A", "A"] == pytest.approx(0.05333333, rel=1e-6)
