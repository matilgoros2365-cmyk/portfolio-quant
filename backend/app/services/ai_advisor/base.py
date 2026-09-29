"""Abstracción del asesor de IA que propone universos de cartera."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class Candidate:
    """Una cartera candidata propuesta (por la IA o por los modelos curados)."""

    id: str
    name: str
    tickers: list[str]
    description: str
    rationale: str   # por qué elegirla
    risks: str       # riesgo de elegirla


class AIAdvisor(ABC):
    @abstractmethod
    def suggest(
        self, context: dict, allowlist: dict[str, str]
    ) -> list[Candidate] | None:
        """Propone carteras candidatas a medida del perfil.

        Devuelve la lista (la primera es la recomendada) o None si no se pudo
        (sin key, error de red, respuesta inválida) -> el caller usa el fallback.
        """
