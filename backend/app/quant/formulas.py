"""Catálogo de fórmulas del motor cuantitativo.

Documenta, en texto, qué calcula cada métrica y con qué fórmula. Se expone
por API y se guarda junto a cada análisis para poder auditarlo después.
"""
from __future__ import annotations

FORMULAS: dict[str, dict[str, str]] = {
    "retorno_simple": {
        "formula": "r_t = P_t / P_{t-1} - 1",
        "descripcion": "Variación porcentual del precio (ajustado) entre períodos.",
    },
    "retorno_log": {
        "formula": "r_t = ln(P_t / P_{t-1})",
        "descripcion": "Retorno logarítmico (aditivo en el tiempo).",
    },
    "cagr": {
        "formula": "CAGR = (P_fin / P_ini)^(1/años) - 1",
        "descripcion": "Tasa de crecimiento anual compuesta.",
    },
    "retorno_esperado": {
        "formula": "E[r] = media(r) × 252",
        "descripcion": "Retorno esperado anualizado (media aritmética histórica).",
    },
    "volatilidad": {
        "formula": "σ = desv_est(r, ddof=1) × √252",
        "descripcion": "Volatilidad anualizada (riesgo total).",
    },
    "downside_deviation": {
        "formula": "DD = √( promedio( min(0, r - MAR)² ) ) × √252",
        "descripcion": "Desvío solo de los retornos por debajo del mínimo aceptable.",
    },
    "covarianza": {
        "formula": "Σ = cov(r) × 252",
        "descripcion": "Matriz de covarianza anualizada entre activos.",
    },
    "correlacion": {
        "formula": "ρ_ij = Σ_ij / (σ_i · σ_j)",
        "descripcion": "Correlación de Pearson entre pares de activos.",
    },
    "sharpe": {
        "formula": "Sharpe = (E[r] - Rf) / σ",
        "descripcion": "Retorno por unidad de riesgo total, sobre la tasa libre de riesgo.",
    },
    "sortino": {
        "formula": "Sortino = (E[r] - Rf) / DownsideDeviation",
        "descripcion": "Como Sharpe, pero penaliza solo el riesgo a la baja.",
    },
    "max_drawdown": {
        "formula": "MDD = min( W_t / max_{s≤t} W_s - 1 )",
        "descripcion": "Peor caída acumulada desde un máximo previo.",
    },
    "var_historico": {
        "formula": "VaR_c = - percentil(r, 1 - c)",
        "descripcion": "Pérdida que no se supera con probabilidad c (histórico).",
    },
    "cvar": {
        "formula": "CVaR_c = - promedio( r | r ≤ -VaR_c )",
        "descripcion": "Pérdida media en la cola, más allá del VaR (Expected Shortfall).",
    },
    "contribucion_riesgo": {
        "formula": "CC_i = w_i · (Σw)_i / (wᵀΣw)",
        "descripcion": "Fracción del riesgo total de la cartera que aporta cada activo.",
    },
    "herfindahl": {
        "formula": "HHI = Σ w_i²  ;  Nº efectivo = 1 / HHI",
        "descripcion": "Concentración de la cartera (1/n = diversificada, 1 = concentrada).",
    },
    "min_varianza": {
        "formula": "min wᵀΣw  s.a.  Σw = 1, w ≥ 0",
        "descripcion": "Cartera de mínima volatilidad.",
    },
    "max_sharpe": {
        "formula": "max (μᵀw - Rf) / √(wᵀΣw)  s.a.  Σw = 1, w ≥ 0",
        "descripcion": "Cartera tangente (máximo retorno ajustado por riesgo).",
    },
    "risk_parity": {
        "formula": "min ½ wᵀΣw - (1/n) Σ ln(w_i)",
        "descripcion": "Cada activo aporta la misma cantidad de riesgo.",
    },
    "frontera_eficiente": {
        "formula": "min wᵀΣw  s.a.  μᵀw ≥ objetivo, Σw = 1, w ≥ 0",
        "descripcion": "Mínima varianza para cada nivel de retorno objetivo.",
    },
    "black_litterman": {
        "formula": "Π = δ Σ w_mkt  ;  posterior combina Π con las views",
        "descripcion": "Retornos de equilibrio implícitos del mercado (más estables).",
    },
    "monte_carlo": {
        "formula": "W_{t+1} = W_t · (1 + r_t) + aporte,  r_t ~ distribución elegida",
        "descripcion": "Miles de trayectorias simuladas del patrimonio a futuro.",
    },
    "estabilidad": {
        "formula": "desv_est de los pesos al re-optimizar sobre remuestreos (bootstrap)",
        "descripcion": "Mide qué tan robusta es la cartera ante cambios en los datos.",
    },
    "solapamiento_etf": {
        "formula": "overlap(A,B) = Σ min(w_a_i, w_b_i)  sobre tenencias en común",
        "descripcion": "Cuánto se pisan dos ETFs por sus tenencias.",
    },
    "look_through": {
        "formula": "exposición_j = Σ_fondos ( w_fondo · peso_j_en_fondo )",
        "descripcion": "Exposición real a cada acción mirando dentro de los ETFs.",
    },
}


def formulas_subset(keys: list[str]) -> dict[str, dict[str, str]]:
    """Devuelve solo las fórmulas pedidas (las que existan)."""
    return {k: FORMULAS[k] for k in keys if k in FORMULAS}
