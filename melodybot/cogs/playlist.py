"""Playlists salvas por servidor (feature Premium)."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from .. import ui
from ..bot import MelodyBot
from ..music.track import TrackResolveError, resolve_query
from ..plans import Plan

log = logging.getLogger("melodybot.cogs.playlist")

MAX_PLAYLISTS = 25
MAX_ITEMS = 100


async def _require_premium(interaction: discord.Interaction, bot: MelodyBot) -> bool:
    if interaction.guild is None:
        await interaction.response.send_message("Use em um servidor.", ephemeral=True)
        return False
    plan = await bot.get_plan(interaction.guild.id)
    if plan != Plan.PREMIUM:
        await interaction.response.send_message(
            embed=ui.simple(
                "✨ Playlists salvas são Premium",
                "Salve e recarregue filas inteiras.\nUse `/premium`.",
                color=ui.GOLD,
            ),
            ephemeral=True,
        )
        return False
    return True


class PlaylistCog(commands.Cog):
    def __init__(self, bot: MelodyBot) -> None:
        self.bot = bot

    group = app_commands.Group(name="playlist", description="Playlists salvas do servidor.")

    @group.command(name="save", description="Salva a fila atual como uma playlist.")
    @app_commands.describe(name="Nome da playlist")
    async def save(self, interaction: discord.Interaction, name: str) -> None:
        if not await _require_premium(interaction, self.bot):
            return
        assert interaction.guild is not None

        player = self.bot.players.get_if_exists(interaction.guild.id)
        items: list[tuple[str, str]] = []
        if player is not None:
            if player.current is not None:
                items.append((player.current.title, player.current.webpage_url))
            items.extend((t.title, t.webpage_url) for t in player.queue)

        if not items:
            return await interaction.response.send_message(
                embed=ui.simple("🎧 Nada na fila pra salvar.", color=ui.WARN),
                ephemeral=True,
            )

        existing = await self.bot.db.list_playlists(interaction.guild.id)
        if len(existing) >= MAX_PLAYLISTS and name not in {n for n, _ in existing}:
            return await interaction.response.send_message(
                embed=ui.simple(
                    "📚 Limite de playlists atingido",
                    f"Máximo de {MAX_PLAYLISTS} por servidor.",
                    color=ui.WARN,
                ),
                ephemeral=True,
            )

        saved = await self.bot.db.save_playlist(interaction.guild.id, name, items[:MAX_ITEMS])
        await interaction.response.send_message(
            embed=ui.simple(
                f"💾 Playlist “{name}” salva",
                f"{saved} faixa(s) guardadas.",
                color=ui.OK,
            )
        )

    @group.command(name="list", description="Lista as playlists salvas.")
    async def list_cmd(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)
        playlists = await self.bot.db.list_playlists(interaction.guild.id)
        if not playlists:
            return await interaction.response.send_message(
                embed=ui.simple("📭 Nenhuma playlist salva ainda.", color=ui.ACCENT),
                ephemeral=True,
            )
        lines = "\n".join(f"• **{name}** · `{n}` faixa(s)" for name, n in playlists)
        await interaction.response.send_message(
            embed=ui.simple("📚 Playlists do servidor", lines, color=ui.ACCENT)
        )

    @group.command(name="load", description="Carrega uma playlist na fila.")
    @app_commands.describe(name="Nome da playlist")
    async def load(self, interaction: discord.Interaction, name: str) -> None:
        if not await _require_premium(interaction, self.bot):
            return
        assert interaction.guild is not None

        user = interaction.user
        if not isinstance(user, discord.Member) or user.voice is None:
            return await interaction.response.send_message(
                embed=ui.simple("🎧 Entra num canal de voz primeiro!", color=ui.WARN),
                ephemeral=True,
            )

        items = await self.bot.db.get_playlist_items(interaction.guild.id, name)
        if not items:
            return await interaction.response.send_message(
                embed=ui.simple(f"❓ Playlist “{name}” não encontrada.", color=ui.WARN),
                ephemeral=True,
            )

        await interaction.response.defer()

        channel = user.voice.channel
        vc = interaction.guild.voice_client or await channel.connect()
        if vc.channel != channel:
            await vc.move_to(channel)

        player = self.bot.players.get(interaction.guild)
        music_cog = self.bot.get_cog("MusicCog")
        if music_cog is not None:
            music_cog._attach_change_handler(player)

        loaded = 0
        for _title, url in items:
            try:
                track = await resolve_query(url, requester_id=user.id)
            except TrackResolveError:
                continue
            player.enqueue(track)
            loaded += 1

        if loaded == 0:
            return await interaction.followup.send(
                embed=ui.simple("😕 Não consegui carregar as faixas.", color=ui.WARN)
            )

        player.start()
        await interaction.followup.send(
            embed=ui.simple(
                f"▶️ Playlist “{name}” carregada",
                f"{loaded} faixa(s) na fila.",
                color=ui.OK,
            )
        )

    @group.command(name="delete", description="Apaga uma playlist salva.")
    @app_commands.describe(name="Nome da playlist")
    async def delete(self, interaction: discord.Interaction, name: str) -> None:
        if not await _require_premium(interaction, self.bot):
            return
        assert interaction.guild is not None
        ok = await self.bot.db.delete_playlist(interaction.guild.id, name)
        if ok:
            await interaction.response.send_message(
                embed=ui.simple(f"🗑️ Playlist “{name}” apagada.", color=ui.OK)
            )
        else:
            await interaction.response.send_message(
                embed=ui.simple(f"❓ Playlist “{name}” não encontrada.", color=ui.WARN),
                ephemeral=True,
            )


async def setup(bot: MelodyBot) -> None:
    await bot.add_cog(PlaylistCog(bot))
