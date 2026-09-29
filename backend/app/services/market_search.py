"""Búsqueda de instrumentos (proxy a Yahoo Finance) y catálogo por categorías.

Permite comprar cualquier símbolo que exista en Yahoo (acciones, cripto, bonos,
ETFs, etc.) buscándolo por nombre o ticker, más listas rápidas curadas.
"""
from __future__ import annotations

import time

import requests

from app.profiling.model_portfolios import MODELS

_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PortfolioQuant/1.0)"}

_TYPE_ES = {
    "EQUITY": "Acción",
    "ETF": "ETF",
    "CRYPTOCURRENCY": "Cripto",
    "MUTUALFUND": "Fondo",
    "INDEX": "Índice",
    "CURRENCY": "Moneda",
    "FUTURE": "Futuro",
}

_search_cache: dict[str, tuple[float, list]] = {}
_CACHE_TTL = 120


def search_symbols(query: str, limit: int = 12) -> list[dict]:
    q = (query or "").strip()
    if len(q) < 1:
        return []
    now = time.time()
    hit = _search_cache.get(q.lower())
    if hit and now - hit[0] < _CACHE_TTL:
        return hit[1]
    try:
        r = requests.get(
            _SEARCH_URL,
            params={"q": q, "quotesCount": limit, "newsCount": 0, "lang": "en-US"},
            headers=_HEADERS,
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
    except Exception:  # noqa: BLE001
        return []
    out = []
    for it in data.get("quotes", []):
        sym = it.get("symbol")
        if not sym:
            continue
        out.append({
            "symbol": sym,
            "name": it.get("shortname") or it.get("longname") or sym,
            "type": _TYPE_ES.get(str(it.get("quoteType", "")).upper(), "Otro"),
            "exchange": it.get("exchange"),
        })
    _search_cache[q.lower()] = (now, out)
    return out


# Listas rápidas curadas por categoría (símbolo, nombre legible).
CATALOG: dict[str, list[tuple[str, str]]] = {
    "Acciones populares": [
        ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("NVDA", "NVIDIA"),
        ("AMZN", "Amazon"), ("GOOGL", "Alphabet (Google)"), ("TSLA", "Tesla"),
        ("META", "Meta"), ("KO", "Coca-Cola"), ("MELI", "MercadoLibre"),
        ("JPM", "JPMorgan"),
    ],
    "Cripto": [
        ("BTC-USD", "Bitcoin"), ("ETH-USD", "Ethereum"), ("SOL-USD", "Solana"),
        ("BNB-USD", "BNB"), ("XRP-USD", "XRP"), ("ADA-USD", "Cardano"),
        ("DOGE-USD", "Dogecoin"),
    ],
    "Bonos": [
        ("TLT", "Tesoro EE.UU. largo (20+ años)"), ("IEF", "Tesoro mediano"),
        ("SHY", "Tesoro corto"), ("BND", "Bonos EE.UU. (amplio)"),
        ("LQD", "Corporativos buena calidad"), ("TIP", "Ajustados por inflación"),
        ("HYG", "Alto rendimiento"),
    ],
    "ETFs": [
        ("VOO", "S&P 500"), ("QQQ", "Nasdaq-100"), ("VT", "Acciones del mundo"),
        ("VWO", "Mercados emergentes"), ("GLD", "Oro"), ("VNQ", "Inmuebles (REITs)"),
        ("ARGT", "Argentina"),
    ],
    "Acciones argentinas (ADR)": [
        ("GGAL", "Grupo Galicia"), ("YPF", "YPF"), ("PAM", "Pampa Energía"),
        ("BMA", "Banco Macro"), ("BBAR", "BBVA Argentina"), ("TEO", "Telecom"),
        ("CEPU", "Central Puerto"), ("CRESY", "Cresud"),
    ],
}


def catalog() -> dict:
    categorias = {
        name: [{"symbol": s, "name": n} for s, n in items]
        for name, items in CATALOG.items()
    }
    carteras = [
        {"id": m.id, "name": m.name, "tickers": m.tickers, "description": m.description}
        for m in MODELS
    ]
    return {"categorias": categorias, "carteras": carteras}
