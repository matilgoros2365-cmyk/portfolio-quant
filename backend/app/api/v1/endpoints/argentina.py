"""Endpoint de referencias del mercado argentino (dólar + Merval)."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.market_detail import ArgentinaMarket, DollarRate, Quote
from app.services.argentina import get_dollar_rates, get_merval

router = APIRouter()


@router.get("/market/argentina", response_model=ArgentinaMarket)
def argentina_market() -> ArgentinaMarket:
    """Cotización del dólar (oficial/blue/MEP/CCL) y el índice Merval."""
    rates = get_dollar_rates()
    merval = get_merval()
    return ArgentinaMarket(
        dollars=[DollarRate(**r) for r in rates],
        merval=Quote(**merval) if merval else None,
        source="dolarapi.com · Yahoo Finance",
        note=(
            "Valores de referencia (diferidos). Los instrumentos de la cartera "
            "cotizan en dólares en EE.UU.; el dólar local es solo contexto."
        ),
    )
