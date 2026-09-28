"""Modelo `User`: perfil local (estilo Netflix), sin cuentas ni contraseñas."""
from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models._mixins import TimestampMixin


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    avatar_color: Mapped[str | None] = mapped_column(String(16))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.name} ({self.id[:8]})>"
