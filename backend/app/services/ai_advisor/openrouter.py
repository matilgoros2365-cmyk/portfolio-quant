"""Asesor de IA vía OpenRouter (API compatible con OpenAI, con modelos gratis).

La IA propone conjuntos de activos a medida del perfil, eligiendo SOLO de la
lista vetada. Todo se valida: tickers fuera de la lista se descartan. Si algo
falla (sin key, red, JSON inválido), devuelve None y el sistema usa el fallback.
"""
from __future__ import annotations

import json
import re

import requests

from app.services.ai_advisor.base import AIAdvisor, Candidate

_URL = "https://openrouter.ai/api/v1/chat/completions"

_SYSTEM = (
    "Sos un asistente de planificación financiera prudente para personas que no "
    "saben nada de inversiones. Proponés carteras diversificadas de ETFs eligiendo "
    "SOLO de un menú fijo que te dan. Nunca inventás tickers ni das números de "
    "rendimiento o probabilidades (de eso se encarga otro motor). Respondés siempre "
    "en español, en JSON válido y nada más."
)


def _build_prompt(context: dict, allowlist: dict[str, str]) -> str:
    menu = "\n".join(f"- {t}: {desc}" for t, desc in allowlist.items())
    excl = context.get("exclusions") or []
    excl_txt = ", ".join(excl) if excl else "ninguna"
    return f"""PERFIL DE LA PERSONA:
- Objetivo: {context.get('goal_type')}
- Horizonte: {context.get('horizon_years')} años
- Nivel de riesgo (etiqueta interna): {context.get('risk_label')}
- ¿Podría necesitar el dinero pronto?: {"sí" if context.get('short_horizon') else "no"}
- Moneda de referencia: {context.get('currency')}
- Exclusiones pedidas: {excl_txt}

MENÚ DE INSTRUMENTOS PERMITIDOS (elegí solo de acá):
{menu}

TAREA:
Proponé 2 o 3 carteras candidatas pensadas para esta persona. Cada una con 3 a 5
tickers del menú, bien diversificada y coherente con su perfil. La PRIMERA es la
recomendada. Respetá las exclusiones. No repitas exactamente la misma cartera.

Respondé SOLO con JSON, sin texto extra, con esta forma:
{{"carteras": [
  {{"nombre": "Nombre corto", "tickers": ["VT","BND","GLD"],
    "por_que": "Por qué le conviene a esta persona (1-2 frases).",
    "riesgo": "Qué riesgo implica elegirla (1-2 frases)."}}
]}}"""


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    # Sacar cercos de código markdown si los hay.
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _parse_candidates(content: str, allowlist: dict[str, str]) -> list[Candidate] | None:
    data = _extract_json(content)
    if not data or "carteras" not in data:
        return None
    out: list[Candidate] = []
    for i, c in enumerate(data["carteras"]):
        if not isinstance(c, dict):
            continue
        raw = c.get("tickers") or []
        tickers = [str(t).upper() for t in raw if str(t).upper() in allowlist]
        # Sin duplicados, máximo 6.
        seen: list[str] = []
        for t in tickers:
            if t not in seen:
                seen.append(t)
        tickers = seen[:6]
        if len(tickers) < 2:
            continue
        out.append(Candidate(
            id=f"ai_{i + 1}",
            name=str(c.get("nombre") or f"Cartera {i + 1}"),
            tickers=tickers,
            description="Propuesta a medida (IA)",
            rationale=str(c.get("por_que") or ""),
            risks=str(c.get("riesgo") or ""),
        ))
    return out or None


class OpenRouterAdvisor(AIAdvisor):
    def __init__(self, api_key: str, model: str = "openrouter/free", timeout: int = 30) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def suggest(self, context: dict, allowlist: dict[str, str]) -> list[Candidate] | None:
        if not self.api_key:
            return None
        try:
            resp = requests.post(
                _URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://portfolioquant.local",
                    "X-Title": "PortfolioQuant",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": _build_prompt(context, allowlist)},
                    ],
                    "temperature": 0.4,
                    "max_tokens": 900,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        except Exception:  # noqa: BLE001 - cualquier fallo -> fallback curado
            return None
        return _parse_candidates(content, allowlist)
