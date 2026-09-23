"""Modelo `FundHolding`: tenencias (holdings) de un ETF/fondo.

Con datos gratuitos solo se obtienen las principales tenencias (top-N),
así que la cobertura es parcial. Se cachea en la base porque cambian lento.
"""
from __future__ import annotations

from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models._mixins import TimestampMixin


class FundHolding(Base, TimestampMixin):
    __tablename__ = "fund_holdings"
    __table_args__ = (
        UniqueConstraint(
            "fund_symbol", "holding_symbol", name="uq_fund_holding"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fund_symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    holding_symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    holding_name: Mapped[str | None] = mapped_column(String(255))
    # Peso de la tenencia dentro del fondo (fracción 0-1).
    weight: Mapped[float] = mapped_column(Float, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FundHolding {self.fund_symbol}:{self.holding_symbol}={self.weight}>"
