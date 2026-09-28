"""Endpoint de análisis de factores (Fase 5)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.factors import FactorRequest, FactorResponse
from app.services.audit import save_analysis
from app.services.factor_analysis import FactorAnalysisService
from app.services.optimizer import InsufficientDataError

router = APIRouter()


@router.post("/portfolio/factors", response_model=FactorResponse)
def analyze_factors(
    payload: FactorRequest,
    db: Session = Depends(get_db),
) -> FactorResponse:
    """Exposición de la cartera a factores de riesgo (mercado, tamaño, valor, bonos)."""
    if not payload.custom_asset_universe or len(payload.custom_asset_universe) < 2:
        raise HTTPException(
            status_code=422,
            detail='Enviá "custom_asset_universe" con al menos 2 símbolos.',
        )
    service = FactorAnalysisService(db)
    try:
        result = service.analyze(
            payload.custom_asset_universe,
            risk_profile=payload.risk_profile,
            base_currency=payload.base_currency,
            max_weight=payload.max_weight,
        )
    except InsufficientDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result.analysis_id = save_analysis(
        db, "factors", payload.model_dump(mode="json"), result.model_dump(mode="json"),
        risk_profile=payload.risk_profile.value, base_currency=payload.base_currency,
    )
    return result
