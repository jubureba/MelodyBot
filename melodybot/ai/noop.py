"""Provider de IA nulo: usado quando a IA esta desabilitada."""

from __future__ import annotations

from .base import AIProvider


class NoopAIProvider(AIProvider):
    name = "none"

    @property
    def enabled(self) -> bool:
        return False

    async def suggest_tracks(
        self, mood: str, count: int, context: list[str] | None = None
    ) -> list[str]:
        return []
