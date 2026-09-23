"""Endpoint de datos de mercado por símbolo."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analysis import AssetMetrics
from app.services.analysis import PortfolioAnalyzer

router = APIRouter()


@router.get("/market-data/{symbol}", response_model=AssetMetrics)
def get_market_data(
    symbol: str,
    refresh: bool = Query(False, description="Forzar re-descarga completa"),
    db: Session = Depends(get_db),
) -> AssetMetrics:
    """Descarga (o lee de caché) los precios de un símbolo y devuelve sus métricas."""
    analyzer = PortfolioAnalyzer(db)
    metrics = analyzer.analyze_symbol(symbol, full_refresh=refresh)
    if metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron datos para el símbolo '{symbol}'.",
        )
    return metrics
