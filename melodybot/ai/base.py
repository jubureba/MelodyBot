"""Interface de provider de IA (plugavel) para o DJ inteligente."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Contrato para geradores de sugestoes de musica por linguagem natural."""

    name: str = "base"

    @property
    def enabled(self) -> bool:
        return True

    @abstractmethod
    async def suggest_tracks(
        self, mood: str, count: int, context: list[str] | None = None
    ) -> list[str]:
        """Retorna uma lista de buscas de musica (ex: 'Artista - Musica').

        mood: descricao livre do momento/humor.
        count: quantas faixas sugerir.
        context: faixas recentes do servidor (para dar coerencia/gosto).
        """
