"""Tests del asesor de IA (parsing/validación, sin red)."""
from __future__ import annotations

from app.services.ai_advisor.allowlist import ALLOWLIST
from app.services.ai_advisor.openrouter import _parse_candidates


def test_parse_valid_and_filters_unknown_tickers() -> None:
    content = (
        "```json\n"
        '{"carteras":[{"nombre":"Crecimiento","tickers":["QQQ","VOO","GLD","FAKE"],'
        '"por_que":"Potencial","riesgo":"Volátil"},'
        '{"nombre":"Muy corta","tickers":["BND"],"por_que":"x","riesgo":"y"}]}\n'
        "```"
    )
    cands = _parse_candidates(content, ALLOWLIST)
    assert cands is not None
    # La segunda se descarta (menos de 2 tickers válidos).
    assert len(cands) == 1
    c = cands[0]
    assert c.name == "Crecimiento"
    assert c.tickers == ["QQQ", "VOO", "GLD"]  # "FAKE" fuera de la lista se descartó
    assert c.rationale and c.risks


def test_parse_garbage_returns_none() -> None:
    assert _parse_candidates("no soy json", ALLOWLIST) is None
    assert _parse_candidates('{"otra_cosa": 1}', ALLOWLIST) is None
