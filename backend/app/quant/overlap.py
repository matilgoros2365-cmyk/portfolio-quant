"""Solapamiento de tenencias entre fondos/ETFs.

Métrica estándar de "overlap por peso": para dos fondos con tenencias
{símbolo: peso}, el solapamiento es Σ min(w_a, w_b) sobre los símbolos en
común. Va de 0 (nada en común) a ~1 (idénticos).
"""
from __future__ import annotations


def weight_overlap(
    holdings_a: dict[str, float], holdings_b: dict[str, float]
) -> float:
    """Solapamiento por peso: Σ min(w_a, w_b) sobre tenencias comunes."""
    common = set(holdings_a) & set(holdings_b)
    return float(sum(min(holdings_a[s], holdings_b[s]) for s in common))


def overlapping_holdings(
    holdings_a: dict[str, float], holdings_b: dict[str, float]
) -> list[tuple[str, float, float]]:
    """Lista de (símbolo, peso_en_a, peso_en_b) para las tenencias comunes,
    ordenada por el menor de los dos pesos (mayor solapamiento primero)."""
    common = set(holdings_a) & set(holdings_b)
    rows = [(s, holdings_a[s], holdings_b[s]) for s in common]
    rows.sort(key=lambda r: min(r[1], r[2]), reverse=True)
    return rows


def coverage(holdings: dict[str, float]) -> float:
    """Fracción del fondo cubierta por las tenencias conocidas (top-N)."""
    return float(sum(holdings.values()))
