"""Motor de scoring del perfilado (funciones puras, auditable).

Toma las respuestas del cuestionario y produce el perfil: score + confidence
por dimensión (con las contribuciones de cada respuesta), el techo de
capacidad, la tolerancia, el nivel de riesgo final [0,1], la etiqueta, las
banderas de conflicto y los parámetros financieros derivados.

Reglas clave:
- La capacidad financiera es un TECHO (se toma el mínimo).
- La tolerancia sin evidencia = NEUTRO (50), nunca conservador.
- "No sé" no puntúa y baja la confianza (no se interpreta como conservador).
- nivel_final = min(tolerancia, techo_capacidad).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.profiling import config as C


@dataclass(slots=True)
class DimensionResult:
    name: str
    score: float
    confidence: float
    evidence_count: int
    contributions: list[dict] = field(default_factory=list)


@dataclass(slots=True)
class ProfileResult:
    dimensions: dict[str, DimensionResult]
    techo_capacidad: float
    tolerancia: float
    risk_level: float          # 0-1 (lo que consume portfolio_for_risk_level)
    risk_label: str
    max_weight: float
    capacity_binding: bool
    tolerance_binding: bool
    overall_confidence: float
    horizon_years: int | None
    mc_contribution_factor: float
    goal_priority: str | None
    goal_alarm_prob: float
    exclusions: list[str]


def score_profile(answers: dict) -> ProfileResult:
    dims: dict[str, DimensionResult] = {}

    # --- D1 horizonte ---
    q3 = answers.get("Q3")
    if q3 in C.HORIZON_SCORE:
        h_score, h_conf = C.HORIZON_SCORE[q3]
        h_ev = 1
        h_contrib = [{"question": "Q3", "answer": q3, "score": h_score}]
    else:
        h_score, h_conf, h_ev, h_contrib = 55.0, 0.3, 0, []
    dims["horizon"] = DimensionResult("horizon", h_score, h_conf, h_ev, h_contrib)

    # --- D2 liquidez / capacidad (topes; se toma el mínimo) ---
    caps: list[float] = [h_score]  # el horizonte también es parte del techo
    liq_contrib: list[dict] = []
    liq_conf_parts: list[float] = []
    q4 = answers.get("Q4")
    if q4 in C.CAP_IMPORTANCE:
        caps.append(C.CAP_IMPORTANCE[q4])
        liq_contrib.append({"question": "Q4", "answer": q4, "cap": C.CAP_IMPORTANCE[q4]})
        liq_conf_parts.append(1.0)
    q5 = answers.get("Q5")
    if q5 in C.CAP_EMERGENCY:
        cap5, conf5 = C.CAP_EMERGENCY[q5]
        caps.append(cap5)
        liq_contrib.append({"question": "Q5", "answer": q5, "cap": cap5})
        liq_conf_parts.append(conf5)
    liquidity_cap = min(caps)
    liq_conf = sum(liq_conf_parts) / 2 if liq_conf_parts else 0.3
    dims["liquidity"] = DimensionResult(
        "liquidity", liquidity_cap, min(liq_conf, 1.0), len(liq_conf_parts), liq_contrib
    )

    techo_capacidad = min(caps)

    # --- D4 tolerancia emocional ---
    tol_parts: list[tuple[float, float]] = []  # (score, weight)
    tol_contrib: list[dict] = []
    q9 = answers.get("Q9")
    if q9 in C.TOL_SCENARIO:
        tol_parts.append((C.TOL_SCENARIO[q9], C.TOL_WEIGHTS["Q9"]))
        tol_contrib.append({"question": "Q9", "answer": q9, "score": C.TOL_SCENARIO[q9]})
    q10 = answers.get("Q10")
    if q10 in C.TOL_THRESHOLD:
        tol_parts.append((C.TOL_THRESHOLD[q10], C.TOL_WEIGHTS["Q10"]))
        tol_contrib.append({"question": "Q10", "answer": q10, "score": C.TOL_THRESHOLD[q10]})
    if not tol_parts:
        qb = answers.get("QB")
        if qb in C.TOL_AB:
            tol_parts.append((C.TOL_AB[qb], 1.0))
            tol_contrib.append({"question": "QB", "answer": qb, "score": C.TOL_AB[qb]})

    if tol_parts:
        w_total = sum(w for _, w in tol_parts)
        tolerancia = sum(s * w for s, w in tol_parts) / w_total
        tol_conf = min(w_total / (C.TOL_WEIGHTS["Q9"] + C.TOL_WEIGHTS["Q10"]), 1.0)
        tol_ev = len(tol_parts)
    else:
        tolerancia = C.DEFAULT_TOLERANCE  # neutro, NO conservador
        tol_conf = 0.0
        tol_ev = 0
    dims["risk_tolerance"] = DimensionResult(
        "risk_tolerance", tolerancia, tol_conf, tol_ev, tol_contrib
    )

    # --- Decisión: capacidad manda ---
    nivel_100 = min(tolerancia, techo_capacidad)
    risk_level = round(nivel_100 / 100.0, 4)
    risk_label = C.band_label(risk_level)
    max_weight = C.MAX_WEIGHT_BY_BAND[risk_label]
    capacity_binding = (tolerancia - techo_capacidad) > C.BINDING_GAP
    tolerance_binding = (techo_capacidad - tolerancia) > C.BINDING_GAP

    # --- D3 aportes (haircut Monte Carlo) ---
    q8 = answers.get("Q8")
    mc_factor = C.CONTRIB_STABILITY.get(q8, 1.0)

    # --- D5 prioridad del objetivo ---
    q11 = answers.get("Q11")
    goal_alarm = C.GOAL_PRIORITY_ALARM.get(q11, 0.60)

    # --- Q13 exclusiones ---
    raw_excl = answers.get("Q13", [])
    if isinstance(raw_excl, str):
        raw_excl = [raw_excl]
    exclusions = [e for e in raw_excl if e not in ("none", C.DONT_KNOW)]

    horizon_years = C.HORIZON_YEARS.get(q3)

    overall_conf = round(
        (dims["horizon"].confidence + dims["liquidity"].confidence + dims["risk_tolerance"].confidence)
        / 3.0,
        3,
    )

    return ProfileResult(
        dimensions=dims,
        techo_capacidad=round(techo_capacidad, 2),
        tolerancia=round(tolerancia, 2),
        risk_level=risk_level,
        risk_label=risk_label,
        max_weight=max_weight,
        capacity_binding=capacity_binding,
        tolerance_binding=tolerance_binding,
        overall_confidence=overall_conf,
        horizon_years=horizon_years,
        mc_contribution_factor=mc_factor,
        goal_priority=q11,
        goal_alarm_prob=goal_alarm,
        exclusions=exclusions,
    )
