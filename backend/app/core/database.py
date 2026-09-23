"""Conexión a la base de datos y sesión de SQLAlchemy 2.0 (estilo tipado).

Arranque liviano: motor síncrono + SQLite. La clase `Base` es la base
declarativa de la que heredan todos los modelos. `init_db()` crea las
tablas automáticamente (sin Alembic por ahora).
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa compartida por todos los modelos ORM."""


# SQLite necesita `check_same_thread=False` para poder usarse desde FastAPI.
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: entrega una sesión y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea todas las tablas registradas en `Base.metadata`.

    Importa el paquete de modelos para que se registren antes de crear.
    """
    from app import models  # noqa: F401  (registra los modelos en Base)

    Base.metadata.create_all(bind=engine)
