"""Servidor de webhook para confirmar pagamentos e ativar o Premium.

Roda junto ao bot (mesmo processo) num pequeno servidor aiohttp. So sobe
se pagamentos estiverem habilitados.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from aiohttp import web

from .bot import MelodyBot
from .plans import Plan

log = logging.getLogger("melodybot.webhook")

PREMIUM_DURATION = timedelta(days=30)


class WebhookServer:
    def __init__(self, bot: MelodyBot) -> None:
        self.bot = bot
        self._runner: web.AppRunner | None = None

    async def start(self) -> None:
        app = web.Application()
        app.router.add_post("/webhook/{provider}", self._handle)
        app.router.add_get("/health", self._health)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "0.0.0.0", self.bot.settings.webhook_port)
        await site.start()
        log.info("Webhook server ouvindo na porta %d", self.bot.settings.webhook_port)

    async def stop(self) -> None:
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None

    async def _health(self, _request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def _handle(self, request: web.Request) -> web.Response:
        try:
            payload = await request.json()
        except Exception:  # noqa: BLE001
            payload = {}
        query = dict(request.query)

        event = await self.bot.payments.parse_webhook(payload, query)
        if event is None:
            return web.json_response({"ignored": True})

        log.info("Webhook: status=%s guild=%s", event.status, event.guild_id)

        if event.status == "approved" and event.guild_id is not None:
            active_until = datetime.now(UTC) + PREMIUM_DURATION
            await self.bot.db.set_plan(event.guild_id, Plan.PREMIUM, active_until)
            await self.bot.db.record_payment(
                guild_id=event.guild_id,
                provider=self.bot.payments.name,
                external_id=event.external_id,
                status="approved",
                amount=event.amount,
            )
            log.info("Premium ativado para guild %s ate %s", event.guild_id, active_until)

        return web.json_response({"ok": True})
