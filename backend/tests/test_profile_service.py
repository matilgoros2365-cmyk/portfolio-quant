"""Test del servicio de perfiles locales y cuestionarios (en memoria)."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.services.profile_service import ProfileService


def _service() -> ProfileService:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return ProfileService(Session(bind=engine))


def test_create_user_and_assessment() -> None:
    svc = _service()
    user = svc.create_user("Matilda", avatar_color="#4f46e5")
    assert user.id and len(user.id) == 36
    assert user.name == "Matilda"

    answers = {
        "Q3": "y5_10", "Q4": "other_savings", "Q5": "several_months",
        "Q9": "hold", "Q10": "at_20", "Q8": "fairly_sure",
        "currency": "USD", "initial_capital": 10000, "monthly_contribution": 200,
        "target_wealth": 100000, "Q1": "grow",
    }
    a = svc.create_assessment(user.id, answers)
    assert a.is_current is True
    assert a.profile["risk_label"] in {"MODERATE", "AGGRESSIVE", "VERY_AGGRESSIVE", "CONSERVATIVE"}
    assert a.derived["investment_horizon_years"] == 7
    assert a.derived["currency"] == "USD"
    # Haircut de aportes aplicado (0.9 para "fairly_sure").
    assert a.derived["monthly_contribution_effective"] == 180.0


def test_new_assessment_supersedes_previous() -> None:
    svc = _service()
    user = svc.create_user("Felipe")
    svc.create_assessment(user.id, {"Q3": "y1_3", "Q9": "sell_part"})
    svc.create_assessment(user.id, {"Q3": "gt_10", "Q9": "add"})

    current = svc.current_assessment(user.id)
    assert current is not None
    assert current.answers["Q3"] == "gt_10"  # el más nuevo es el vigente

    history = svc.list_assessments(user.id)
    assert len(history) == 2
    # Solo uno vigente.
    assert sum(1 for a in history if a.is_current) == 1
