"""Configuración central de la aplicación.

Lee variables de entorno (opcionalmente desde un archivo `.env`).
En el arranque liviano usamos SQLite; más adelante se cambia DATABASE_URL
a PostgreSQL sin tocar el resto del código.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- General ---
    app_name: str = "PortfolioQuant Engine"
    api_v1_prefix: str = "/api/v1"

    # --- Base de datos ---
    # SQLite por defecto (archivo local). Ejemplo Postgres futuro:
    # postgresql+psycopg://user:pass@localhost:5432/portfolioquant
    database_url: str = "sqlite:///./portfolioquant.db"
    db_echo: bool = False  # True para ver el SQL en consola (debug)

    # --- Proveedores de datos ---
    # API key gratuita de FRED (datos macro). Sin ella, la parte macro no corre.
    # Se obtiene en: https://fredaccount.stlouisfed.org/apikeys
    fred_api_key: str | None = None


settings = Settings()
