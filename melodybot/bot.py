"""Classe principal do bot: junta config, banco, planos e player."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from .ai import build_ai_provider
from .ai.base import AIProvider
from .config import Settings
from .database import Database
from .music.manager import PlayerManager
from .payments import build_payment_provider
from .payments.base import PaymentProvider
from .plans import Plan, PlanLimits, build_plan_table

log = logging.getLogger("melodybot")

INITIAL_COGS = [
    "melodybot.cogs.music",
    "melodybot.cogs.premium",
    "melodybot.cogs.dj",
    "melodybot.cogs.playlist",
]


class MelodyBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = False  # slash commands nao precisam
        intents.voice_states = True
        intents.guilds = True

        super().__init__(command_prefix="!", intents=intents, help_command=None)

        self.settings = settings
        self.db = Database(settings.database_path)
        self.players = PlayerManager()
        self._plan_table = build_plan_table(
            settings.free_queue_limit, settings.free_max_track_seconds
        )
        self.payments: PaymentProvider = build_payment_provider(settings)
        self.ai: AIProvider = build_ai_provider(settings)

    # --- Planos ---

    async def get_plan(self, guild_id: int) -> Plan:
        return await self.db.get_plan(guild_id)

    def limits_for(self, plan: Plan) -> PlanLimits:
        return self._plan_table[plan]

    async def limits_for_guild(self, guild_id: int) -> PlanLimits:
        return self.limits_for(await self.get_plan(guild_id))

    # --- Ciclo de vida ---

    async def setup_hook(self) -> None:
        await self.db.connect()
        log.info("Banco conectado em %s", self.settings.database_path)

        for cog in INITIAL_COGS:
            await self.load_extension(cog)
            log.info("Cog carregado: %s", cog)

        await self._sync_commands()

    async def _sync_commands(self) -> None:
        """Sincroniza os slash commands.

        Em dev, registra apenas nas guilds de teste (aparecem na hora).
        Para evitar comandos duplicados quando ja houve um sync GLOBAL antes,
        fazemos um unico sync global vazio de limpeza — de forma isolada, sem
        deixar a arvore local sem comandos.
        """
        if not self.settings.dev_guild_ids:
            await self.tree.sync()
            log.info("Slash commands sincronizados globalmente")
            return

        # 1) Remove comandos globais remanescentes no Discord (nao mexe na
        #    arvore local: get_commands continua com tudo). Um sync global
        #    "vazio" so acontece se realmente existirem globais registrados.
        try:
            existing_global = await self.tree.fetch_commands()
            if existing_global:
                # Copia temporariamente a arvore, zera os globais e restaura.
                snapshot = list(self.tree.get_commands(guild=None))
                self.tree.clear_commands(guild=None)
                await self.tree.sync()  # apaga os globais no Discord
                for cmd in snapshot:
                    self.tree.add_command(cmd)
        except Exception:  # noqa: BLE001
            log.exception("Falha ao limpar comandos globais (seguindo mesmo assim)")

        # 2) Registra a arvore em cada guild de dev.
        for gid in self.settings.dev_guild_ids:
            guild = discord.Object(id=gid)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

        log.info(
            "Slash commands sincronizados em %d guild(s) de dev",
            len(self.settings.dev_guild_ids),
        )

    async def on_ready(self) -> None:
        log.info("MelodyBot online como %s (id=%s)", self.user, self.user.id if self.user else "?")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="/play | musica paraense"
            )
        )

    async def close(self) -> None:
        await self.db.close()
        await super().close()
