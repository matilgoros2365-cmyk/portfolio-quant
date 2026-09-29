"""Asesor de IA: propone universos de cartera a medida (con fallback curado)."""
from app.core.config import settings
from app.services.ai_advisor.allowlist import ALLOWLIST
from app.services.ai_advisor.base import AIAdvisor, Candidate
from app.services.ai_advisor.openrouter import OpenRouterAdvisor

__all__ = ["AIAdvisor", "Candidate", "ALLOWLIST", "OpenRouterAdvisor", "build_advisor"]


def build_advisor() -> AIAdvisor | None:
    """Crea el asesor si hay key configurada; si no, None (se usa el fallback)."""
    if settings.openrouter_api_key:
        return OpenRouterAdvisor(settings.openrouter_api_key, settings.openrouter_model)
    return None
