"""Modelo `AnalysisRun`: registro auditable de cada análisis realizado.

Guarda los inputs y el resultado completo (incluidas fórmulas y cálculos
intermedios) de cada llamada, para poder revisarlos después.
"""
from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models._mixins import TimestampMixin


class AnalysisRun(Base, TimestampMixin):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Perfil local dueño del análisis (opcional; se completa cuando hay usuario).
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    # Tipo: optimize | risk | simulate | factors | robustness
    kind: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    risk_profile: Mapped[str | None] = mapped_column(String(32))
    base_currency: Mapped[str | None] = mapped_column(String(8))
    label: Mapped[str | None] = mapped_column(String(255))
    # Payload de entrada y respuesta completa (JSON).
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AnalysisRun {self.id} {self.kind} {self.created_at}>"
