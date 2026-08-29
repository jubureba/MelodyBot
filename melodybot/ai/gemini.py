"""Provider de IA usando Google Gemini.

O SDK 'google-generativeai' e importado de forma lazy — nao e dependencia
obrigatoria de quem roda o bot sem IA.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

from .base import AIProvider

log = logging.getLogger("melodybot.ai.gemini")

_PROMPT = """Voce e um DJ especialista. Monte uma playlist de {count} musicas \
que combinem com este momento/humor:

"{mood}"

{context_block}

Regras:
- Responda SOMENTE com um array JSON de strings, cada uma no formato "Artista - Musica".
- Musicas reais e conhecidas. Variedade de artistas.
- Nada de texto fora do JSON.

Exemplo de resposta: ["Artista A - Musica 1", "Artista B - Musica 2"]"""


class GeminiAIProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY nao configurado.")
        try:
            import google.generativeai as genai  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "Pacote 'google-generativeai' nao instalado. "
                "Rode: pip install google-generativeai"
            ) from exc
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    async def suggest_tracks(
        self, mood: str, count: int, context: list[str] | None = None
    ) -> list[str]:
        context_block = ""
        if context:
            recent = ", ".join(context[:15])
            context_block = (
                f"O servidor costuma ouvir: {recent}. "
                "Use isso para acertar o gosto, sem repetir exatamente as mesmas."
            )
        prompt = _PROMPT.format(count=count, mood=mood, context_block=context_block)

        loop = asyncio.get_running_loop()
        try:
            response = await loop.run_in_executor(
                None, lambda: self._model.generate_content(prompt)
            )
            text = response.text or ""
        except Exception as exc:  # noqa: BLE001
            log.warning("Falha na chamada Gemini: %s", exc)
            return []

        return self._parse(text, count)

    @staticmethod
    def _parse(text: str, count: int) -> list[str]:
        # Extrai o primeiro array JSON da resposta.
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []
        tracks = [str(item).strip() for item in data if str(item).strip()]
        return tracks[:count]
