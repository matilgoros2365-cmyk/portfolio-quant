"""Modelos de cartera: distintos conjuntos de activos, con su lógica y riesgos.

En vez de armar siempre la cartera con los mismos activos, definimos varios
"modelos" (canastas diferentes). Según el perfil se elige uno como primario y
los demás se ofrecen como alternativas, explicando por qué elegir cada una y
qué riesgo implica.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.profiling.universe import TICKER_TAGS, filter_tickers


@dataclass(slots=True)
class ModelUniverse:
    id: str
    name: str
    tickers: list[str]
    description: str   # qué es
    rationale: str     # por qué elegirla
    risks: str         # riesgo de elegirla


MODELS: list[ModelUniverse] = [
    ModelUniverse(
        id="global_div",
        name="Global diversificada",
        tickers=["VT", "BND", "GLD"],
        description="Acciones de todo el mundo, bonos y oro.",
        rationale="Es la más diversificada y simple: repartís el riesgo entre miles de empresas de muchos países, más bonos y oro que amortiguan las caídas.",
        risks="Al estar tan repartida, en años muy buenos de un sector puntual crece menos que una apuesta concentrada. Igual cae en crisis globales.",
    ),
    ModelUniverse(
        id="us_core",
        name="Clásica de Estados Unidos",
        tickers=["VOO", "BND", "GLD"],
        description="Las 500 empresas más grandes de EE.UU. (S&P 500), bonos y oro.",
        rationale="Apuesta al mercado más grande, líquido y estudiado del mundo. Históricamente muy sólido a largo plazo.",
        risks="Queda concentrada en un solo país: si a EE.UU. le va mal (o su moneda), lo sentís más. Menos exposición internacional.",
    ),
    ModelUniverse(
        id="growth_tech",
        name="Crecimiento y tecnología",
        tickers=["QQQ", "VOO", "GLD"],
        description="Nasdaq-100 (tecnológicas) + S&P 500 + oro.",
        rationale="Mayor potencial de crecimiento a largo plazo, apoyándose en las empresas más innovadoras.",
        risks="Mucha tecnología concentrada: es más volátil y las caídas pueden ser más profundas y largas (por ejemplo 2022 o la burbuja puntocom).",
    ),
    ModelUniverse(
        id="income_stability",
        name="Estabilidad e ingresos",
        tickers=["BND", "TLT", "VOO", "GLD"],
        description="Mayoría en bonos (cortos y largos), algo de acciones y oro.",
        rationale="Prioriza la estabilidad y variaciones más suaves. Buena si querés dormir tranquilo o necesitás el dinero relativamente pronto.",
        risks="El crecimiento a largo plazo es más limitado. Los bonos largos (TLT) sufren cuando suben las tasas de interés.",
    ),
    ModelUniverse(
        id="argentina_tilt",
        name="Con exposición a Argentina",
        tickers=["VT", "BND", "GLD", "ARGT"],
        description="Cartera global diversificada más un ETF de empresas argentinas (en dólares).",
        rationale="Suma algo de potencial local manteniendo una base global diversificada.",
        risks="Argentina tiene riesgo país alto: mucha volatilidad y riesgo político y cambiario. Conviene solo como parte chica y si tolerás sobresaltos.",
    ),
]

_BY_ID = {m.id: m for m in MODELS}


def get_model(model_id: str) -> ModelUniverse | None:
    return _BY_ID.get(model_id)


def select_primary(goal_type: str | None, risk_label: str | None) -> ModelUniverse:
    """Elige el modelo primario según objetivo y nivel de riesgo del perfil."""
    conservative = risk_label in ("VERY_CONSERVATIVE", "CONSERVATIVE")
    aggressive = risk_label in ("AGGRESSIVE", "VERY_AGGRESSIVE")

    if goal_type in ("retirement", "income") and not aggressive:
        return _BY_ID["income_stability"]
    if conservative:
        return _BY_ID["income_stability"]
    if aggressive:
        return _BY_ID["growth_tech"]
    return _BY_ID["global_div"]  # moderado


def available_models(exclusions: list[str] | None = None) -> list[ModelUniverse]:
    """Modelos cuyos tickers sobreviven a las exclusiones (al menos 2 activos)."""
    out = []
    for m in MODELS:
        if len(filter_tickers(m.tickers, exclusions)) >= 2:
            out.append(m)
    return out


def model_tickers(model: ModelUniverse, exclusions: list[str] | None = None) -> list[str]:
    return filter_tickers(model.tickers, exclusions)
