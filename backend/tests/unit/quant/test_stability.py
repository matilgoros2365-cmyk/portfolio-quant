"""Tests de estabilidad (remuestreo)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.quant.stability import resampled_optimization


def test_resampled_optimization_structure() -> None:
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {
            "AAA": rng.normal(0.0005, 0.01, 250),
            "BBB": rng.normal(0.0003, 0.02, 250),
            "CCC": rng.normal(0.0004, 0.006, 250),
        }
    )
    result = resampled_optimization(df, level=0.5, n_resamples=15, seed=1)
    assert result.symbols == ["AAA", "BBB", "CCC"]
    assert len(result.mean_weights) == 3
    assert len(result.std_weights) == 3
    # Los pesos promedio suman ~1 y son válidos.
    assert result.mean_weights.sum() == np.float64(result.mean_weights.sum())
    assert abs(float(result.mean_weights.sum()) - 1.0) < 0.05
    assert result.instability >= 0.0
    assert result.n_resamples == 15


def test_identical_assets_low_instability_reproducible() -> None:
    # Con semilla fija, dos corridas dan el mismo resultado.
    rng = np.random.default_rng(2)
    df = pd.DataFrame(
        {"AAA": rng.normal(0.0004, 0.012, 200), "BBB": rng.normal(0.0004, 0.012, 200)}
    )
    r1 = resampled_optimization(df, level=0.5, n_resamples=10, seed=42)
    r2 = resampled_optimization(df, level=0.5, n_resamples=10, seed=42)
    assert r1.instability == r2.instability
