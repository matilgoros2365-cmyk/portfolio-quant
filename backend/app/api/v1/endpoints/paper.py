"""Endpoints del modo práctica (paper trading)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.paper import (
    BuyPortfolioRequest,
    BuyRequest,
    PaperHistory,
    PaperSnapshot,
    SellRequest,
)
from app.services.paper_trading import PaperError, PaperTradingService
from app.services.profile_service import ProfileService

router = APIRouter()


def _require_user(db: Session, user_id: str) -> None:
    if ProfileService(db).get_user(user_id) is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado.")


@router.get("/users/{user_id}/paper", response_model=PaperSnapshot)
def get_paper(user_id: str, db: Session = Depends(get_db)) -> PaperSnapshot:
    _require_user(db, user_id)
    return PaperTradingService(db).snapshot(user_id)


@router.get("/users/{user_id}/paper/history", response_model=PaperHistory)
def get_paper_history(user_id: str, db: Session = Depends(get_db)) -> PaperHistory:
    _require_user(db, user_id)
    return PaperTradingService(db).value_history(user_id)


@router.post("/users/{user_id}/paper/buy", response_model=PaperSnapshot)
def paper_buy(user_id: str, payload: BuyRequest, db: Session = Depends(get_db)) -> PaperSnapshot:
    _require_user(db, user_id)
    svc = PaperTradingService(db)
    try:
        svc.buy(user_id, payload.symbol, payload.amount)
    except PaperError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return svc.snapshot(user_id)


@router.post("/users/{user_id}/paper/sell", response_model=PaperSnapshot)
def paper_sell(user_id: str, payload: SellRequest, db: Session = Depends(get_db)) -> PaperSnapshot:
    _require_user(db, user_id)
    svc = PaperTradingService(db)
    try:
        svc.sell(user_id, payload.symbol, payload.amount, payload.all)
    except PaperError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return svc.snapshot(user_id)


@router.post("/users/{user_id}/paper/buy-portfolio", response_model=PaperSnapshot)
def paper_buy_portfolio(
    user_id: str, payload: BuyPortfolioRequest, db: Session = Depends(get_db)
) -> PaperSnapshot:
    _require_user(db, user_id)
    svc = PaperTradingService(db)
    svc.buy_portfolio(
        user_id,
        [a.model_dump() for a in payload.allocations],
        payload.amount,
    )
    return svc.snapshot(user_id)


@router.post("/users/{user_id}/paper/reset", response_model=PaperSnapshot)
def paper_reset(user_id: str, db: Session = Depends(get_db)) -> PaperSnapshot:
    _require_user(db, user_id)
    svc = PaperTradingService(db)
    svc.reset(user_id)
    return svc.snapshot(user_id)
