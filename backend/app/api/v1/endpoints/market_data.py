"""Endpoint de datos de mercado por símbolo."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analysis import AssetMetrics
from app.schemas.market_detail import AssetDetail, Composition, Quote
from app.services.analysis import PortfolioAnalyzer
from app.services.market_data.yahoo import YahooFinanceProvider
from app.services.market_search import catalog, search_symbols

router = APIRouter()


@router.get("/market/search")
def market_search(q: str = Query("", description="Nombre o ticker a buscar")) -> list[dict]:
    """Busca instrumentos (acciones, cripto, bonos, ETFs...) por nombre o ticker."""
    return search_symbols(q)


@router.get("/market/catalog")
def market_catalog() -> dict:
    """Listas rápidas por categoría + carteras armadas."""
    return catalog()


@router.get("/market-data/{symbol}", response_model=AssetMetrics)
def get_market_data(
    symbol: str,
    refresh: bool = Query(False, description="Forzar re-descarga completa"),
    db: Session = Depends(get_db),
) -> AssetMetrics:
    """Descarga (o lee de caché) los precios de un símbolo y devuelve sus métricas."""
    analyzer = PortfolioAnalyzer(db)
    metrics = analyzer.analyze_symbol(symbol, full_refresh=refresh)
    if metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron datos para el símbolo '{symbol}'.",
        )
    return metrics


@router.get("/market-data/{symbol}/detail", response_model=AssetDetail)
def get_asset_detail(symbol: str) -> AssetDetail:
    """Precio actual (diferido) + qué hay adentro del activo (rubro, sectores, empresas)."""
    provider = YahooFinanceProvider()
    quote = provider.get_quote(symbol)
    composition = provider.get_composition(symbol)
    return AssetDetail(
        symbol=symbol.upper(),
        quote=Quote(**quote),
        composition=Composition(**composition),
    )
