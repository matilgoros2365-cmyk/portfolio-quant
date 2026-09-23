"""Endpoint de optimización / recomendación de cartera (Fase 2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.optimization import OptimizationResponse, OptimizeRequest
from app.services.optimizer import InsufficientDataError, PortfolioOptimizer

router = APIRouter()


@router.post("/portfolio/optimize", response_model=OptimizationResponse)
def optimize_portfolio(
    payload: OptimizeRequest,
    db: Session = Depends(get_db),
) -> OptimizationResponse:
    """Recomienda una cartera según el perfil de riesgo.

    Devuelve la cartera recomendada (con pesos), las carteras clásicas de
    referencia (mín. varianza, máx. Sharpe, risk parity) y la frontera
    eficiente. Requiere `custom_asset_universe` con al menos 2 símbolos.
    """
    if not payload.custom_asset_universe or len(payload.custom_asset_universe) < 2:
        raise HTTPException(
            status_code=422,
            detail=(
                "Enviá 'custom_asset_universe' con al menos 2 símbolos "
                'para optimizar (ej: ["VOO", "QQQ", "TLT", "GLD"]).'
            ),
        )
    optimizer = PortfolioOptimizer(db)
    try:
        return optimizer.optimize(
            payload.custom_asset_universe,
            risk_profile=payload.risk_profile,
            base_currency=payload.base_currency,
            max_weight=payload.max_weight,
        )
    except InsufficientDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
