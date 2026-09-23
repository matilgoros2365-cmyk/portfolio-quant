"""Análisis de concentración de una cartera.

Trabaja sobre pesos (fracciones que suman 1). El índice de Herfindahl (HHI)
mide qué tan concentrada está: 1/n = perfectamente diversificada entre n
activos; 1 = todo en un solo activo.
"""
from __future__ import annotations

import numpy as np


def herfindahl_index(weights: np.ndarray) -> float:
    """HHI = Σ w_i². Entre 1/n (diversificada) y 1 (concentrada)."""
    w = np.asarray(weights, dtype=float)
    return float(np.sum(w**2))


def effective_number_of_assets(weights: np.ndarray) -> float:
    """Nº efectivo de activos = 1/HHI (cuántos activos 'equivalentes' hay)."""
    hhi = herfindahl_index(weights)
    if hhi <= 0:
        return float("nan")
    return float(1.0 / hhi)


def top_n_concentration(weights: np.ndarray, n: int = 3) -> float:
    """Suma de los `n` pesos más grandes."""
    w = np.sort(np.asarray(weights, dtype=float))[::-1]
    return float(np.sum(w[:n]))


def concentration_summary(weights: np.ndarray) -> dict[str, float]:
    """Resumen de concentración de la cartera."""
    w = np.asarray(weights, dtype=float)
    return {
        "herfindahl_index": herfindahl_index(w),
        "effective_num_assets": effective_number_of_assets(w),
        "max_weight": float(np.max(w)) if len(w) else float("nan"),
        "top3_weight": top_n_concentration(w, 3),
    }


def look_through_exposures(
    portfolio_weights: dict[str, float],
    holdings: dict[str, dict[str, float]],
) -> tuple[dict[str, float], float]:
    """Exposición real a cada subyacente mirando "a través" de los ETFs.

    Para cada activo de la cartera:
      - si es un fondo con tenencias conocidas, se reparte su peso entre sus
        subyacentes (peso_cartera × peso_dentro_del_fondo);
      - lo no cubierto (por datos parciales) se agrupa como '_no_cubierto'.

    Devuelve (exposiciones, cobertura), donde `cobertura` es la fracción de
    la cartera que se pudo desagregar en subyacentes.
    """
    exposures: dict[str, float] = {}
    covered = 0.0

    for symbol, p_weight in portfolio_weights.items():
        fund = holdings.get(symbol.upper())
        if fund:
            fund_total = sum(fund.values())
            for holding_symbol, h_weight in fund.items():
                exposures[holding_symbol] = (
                    exposures.get(holding_symbol, 0.0) + p_weight * h_weight
                )
            covered += p_weight * min(fund_total, 1.0)
            remainder = p_weight * max(1.0 - fund_total, 0.0)
            if remainder > 0:
                exposures["_no_cubierto"] = (
                    exposures.get("_no_cubierto", 0.0) + remainder
                )
        else:
            # Activo simple (o sin tenencias conocidas): cuenta como sí mismo.
            exposures[symbol.upper()] = exposures.get(symbol.upper(), 0.0) + p_weight
            covered += p_weight

    return exposures, float(covered)
