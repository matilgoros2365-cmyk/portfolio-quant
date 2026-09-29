"""Router principal de la API v1: agrupa todos los endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analyses,
    argentina,
    factors,
    market_data,
    optimize,
    paper,
    portfolio,
    risk,
    robustness,
    simulate,
    users,
)

api_router = APIRouter()
api_router.include_router(market_data.router, tags=["market-data"])
api_router.include_router(argentina.router, tags=["market-data"])
api_router.include_router(paper.router, tags=["paper"])
api_router.include_router(portfolio.router, tags=["portfolio"])
api_router.include_router(optimize.router, tags=["portfolio"])
api_router.include_router(risk.router, tags=["portfolio"])
api_router.include_router(simulate.router, tags=["portfolio"])
api_router.include_router(factors.router, tags=["portfolio"])
api_router.include_router(robustness.router, tags=["portfolio"])
api_router.include_router(analyses.router, tags=["analyses"])
api_router.include_router(users.router, tags=["profiles"])
