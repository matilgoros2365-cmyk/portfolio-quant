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

    # --- CORS (orígenes permitidos para el frontend) ---
    # Coma-separado. En deploy: poner acá la URL del frontend (ej. Vercel).
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # --- Asesor IA (opcional; OpenRouter, gratis). Sin key -> modelos curados. ---
    # Key gratuita en: https://openrouter.ai/settings/keys
    openrouter_api_key: str | None = None
    # Modelo gratis que responde JSON de forma confiable (probado). Cambiable en .env.
    openrouter_model: str = "nvidia/nemotron-3-super-120b-a12b:free"


settings = Settings()
