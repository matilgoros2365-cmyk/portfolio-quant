"""Punto de entrada de la API FastAPI.

En esta Tarea 1 solo levanta la app, crea las tablas al iniciar y expone
un endpoint de salud. Los endpoints reales llegan en la Tarea 5.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al arrancar: crear tablas si no existen.
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Chequeo simple de que la app está viva."""
    return {"status": "ok", "app": settings.app_name}
