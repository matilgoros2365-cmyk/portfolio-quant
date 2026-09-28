"""Modelo `Assessment`: un cuestionario respondido por un usuario.

Guarda las respuestas, el perfil inferido (scores + confidence por dimensión,
con las contribuciones de cada respuesta) y los parámetros financieros
derivados. No se borra: se guardan históricos; el más reciente es `is_current`.
"""
from __future__ import annotations

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models._mixins import TimestampMixin


class Assessment(Base, TimestampMixin):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    answers: Mapped[dict] = mapped_column(JSON, nullable=False)
    profile: Mapped[dict] = mapped_column(JSON, nullable=False)   # ProfileResult serializado
    derived: Mapped[dict] = mapped_column(JSON, nullable=False)   # inputs financieros derivados

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Assessment {self.id} user={self.user_id[:8]} current={self.is_current}>"
