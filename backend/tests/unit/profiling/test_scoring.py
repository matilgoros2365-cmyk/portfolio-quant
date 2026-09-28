"""Tests del motor de scoring del perfilado, con valores calculados a mano."""
from __future__ import annotations

import pytest

from app.profiling.scoring import score_profile


def test_long_horizon_calm_gives_high_level() -> None:
    answers = {
        "Q3": "gt_10", "Q4": "other_savings", "Q5": "several_months",
        "Q9": "hold", "Q10": "at_30", "Q8": "very_sure", "Q11": "flexible",
    }
    p = score_profile(answers)
    # techo = min(95,100,100)=95 ; tolerancia = 78*0.6 + 85*0.4 = 80.8
    assert p.techo_capacidad == pytest.approx(95.0)
    assert p.tolerancia == pytest.approx(80.8)
    assert p.risk_level == pytest.approx(0.808)
    assert p.capacity_binding is False
    assert p.tolerance_binding is False
    assert p.horizon_years == 15
    assert p.mc_contribution_factor == 1.0


def test_capacity_caps_high_tolerance_contradiction() -> None:
    # Tolera mucho riesgo pero necesita la plata ya: manda la capacidad.
    answers = {
        "Q3": "lt_1y", "Q4": "need_for_expenses", "Q5": "none",
        "Q9": "add", "Q10": "at_30",
    }
    p = score_profile(answers)
    assert p.techo_capacidad == pytest.approx(10.0)
    assert p.tolerancia == pytest.approx(89.2)
    assert p.risk_level == pytest.approx(0.10)   # gana el techo (10), no la tolerancia (89)
    assert p.risk_label == "VERY_CONSERVATIVE"
    assert p.capacity_binding is True


def test_dont_know_tolerance_is_neutral_not_conservative() -> None:
    answers = {
        "Q3": "y5_10", "Q4": "other_savings", "Q5": "several_months",
        "Q9": "dont_know", "Q10": "dont_know",
    }
    p = score_profile(answers)
    # Sin evidencia de tolerancia -> 50 (neutro), NUNCA conservador.
    assert p.tolerancia == pytest.approx(50.0)
    assert p.risk_level == pytest.approx(0.5)
    assert p.risk_label == "MODERATE"
    tol = next(d for d in p.dimensions.values() if d.name == "risk_tolerance")
    assert tol.confidence == 0.0
    assert tol.evidence_count == 0


def test_ab_fallback_when_scenario_unknown() -> None:
    answers = {
        "Q3": "y5_10", "Q4": "other_savings", "Q5": "several_months",
        "Q9": "dont_know", "Q10": "dont_know", "QB": "def_b",
    }
    p = score_profile(answers)
    assert p.tolerancia == pytest.approx(90.0)  # QB def_b
    assert p.risk_level == pytest.approx(0.75)  # min(90, techo 75)


def test_exclusions_and_contribution_factor() -> None:
    answers = {"Q3": "y5_10", "Q8": "may_vary", "Q13": ["crypto", "none"]}
    p = score_profile(answers)
    assert p.mc_contribution_factor == 0.7
    assert p.exclusions == ["crypto"]  # "none" se filtra


def test_overall_confidence_in_range() -> None:
    p = score_profile({"Q3": "y3_5", "Q4": "manageable", "Q5": "some", "Q9": "wait"})
    assert 0.0 <= p.overall_confidence <= 1.0
    # Cada respuesta deja su contribución auditable.
    horizon = next(d for d in p.dimensions.values() if d.name == "horizon")
    assert horizon.contributions == [{"question": "Q3", "answer": "y3_5", "score": 50.0}]
