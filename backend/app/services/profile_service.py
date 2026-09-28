"""Servicio de perfiles locales y cuestionarios."""
from __future__ import annotations

from dataclasses import asdict

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.user import User
from app.profiling.scoring import ProfileResult, score_profile


def profile_to_dict(p: ProfileResult) -> dict:
    """Serializa el ProfileResult a dict JSON-friendly (para guardar y devolver)."""
    d = asdict(p)
    d["dimensions"] = [asdict(v) for v in p.dimensions.values()]
    return d


def derived_inputs(answers: dict, p: ProfileResult) -> dict:
    """Parámetros financieros derivados que consumirá el motor cuantitativo."""
    return {
        "currency": answers.get("currency", "USD"),
        "initial_capital": answers.get("initial_capital"),
        "monthly_contribution": answers.get("monthly_contribution"),
        "monthly_contribution_effective": (
            round(answers["monthly_contribution"] * p.mc_contribution_factor, 2)
            if isinstance(answers.get("monthly_contribution"), (int, float))
            else None
        ),
        "target_wealth": answers.get("target_wealth"),
        "goal_type": answers.get("Q1"),
        "goal_name": answers.get("goal_name"),
        "investment_horizon_years": p.horizon_years,
        "risk_level": p.risk_level,
        "risk_label": p.risk_label,
        "max_weight": p.max_weight,
        "exclusions": p.exclusions,
        "goal_alarm_prob": p.goal_alarm_prob,
    }


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- usuarios ---
    def create_user(self, name: str, avatar_color: str | None = None) -> User:
        user = User(name=name, avatar_color=avatar_color)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.created_at)).all())

    def get_user(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    # --- cuestionarios ---
    def create_assessment(self, user_id: str, answers: dict) -> Assessment:
        result = score_profile(answers)
        # El nuevo assessment pasa a ser el vigente; los anteriores dejan de serlo.
        self.db.execute(
            update(Assessment).where(Assessment.user_id == user_id).values(is_current=False)
        )
        assessment = Assessment(
            user_id=user_id,
            is_current=True,
            answers=answers,
            profile=profile_to_dict(result),
            derived=derived_inputs(answers, result),
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def list_assessments(self, user_id: str) -> list[Assessment]:
        return list(
            self.db.scalars(
                select(Assessment)
                .where(Assessment.user_id == user_id)
                .order_by(Assessment.created_at.desc())
            ).all()
        )

    def current_assessment(self, user_id: str) -> Assessment | None:
        return self.db.scalar(
            select(Assessment).where(
                Assessment.user_id == user_id, Assessment.is_current.is_(True)
            )
        )
