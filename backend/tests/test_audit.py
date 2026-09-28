"""Test del guardado/lectura de análisis (historial)."""
from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.analysis_run import AnalysisRun
from app.services.audit import save_analysis


def _session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return Session(bind=engine)


def test_save_and_read_analysis() -> None:
    db = _session()
    run_id = save_analysis(
        db,
        kind="optimize",
        inputs={"risk_profile": "MODERATE", "universe": ["VOO", "QQQ"]},
        result={"recommended": {"weights": [{"symbol": "VOO", "weight": 0.6}]}},
        risk_profile="MODERATE",
        base_currency="USD",
        label="Recomendada (Moderada)",
    )
    assert run_id > 0

    row = db.get(AnalysisRun, run_id)
    assert row is not None
    assert row.kind == "optimize"
    assert row.risk_profile == "MODERATE"
    assert row.inputs["universe"] == ["VOO", "QQQ"]
    assert row.result["recommended"]["weights"][0]["symbol"] == "VOO"
    assert row.created_at is not None


def test_list_orders_newest_first() -> None:
    db = _session()
    for i in range(3):
        save_analysis(db, kind="risk", inputs={"i": i}, result={"i": i})
    rows = db.scalars(
        select(AnalysisRun).order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
    ).all()
    assert len(rows) == 3
    assert rows[0].inputs["i"] == 2  # el último guardado primero
