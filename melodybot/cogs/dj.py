"""Diferencial do MelodyBot: DJ com IA, autoplay e retrospectiva do servidor."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from .. import ui
from ..bot import MelodyBot
from ..music.filters import FILTER_LABELS, AudioFilter
from ..music.track import TrackResolveError, resolve_query
from ..plans import Plan

log = logging.getLogger("melodybot.cogs.dj")

MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


class DJCog(commands.Cog):
    def __init__(self, bot: MelodyBot) -> None:
        self.bot = bot

    def _music_cog(self):
        return self.bot.get_cog("MusicCog")

    @app_commands.command(
        name="vibe",
        description="DJ com IA: descreva o momento e o bot monta a fila.",
    )
    @app_commands.describe(mood="Ex: 'sexta relaxante', 'treino pesado', 'pagode de churrasco'")
    async def vibe(self, interaction: discord.Interaction, mood: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)

        # Feature Premium.
        plan = await self.bot.get_plan(interaction.guild.id)
        if plan != Plan.PREMIUM:
            return await interaction.response.send_message(
                embed=ui.simple(
                    "✨ /vibe é uma feature Premium",
                    "O DJ com IA monta filas sob medida pro momento.\nUse `/premium`.",
                    color=ui.GOLD,
                ),
                ephemeral=True,
            )

        if not self.bot.ai.enabled:
            return await interaction.response.send_message(
                embed=ui.simple("🤖 IA não configurada neste bot.", color=ui.WARN),
                ephemeral=True,
            )

        # Precisa estar num canal de voz.
        user = interaction.user
        if not isinstance(user, discord.Member) or user.voice is None:
            return await interaction.response.send_message(
                embed=ui.simple("🎧 Entra num canal de voz primeiro!", color=ui.WARN),
                ephemeral=True,
            )

        await interaction.response.defer()

        recent = await self.bot.db.recent_titles(interaction.guild.id, limit=15)
        suggestions = await self.bot.ai.suggest_tracks(mood, count=5, context=recent)
        if not suggestions:
            return await interaction.followup.send(
                embed=ui.simple(
                    "🤔 Não consegui montar uma vibe pra isso",
                    "Tenta descrever de outro jeito.",
                    color=ui.WARN,
                )
            )

        music_cog = self._music_cog()
        channel = user.voice.channel
        vc = interaction.guild.voice_client or await channel.connect()
        if vc.channel != channel:
            await vc.move_to(channel)

        player = self.bot.players.get(interaction.guild)
        if music_cog is not None:
            music_cog._attach_change_handler(player)

        added: list[str] = []
        for query in suggestions:
            try:
                track = await resolve_query(query, requester_id=user.id)
            except TrackResolveError:
                continue
            player.enqueue(track)
            added.append(track.title)

        if not added:
            return await interaction.followup.send(
                embed=ui.simple("😕 Não achei as faixas sugeridas.", color=ui.WARN)
            )

        player.start()
        lines = "\n".join(f"`{i}.` {t}" for i, t in enumerate(added, start=1))
        emb = ui.simple(f"🎧 Vibe: {mood}", f"Montei sua fila:\n{lines}", color=ui.ACCENT)
        await interaction.followup.send(embed=emb)

    @app_commands.command(
        name="autoplay",
        description="Liga/desliga o rádio inteligente (continua tocando quando a fila acaba).",
    )
    async def autoplay(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)

        plan = await self.bot.get_plan(interaction.guild.id)
        if plan != Plan.PREMIUM:
            return await interaction.response.send_message(
                embed=ui.simple(
                    "✨ Autoplay é uma feature Premium",
                    "O rádio inteligente segue tocando faixas parecidas.\nUse `/premium`.",
                    color=ui.GOLD,
                ),
                ephemeral=True,
            )
        if not self.bot.ai.enabled:
            return await interaction.response.send_message(
                embed=ui.simple("🤖 IA não configurada neste bot.", color=ui.WARN),
                ephemeral=True,
            )

        music_cog = self._music_cog()
        if music_cog is None:
            return await interaction.response.send_message("Indisponível.", ephemeral=True)

        gid = interaction.guild.id
        if gid in music_cog.autoplay_guilds:
            music_cog.autoplay_guilds.discard(gid)
            state = "desligado"
        else:
            music_cog.autoplay_guilds.add(gid)
            state = "ligado"
        await interaction.response.send_message(
            embed=ui.simple(f"📻 Rádio inteligente {state}", color=ui.OK)
        )

    @app_commands.command(
        name="filter",
        description="Aplica um filtro de audio (bass boost, nightcore, etc.).",
    )
    @app_commands.choices(
        preset=[
            app_commands.Choice(name="Nenhum", value="none"),
            app_commands.Choice(name="Bass Boost", value="bassboost"),
            app_commands.Choice(name="Nightcore", value="nightcore"),
            app_commands.Choice(name="Vaporwave", value="vaporwave"),
            app_commands.Choice(name="8D", value="8d"),
            app_commands.Choice(name="Treble", value="treble"),
        ]
    )
    async def filter(
        self, interaction: discord.Interaction, preset: app_commands.Choice[str]
    ) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)

        plan = await self.bot.get_plan(interaction.guild.id)
        if plan != Plan.PREMIUM:
            return await interaction.response.send_message(
                embed=ui.simple(
                    "✨ Filtros de áudio são Premium",
                    "Bass boost, nightcore, 8D e mais.\nUse `/premium`.",
                    color=ui.GOLD,
                ),
                ephemeral=True,
            )

        player = self.bot.players.get_if_exists(interaction.guild.id)
        if player is None or player.current is None:
            return await interaction.response.send_message(
                embed=ui.simple("🎧 Nada tocando pra filtrar.", color=ui.WARN),
                ephemeral=True,
            )

        audio_filter = AudioFilter(preset.value)
        player.apply_filter(audio_filter)
        detail = (
            "Aplicado à faixa atual."
            if audio_filter != AudioFilter.NONE
            else "Filtro removido."
        )
        await interaction.response.send_message(
            embed=ui.simple(f"🎛️ Filtro: {FILTER_LABELS[audio_filter]}", detail, color=ui.OK)
        )

    @app_commands.command(
        name="wrapped",
        description="Retrospectiva do servidor: as mais tocadas e quem mais pediu.",
    )
    async def wrapped(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)

        gid = interaction.guild.id
        total = await self.bot.db.total_plays(gid)
        if total == 0:
            return await interaction.response.send_message(
                embed=ui.simple(
                    "📊 Ainda sem histórico",
                    "Toquem algumas músicas e voltem aqui!",
                    color=ui.ACCENT,
                ),
                ephemeral=True,
            )

        top = await self.bot.db.top_tracks(gid, limit=5)
        requesters = await self.bot.db.top_requesters(gid, limit=3)

        emb = discord.Embed(color=ui.GOLD)
        emb.set_author(
            name=f"MelodyBot Wrapped · {interaction.guild.name}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
        )
        emb.description = f"🎶 **{total}** faixas tocadas no total."

        if top:
            top_lines = "\n".join(
                f"{MEDALS[i]} **{title}** · `{plays}x`"
                for i, (title, plays) in enumerate(top)
            )
            emb.add_field(name="🔥 Mais tocadas", value=top_lines, inline=False)

        if requesters:
            req_lines = []
            for i, (uid, plays) in enumerate(requesters):
                member = interaction.guild.get_member(uid)
                name = member.display_name if member else f"Usuário {uid}"
                req_lines.append(f"{MEDALS[i]} {name} · `{plays}` pedidos")
            emb.add_field(name="🎤 Quem mais pediu", value="\n".join(req_lines), inline=False)

        emb.set_footer(text="MelodyBot · música paraense 🎶")
        await interaction.response.send_message(embed=emb)


async def setup(bot: MelodyBot) -> None:
    await bot.add_cog(DJCog(bot))
