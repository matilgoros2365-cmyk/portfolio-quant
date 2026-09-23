"""Modelo `Portfolio`: los inputs mínimos que carga el usuario.

Filosofía Zero Manual Inputs: el usuario solo define intención de negocio;
todo lo demás lo calcula el sistema.
"""
from __future__ import annotations

import enum

from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models._mixins import TimestampMixin


class RiskProfile(str, enum.Enum):
    VERY_CONSERVATIVE = "VERY_CONSERVATIVE"
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"
    VERY_AGGRESSIVE = "VERY_AGGRESSIVE"


class Portfolio(Base, TimestampMixin):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))

    # --- Inputs manuales del usuario (mínimos) ---
    initial_capital: Mapped[float] = mapped_column(Float, nullable=False)
    monthly_contribution: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    investment_horizon_years: Mapped[int] = mapped_column(Integer, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    risk_profile: Mapped[str] = mapped_column(String(32), nullable=False)
    # Opcional: objetivo de patrimonio final.
    target_wealth: Mapped[float | None] = mapped_column(Float)
    # Opcional: universo de activos elegido por el usuario, p. ej.
    # ["VOO", "QQQ", "TLT", "GLD"]. Si es None, lo define el sistema.
    custom_asset_universe: Mapped[list | None] = mapped_column(JSON)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Portfolio {self.name or self.id} {self.risk_profile}>"
