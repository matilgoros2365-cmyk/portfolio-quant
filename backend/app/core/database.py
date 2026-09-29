"""Conexión a la base de datos y sesión de SQLAlchemy 2.0 (estilo tipado).

Arranque liviano: motor síncrono + SQLite. La clase `Base` es la base
declarativa de la que heredan todos los modelos. `init_db()` crea las
tablas automáticamente (sin Alembic por ahora).
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa compartida por todos los modelos ORM."""


# Normalizar la URL de Postgres para que use el driver psycopg 3 (deploy).
_db_url = settings.database_url
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)

_is_sqlite = _db_url.startswith("sqlite")

# SQLite necesita `check_same_thread=False` para poder usarse desde FastAPI.
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(
    _db_url,
    echo=settings.db_echo,
    connect_args=_connect_args,
    pool_pre_ping=not _is_sqlite,  # reconecta si Postgres cerró la conexión ociosa
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):  # pragma: no cover
        """WAL + busy_timeout: mejor concurrencia de lectura/escritura."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=10000")  # espera hasta 10s si está bloqueada
        cursor.close()


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
