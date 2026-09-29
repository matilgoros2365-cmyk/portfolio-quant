"""Tests de la selección de modelo de cartera y filtrado por exclusiones."""
from __future__ import annotations

from app.profiling.model_portfolios import (
    available_models,
    model_tickers,
    select_primary,
)


def test_select_varies_by_profile() -> None:
    assert select_primary("grow", "AGGRESSIVE").id == "growth_tech"
    assert select_primary("grow", "MODERATE").id == "global_div"
    assert select_primary("grow", "CONSERVATIVE").id == "income_stability"
    assert select_primary("retirement", "MODERATE").id == "income_stability"


def test_available_models_present() -> None:
    ids = {m.id for m in available_models([])}
    assert {"global_div", "us_core", "growth_tech", "income_stability", "argentina_tilt"} <= ids


def test_model_tickers_filter_exclusions() -> None:
    # El modelo argentino con solo ETFs amplios no se ve afectado por excluir empresas.
    tk = model_tickers(next(m for m in available_models([]) if m.id == "argentina_tilt"),
                       ["individual_companies"])
    assert "ARGT" in tk and "VT" in tk
