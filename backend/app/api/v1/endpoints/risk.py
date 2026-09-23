"""Endpoint de análisis de riesgo avanzado (Fase 3)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.risk import RiskAnalysisResponse, RiskRequest
from app.services.optimizer import InsufficientDataError
from app.services.risk_analysis import RiskAnalyzer

router = APIRouter()


@router.post("/portfolio/risk", response_model=RiskAnalysisResponse)
def analyze_risk(
    payload: RiskRequest,
    db: Session = Depends(get_db),
) -> RiskAnalysisResponse:
    """Análisis de riesgo de la cartera recomendada para el perfil de riesgo.

    Devuelve VaR/CVaR, contribución al riesgo por activo, concentración,
    solapamiento de ETFs y exposición "look-through" a los subyacentes.
    """
    if not payload.custom_asset_universe or len(payload.custom_asset_universe) < 2:
        raise HTTPException(
            status_code=422,
            detail=(
                "Enviá 'custom_asset_universe' con al menos 2 símbolos "
                'para el análisis de riesgo (ej: ["VOO", "QQQ", "TLT", "GLD"]).'
            ),
        )
    analyzer = RiskAnalyzer(db)
    try:
        return analyzer.analyze(
            payload.custom_asset_universe,
            risk_profile=payload.risk_profile,
            base_currency=payload.base_currency,
            confidence=payload.confidence_level,
            max_weight=payload.max_weight,
        )
    except InsufficientDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
