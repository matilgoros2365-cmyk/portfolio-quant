"""Endpoint de análisis de cartera."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analysis import PortfolioAnalysisResponse
from app.schemas.portfolio import PortfolioCreate
from app.services.analysis import PortfolioAnalyzer

router = APIRouter()


@router.post("/portfolio/analyze", response_model=PortfolioAnalysisResponse)
def analyze_portfolio(
    payload: PortfolioCreate,
    db: Session = Depends(get_db),
) -> PortfolioAnalysisResponse:
    """Analiza un universo de activos: métricas por activo + cartera de referencia.

    En la Fase 1 el análisis se hace sobre `custom_asset_universe` (todavía
    no construimos el universo automáticamente; eso llega en la Fase 2).
    """
    if not payload.custom_asset_universe:
        raise HTTPException(
            status_code=422,
            detail=(
                "En la Fase 1 debés enviar 'custom_asset_universe' con al "
                "menos un símbolo (p. ej. [\"VOO\", \"QQQ\", \"TLT\", \"GLD\"])."
            ),
        )
    analyzer = PortfolioAnalyzer(db)
    return analyzer.analyze(
        payload.custom_asset_universe, base_currency=payload.base_currency
    )
