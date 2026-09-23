"""Modelo `Asset`: un instrumento financiero (acción, ETF, bono, etc.)."""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.daily_price import DailyPrice


class AssetType(str, enum.Enum):
    """Clasificación del activo."""

    EQUITY = "EQUITY"        # Acción individual
    ETF = "ETF"              # Fondo cotizado
    BOND = "BOND"            # Bono / renta fija
    COMMODITY = "COMMODITY"  # Materia prima (oro, etc.)
    INDEX = "INDEX"          # Índice
    CRYPTO = "CRYPTO"        # Criptomoneda
    OTHER = "OTHER"


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Ticker, p. ej. "VOO", "AAPL", "TLT".
    symbol: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255))
    asset_type: Mapped[str] = mapped_column(
        String(32), default=AssetType.OTHER.value, nullable=False
    )
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    exchange: Mapped[str | None] = mapped_column(String(32))
    sector: Mapped[str | None] = mapped_column(String(64))
    # Proxy para activos con poco historial (ver Limitación #2 del diseño):
    # ticker/índice equivalente con el que rellenar historia previa.
    proxy_symbol: Mapped[str | None] = mapped_column(String(32))

    prices: Mapped[list["DailyPrice"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"<Asset {self.symbol} ({self.asset_type})>"
