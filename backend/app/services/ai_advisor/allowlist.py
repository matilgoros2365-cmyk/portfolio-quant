"""Lista vetada de instrumentos que la IA puede elegir.

La IA compone carteras SOLO de este menú (ETFs líquidos y aptos para
principiantes). Nunca inventa tickers: todo lo que proponga se valida contra
esta lista antes de usarse.
"""
from __future__ import annotations

ALLOWLIST: dict[str, str] = {
    # Acciones globales / EE.UU.
    "VT": "Acciones de todo el mundo (global)",
    "VTI": "Todo el mercado de acciones de EE.UU.",
    "VOO": "500 empresas más grandes de EE.UU. (S&P 500)",
    "QQQ": "100 mayores del Nasdaq (sesgo tecnología)",
    # Internacional / emergentes
    "VXUS": "Acciones fuera de EE.UU. (internacional)",
    "VEA": "Acciones de países desarrollados (ex-EE.UU.)",
    "VWO": "Acciones de mercados emergentes",
    # Dividendos / baja volatilidad
    "SCHD": "Acciones de EE.UU. que pagan buenos dividendos",
    "VYM": "Acciones de alto dividendo",
    "USMV": "Acciones de EE.UU. de baja volatilidad",
    # Bonos
    "BND": "Bonos de EE.UU. (amplio)",
    "BNDW": "Bonos del mundo (amplio)",
    "AGG": "Bonos de EE.UU. (amplio)",
    "TLT": "Bonos del Tesoro de EE.UU. a largo plazo",
    "IEF": "Bonos del Tesoro a mediano plazo",
    "SHY": "Bonos del Tesoro a corto plazo",
    "TIP": "Bonos ajustados por inflación (EE.UU.)",
    "LQD": "Bonos corporativos de buena calidad",
    # Oro / materias primas / inmuebles
    "GLD": "Oro",
    "IAU": "Oro (versión más barata)",
    "DBC": "Materias primas (canasta)",
    "VNQ": "Inmuebles de EE.UU. (REITs)",
    # Argentina
    "ARGT": "Empresas de Argentina (ETF, en dólares)",
}


def is_allowed(ticker: str) -> bool:
    return ticker.upper() in ALLOWLIST
