"""Factory de providers de IA."""

from __future__ import annotations

import logging

from ..config import Settings
from .base import AIProvider
from .noop import NoopAIProvider

log = logging.getLogger("melodybot.ai")


def build_ai_provider(settings: Settings) -> AIProvider:
    provider = settings.ai_provider.lower().strip()

    if provider in ("", "none"):
        return NoopAIProvider()

    if provider == "gemini":
        from .gemini import GeminiAIProvider

        try:
            return GeminiAIProvider(api_key=settings.gemini_api_key)
        except RuntimeError as exc:
            log.warning("IA (Gemini) desabilitada: %s", exc)
            return NoopAIProvider()

    log.warning("AI_PROVIDER desconhecido: %s. IA desabilitada.", provider)
    return NoopAIProvider()
