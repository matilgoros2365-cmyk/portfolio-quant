"""Endpoints del historial de análisis y del catálogo de fórmulas."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.analysis_run import AnalysisRun
from app.quant.formulas import FORMULAS
from app.schemas.analyses import AnalysisDetail, AnalysisSummary

router = APIRouter()


@router.get("/analyses", response_model=list[AnalysisSummary])
def list_analyses(
    limit: int = Query(50, ge=1, le=200),
    kind: str | None = Query(None, description="Filtrar por tipo de análisis"),
    db: Session = Depends(get_db),
) -> list[AnalysisRun]:
    """Lista los análisis guardados, del más nuevo al más viejo."""
    query = select(AnalysisRun)
    if kind:
        query = query.where(AnalysisRun.kind == kind)
    query = query.order_by(AnalysisRun.created_at.desc()).limit(limit)
    return list(db.scalars(query).all())


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)) -> AnalysisRun:
    """Devuelve un análisis guardado completo (inputs + resultado + fórmulas)."""
    row = db.get(AnalysisRun, analysis_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Análisis {analysis_id} no encontrado.")
    return row


@router.get("/formulas")
def get_formulas() -> dict[str, dict[str, str]]:
    """Catálogo completo de fórmulas usadas por el motor."""
    return FORMULAS
