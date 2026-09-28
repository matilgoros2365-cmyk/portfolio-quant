"""Construcción automática del universo de inversión.

El usuario principiante no elige tickers: el sistema arma una canasta amplia
y barata por defecto (global), con una opción de tilt argentino, y aplica las
exclusiones que el usuario pidió (Q13).
"""
from __future__ import annotations

from app.profiling import config as C

# Etiquetas por instrumento (para aplicar exclusiones).
TICKER_TAGS: dict[str, set[str]] = {
    "VT": {"broad_etf"},
    "BND": {"broad_etf", "bonds"},
    "GLD": {"broad_etf", "commodity"},
    "ARGT": {"broad_etf", "argentina"},
    "GGAL": {"individual_companies", "argentina"},
    "YPF": {"individual_companies", "argentina"},
    "PAM": {"individual_companies", "argentina"},
    "BMA": {"individual_companies", "argentina"},
}

# Exclusión elegida (Q13) -> etiquetas que hay que sacar.
EXCLUSION_TO_TAGS: dict[str, set[str]] = {
    "crypto": {"crypto"},
    "individual_companies": {"individual_companies"},
    "sectors": {"sector_etf"},
}


def build_universe(
    preference: str = "global", exclusions: list[str] | None = None
) -> list[str]:
    """Devuelve la lista de tickers del universo, ya filtrada por exclusiones.

    - "global" (default): canasta diversificada VT/BND/GLD.
    - "argentina": la global + ARGT (tilt argentino con un ETF amplio, en USD).
    """
    exclusions = exclusions or []
    if preference == "argentina":
        # Tilt argentino prudente: canasta global + un ETF amplio de Argentina.
        tickers = [*C.UNIVERSE_GLOBAL, "ARGT"]
    elif preference == "argentina_plus":
        # Opción avanzada (riesgo alto): suma ADRs argentinos individuales.
        tickers = [*C.UNIVERSE_GLOBAL, *C.UNIVERSE_ARGENTINA]
    else:
        tickers = list(C.UNIVERSE_GLOBAL)

    excl_tags: set[str] = set()
    for e in exclusions:
        excl_tags |= EXCLUSION_TO_TAGS.get(e, set())

    return [t for t in tickers if not (TICKER_TAGS.get(t, set()) & excl_tags)]
