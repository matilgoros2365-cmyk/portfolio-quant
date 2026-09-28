"""Tests del universo por defecto y del resolver de nivel de riesgo."""
from __future__ import annotations

import pytest

from app.models.portfolio import RiskProfile
from app.profiling.universe import build_universe
from app.services.optimizer import resolve_risk_level


def test_universe_global_default() -> None:
    assert build_universe("global") == ["VT", "BND", "GLD"]


def test_universe_argentina_adds_argt() -> None:
    assert build_universe("argentina") == ["VT", "BND", "GLD", "ARGT"]


def test_universe_exclusions_filter_adrs() -> None:
    # argentina_plus trae ADRs individuales; excluir empresas individuales los saca.
    universe = build_universe("argentina_plus", ["individual_companies"])
    assert "ARGT" in universe          # ETF amplio se queda
    assert "GGAL" not in universe      # ADR individual se va
    assert universe[:3] == ["VT", "BND", "GLD"]


def test_universe_crypto_exclusion_noop_on_default() -> None:
    # No hay cripto en la canasta default: excluirla no cambia nada.
    assert build_universe("global", ["crypto"]) == ["VT", "BND", "GLD"]


def test_resolve_from_continuous_level() -> None:
    level, profile = resolve_risk_level(risk_level=0.10)
    assert level == pytest.approx(0.10)
    assert profile == RiskProfile.VERY_CONSERVATIVE

    level, profile = resolve_risk_level(risk_level=0.5)
    assert profile == RiskProfile.MODERATE


def test_resolve_from_enum() -> None:
    level, profile = resolve_risk_level(risk_profile=RiskProfile.AGGRESSIVE)
    assert level == pytest.approx(0.75)
    assert profile == RiskProfile.AGGRESSIVE


def test_resolve_requires_something() -> None:
    with pytest.raises(Exception):
        resolve_risk_level()
