"""Schemas Pydantic para `Asset`."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.asset import AssetType


class AssetBase(BaseModel):
    symbol: str
    name: str | None = None
    asset_type: AssetType = AssetType.OTHER
    currency: str = "USD"
    exchange: str | None = None
    sector: str | None = None
    proxy_symbol: str | None = None


class AssetCreate(AssetBase):
    """Datos para crear un activo."""


class AssetRead(AssetBase):
    """Activo tal como se devuelve por la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
