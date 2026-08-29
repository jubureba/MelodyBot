"""Ponto de entrada: python -m melodybot"""

from __future__ import annotations

import asyncio
import logging

from .bot import MelodyBot
from .config import Settings
from .logging_setup import setup_logging
from .webhook import WebhookServer

log = logging.getLogger("melodybot")


async def _run() -> None:
    settings = Settings.load()
    setup_logging(settings.log_level)

    bot = MelodyBot(settings)

    webhook: WebhookServer | None = None
    if settings.payments_enabled:
        webhook = WebhookServer(bot)

    async with bot:
        if webhook is not None:
            await webhook.start()
        try:
            await bot.start(settings.discord_token)
        finally:
            if webhook is not None:
                await webhook.stop()


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        log.info("Encerrando MelodyBot.")


if __name__ == "__main__":
    main()
