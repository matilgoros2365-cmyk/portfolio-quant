"""Guardado de análisis para auditoría / historial."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun


def save_analysis(
    db: Session,
    kind: str,
    inputs: dict,
    result: dict,
    risk_profile: str | None = None,
    base_currency: str | None = None,
    label: str | None = None,
) -> int:
    """Persiste un análisis completo y devuelve su id."""
    run = AnalysisRun(
        kind=kind,
        risk_profile=risk_profile,
        base_currency=base_currency,
        label=label,
        inputs=inputs,
        result=result,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run.id
