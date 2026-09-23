"""Modelo `DailyPrice`: serie temporal de precios diarios por activo."""
from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.asset import Asset


class DailyPrice(Base):
    __tablename__ = "daily_prices"
    __table_args__ = (
        # Un solo precio por activo y por fecha.
        UniqueConstraint("asset_id", "date", name="uq_daily_price_asset_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date_type] = mapped_column(Date, index=True, nullable=False)

    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    # Cierre ajustado por dividendos y splits: la serie que se usa para
    # calcular retornos. Es el campo obligatorio.
    adj_close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float | None] = mapped_column(Float)

    asset: Mapped["Asset"] = relationship(back_populates="prices")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DailyPrice asset={self.asset_id} {self.date} adj={self.adj_close}>"
