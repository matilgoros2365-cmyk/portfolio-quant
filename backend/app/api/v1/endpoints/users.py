"""Endpoints de perfiles locales y cuestionario de perfilado."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.profiling.scoring import score_profile
from app.schemas.profiling import (
    AssessmentCreate,
    AssessmentOut,
    ProfileOut,
    UserCreate,
    UserOut,
)
from app.services.profile_service import ProfileService, profile_to_dict

router = APIRouter()


@router.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> object:
    return ProfileService(db).create_user(payload.name, payload.avatar_color)


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> object:
    return ProfileService(db).list_users()


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)) -> object:
    user = ProfileService(db).get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado.")
    return user


@router.post("/users/{user_id}/assessments", response_model=AssessmentOut)
def create_assessment(
    user_id: str, payload: AssessmentCreate, db: Session = Depends(get_db)
) -> object:
    service = ProfileService(db)
    if service.get_user(user_id) is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado.")
    return service.create_assessment(user_id, payload.answers)


@router.get("/users/{user_id}/assessments", response_model=list[AssessmentOut])
def list_assessments(user_id: str, db: Session = Depends(get_db)) -> object:
    return ProfileService(db).list_assessments(user_id)


@router.get("/users/{user_id}/assessments/current", response_model=AssessmentOut)
def current_assessment(user_id: str, db: Session = Depends(get_db)) -> object:
    current = ProfileService(db).current_assessment(user_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Este perfil todavía no completó el cuestionario.")
    return current


@router.post("/profile/score", response_model=ProfileOut)
def preview_score(payload: AssessmentCreate) -> ProfileOut:
    """Calcula el perfil sin guardarlo (útil para previsualizar en vivo)."""
    result = score_profile(payload.answers)
    return ProfileOut(**profile_to_dict(result))
