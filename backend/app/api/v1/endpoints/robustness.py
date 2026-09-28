"""Endpoint de robustez: Black-Litterman + estabilidad (Fase 5)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.robustness import RobustnessRequest, RobustnessResponse
from app.services.audit import save_analysis
from app.services.optimizer import InsufficientDataError
from app.services.robustness import RobustnessService

router = APIRouter()


@router.post("/portfolio/robustness", response_model=RobustnessResponse)
def analyze_robustness(
    payload: RobustnessRequest,
    db: Session = Depends(get_db),
) -> RobustnessResponse:
    """Compara retornos históricos vs Black-Litterman y mide la estabilidad."""
    if not payload.custom_asset_universe or len(payload.custom_asset_universe) < 2:
        raise HTTPException(
            status_code=422,
            detail='Enviá "custom_asset_universe" con al menos 2 símbolos.',
        )
    service = RobustnessService(db)
    try:
        result = service.analyze(
            payload.custom_asset_universe,
            risk_profile=payload.risk_profile,
            base_currency=payload.base_currency,
            max_weight=payload.max_weight,
            n_resamples=payload.n_resamples,
            seed=payload.random_seed,
        )
    except InsufficientDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result.analysis_id = save_analysis(
        db, "robustness", payload.model_dump(mode="json"), result.model_dump(mode="json"),
        risk_profile=payload.risk_profile.value, base_currency=payload.base_currency,
    )
    return result
