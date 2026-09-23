"""Modelo `MacroSeries`: series macroeconómicas (FRED).

Cada fila es (serie, fecha, valor). Ejemplos de `series_id`:
  - "DGS10"     -> Tasa del Tesoro de EE.UU. a 10 años (risk-free)
  - "DGS3MO"    -> Tasa del Tesoro a 3 meses
  - "CPIAUCSL"  -> Índice de Precios al Consumidor (inflación)
"""
from __future__ import annotations

from datetime import date as date_type

from sqlalchemy import Date, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MacroSeries(Base):
    __tablename__ = "macro_series"
    __table_args__ = (
        UniqueConstraint("series_id", "date", name="uq_macro_series_id_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Código de la serie en FRED (p. ej. "DGS10").
    series_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    date: Mapped[date_type] = mapped_column(Date, index=True, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MacroSeries {self.series_id} {self.date}={self.value}>"
