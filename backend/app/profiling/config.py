"""Configuración de scoring del perfilado (tablas auditables y editables).

Toda la lógica de "qué suma cada respuesta" vive acá, como datos, no escondida
en el código. Cambiar el comportamiento del perfilado = editar estas tablas.

Cada respuesta aporta a una dimensión (0-100) con una confianza (0-1). La
CAPACIDAD financiera actúa como TECHO (se toma el mínimo); la TOLERANCIA
emocional es el deseo. El nivel final = min(tolerancia, techo_capacidad).
"""
from __future__ import annotations

DONT_KNOW = "dont_know"

# --- D1: horizonte (Q3). Base del techo de capacidad. ---
HORIZON_SCORE: dict[str, tuple[float, float]] = {  # opción -> (score, confidence)
    "lt_1y": (10.0, 1.0),
    "y1_3": (30.0, 1.0),
    "y3_5": (50.0, 1.0),
    "y5_10": (75.0, 1.0),
    "gt_10": (95.0, 1.0),
    "no_date": (55.0, 0.5),
}
# Años representativos para el motor (horizonte -> años).
HORIZON_YEARS: dict[str, int] = {
    "lt_1y": 1, "y1_3": 2, "y3_5": 4, "y5_10": 7, "gt_10": 15, "no_date": 10,
}

# --- D2: liquidez / capacidad financiera (Q4 importancia, Q5 fondo). Topes. ---
CAP_IMPORTANCE: dict[str, float] = {  # Q4 -> tope de riesgo
    "other_savings": 100.0,
    "manageable": 80.0,
    "complicated": 45.0,
    "need_for_expenses": 25.0,
}
CAP_EMERGENCY: dict[str, tuple[float, float]] = {  # Q5 -> (tope, confidence)
    "several_months": (100.0, 1.0),
    "some": (80.0, 1.0),
    "none": (40.0, 1.0),
    "unsure": (60.0, 0.5),
}

# --- D4: tolerancia emocional (Q9 escenario, Q10 umbral, QB branch). ---
TOL_SCENARIO: dict[str, float] = {  # Q9 ; dont_know -> no puntúa
    "sell_all": 10.0, "sell_part": 30.0, "wait": 55.0, "hold": 78.0, "add": 92.0,
}
TOL_THRESHOLD: dict[str, float] = {  # Q10 ; dont_know -> no puntúa
    "at_5": 20.0, "at_10": 40.0, "at_20": 65.0, "at_30": 85.0,
}
TOL_AB: dict[str, float] = {  # QB (branch)
    "def_a": 15.0, "prob_a": 35.0, "unsure": 50.0, "prob_b": 70.0, "def_b": 90.0,
}
TOL_WEIGHTS = {"Q9": 0.6, "Q10": 0.4}
# Sin evidencia de tolerancia -> valor NEUTRO (moderado), NUNCA conservador.
DEFAULT_TOLERANCE = 50.0

# --- D3: estabilidad de aportes (Q8) -> factor de haircut para Monte Carlo. ---
CONTRIB_STABILITY: dict[str, float] = {
    "very_sure": 1.0, "fairly_sure": 0.9, "may_vary": 0.7, "probably_not": 0.5,
}

# --- D5: prioridad del objetivo (Q11) -> umbral de "alarma" en la meta. ---
GOAL_PRIORITY_ALARM: dict[str, float] = {  # prob. mínima deseada de cumplir la meta
    "essential": 0.85, "very_important": 0.75, "flexible": 0.60, "just_growth": 0.0,
}

# --- Q13 exclusiones -> etiquetas que se aplican al universo (Fase 2). ---
EXCLUSION_OPTIONS = {"crypto", "individual_companies", "sectors", "none", DONT_KNOW}

# --- Universos por defecto (Fase 2 los aplica). ---
UNIVERSE_GLOBAL = ["VT", "BND", "GLD"]          # default recomendado
UNIVERSE_ARGENTINA = ["ARGT", "GGAL", "YPF", "PAM", "BMA"]  # opción de riesgo alto

# --- Umbrales de decisión / presentación ---
BINDING_GAP = 20.0  # diferencia para marcar capacity/tolerance binding
# Bandas para la etiqueta legible (el nivel interno es continuo).
RISK_BANDS = [
    (0.20, "VERY_CONSERVATIVE"),
    (0.40, "CONSERVATIVE"),
    (0.60, "MODERATE"),
    (0.80, "AGGRESSIVE"),
    (1.01, "VERY_AGGRESSIVE"),
]
# Tope máximo por activo según banda (más conservador = más diversificado).
MAX_WEIGHT_BY_BAND: dict[str, float] = {
    "VERY_CONSERVATIVE": 0.30,
    "CONSERVATIVE": 0.35,
    "MODERATE": 0.40,
    "AGGRESSIVE": 0.45,
    "VERY_AGGRESSIVE": 0.50,
}


def band_label(level: float) -> str:
    for threshold, label in RISK_BANDS:
        if level < threshold:
            return label
    return "VERY_AGGRESSIVE"
