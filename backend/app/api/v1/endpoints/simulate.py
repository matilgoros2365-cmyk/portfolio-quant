"""Endpoint de simulación de Monte Carlo (Fase 4)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.simulation import SimulateRequest, SimulationResponse
from app.services.audit import save_analysis
from app.services.optimizer import InsufficientDataError
from app.services.simulation import SimulationService

router = APIRouter()


@router.post("/portfolio/simulate", response_model=SimulationResponse)
def simulate_portfolio(
    payload: SimulateRequest,
    db: Session = Depends(get_db),
) -> SimulationResponse:
    """Proyecta el patrimonio con Monte Carlo y calcula la probabilidad de meta.

    Usa la cartera recomendada para el perfil de riesgo. Si mandás
    `target_wealth`, devuelve la probabilidad de alcanzarlo. Incluye el
    impacto de crisis históricas reales sobre la cartera.
    """
    if not payload.custom_asset_universe or len(payload.custom_asset_universe) < 2:
        raise HTTPException(
            status_code=422,
            detail=(
                "Enviá 'custom_asset_universe' con al menos 2 símbolos "
                'para simular (ej: ["VOO", "QQQ", "TLT", "GLD"]).'
            ),
        )
    service = SimulationService(db)
    try:
        result = service.simulate(
            payload.custom_asset_universe,
            risk_profile=payload.risk_profile,
            initial_capital=payload.initial_capital,
            monthly_contribution=payload.monthly_contribution,
            years=payload.investment_horizon_years,
            target_wealth=payload.target_wealth,
            method=payload.method,
            n_simulations=payload.n_simulations,
            student_t_df=payload.student_t_df,
            base_currency=payload.base_currency,
            max_weight=payload.max_weight,
            seed=payload.random_seed,
        )
    except InsufficientDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result.analysis_id = save_analysis(
        db, "simulate", payload.model_dump(mode="json"), result.model_dump(mode="json"),
        risk_profile=payload.risk_profile.value, base_currency=payload.base_currency,
    )
    return result
