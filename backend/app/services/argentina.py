"""Referencias del mercado argentino: cotización del dólar y Merval.

El dólar se obtiene de dolarapi.com (API pública gratuita, sin key). El Merval
vía Yahoo (^MERV). Todo con cache en memoria y degradación elegante si falla.
"""
from __future__ import annotations

import time

import requests

from app.services.market_data.yahoo import YahooFinanceProvider

_DOLLAR_URL = "https://dolarapi.com/v1/dolares"
_CACHE_TTL = 300  # 5 minutos
_cache: dict = {"ts": 0.0, "data": None}

# Casas que mostramos y su nombre legible.
_CASAS = {
    "oficial": "Oficial",
    "blue": "Blue",
    "bolsa": "MEP (bolsa)",
    "contadoconliqui": "Contado con liqui (CCL)",
    "tarjeta": "Tarjeta",
}


def get_dollar_rates() -> list[dict]:
    now = time.time()
    if _cache["data"] is not None and (now - _cache["ts"]) < _CACHE_TTL:
        return _cache["data"]
    try:
        resp = requests.get(_DOLLAR_URL, timeout=6)
        resp.raise_for_status()
        raw = resp.json()
    except Exception:  # noqa: BLE001 - degradar con elegancia
        return _cache["data"] or []

    rates = []
    for item in raw:
        casa = str(item.get("casa", "")).lower()
        if casa in _CASAS:
            rates.append({
                "name": _CASAS[casa],
                "buy": item.get("compra"),
                "sell": item.get("venta"),
            })
    _cache["data"] = rates
    _cache["ts"] = now
    return rates


def get_merval() -> dict | None:
    try:
        return YahooFinanceProvider().get_quote("^MERV")
    except Exception:  # noqa: BLE001
        return None
