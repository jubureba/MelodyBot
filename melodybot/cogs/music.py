"""Comandos de musica (slash) e UI de controle por botoes."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ..bot import MelodyBot
from ..music.player import GuildPlayer, LoopMode
from ..music.track import TrackResolveError, resolve_query

log = logging.getLogger("melodybot.cogs.music")

ACCENT = 0x22D3EE


def _embed(title: str, description: str = "", color: int = ACCENT) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)


async def _ensure_voice(interaction: discord.Interaction) -> discord.VoiceClient | None:
    """Garante que o bot esteja no canal de voz do usuario. Retorna o voice client."""
    user = interaction.user
    if not isinstance(user, discord.Member) or user.voice is None or user.voice.channel is None:
        await interaction.response.send_message(
            embed=_embed("🎧 Entra num canal de voz primeiro!", color=0xF59E0B),
            ephemeral=True,
        )
        return None

    channel = user.voice.channel
    vc = interaction.guild.voice_client if interaction.guild else None
    if vc is None:
        return await channel.connect()
    if vc.channel != channel:
        await vc.move_to(channel)
    return vc


class MusicControls(discord.ui.View):
    """Botoes de controle exibidos com o 'tocando agora'."""

    def __init__(self, cog: MusicCog, guild_id: int) -> None:
        super().__init__(timeout=None)
        self._cog = cog
        self._guild_id = guild_id

    def _player(self) -> GuildPlayer | None:
        return self._cog.bot.players.get_if_exists(self._guild_id)

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.secondary)
    async def pause_resume(self, interaction: discord.Interaction, _button: discord.ui.Button):
        player = self._player()
        if not player:
            return await interaction.response.send_message("Nada tocando.", ephemeral=True)
        if not player.resume():
            player.pause()
        await interaction.response.defer()

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, _button: discord.ui.Button):
        player = self._player()
        if player:
            player.skip()
        await interaction.response.send_message("⏭️ Pulei.", ephemeral=True)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, _button: discord.ui.Button):
        player = self._player()
        if player:
            player.stop()
        vc = interaction.guild.voice_client if interaction.guild else None
        if vc:
            await vc.disconnect()
        await interaction.response.send_message("⏹️ Parei e sai do canal.", ephemeral=True)


class MusicCog(commands.Cog):
    def __init__(self, bot: MelodyBot) -> None:
        self.bot = bot

    @app_commands.command(name="play", description="Toca uma musica (busca ou URL).")
    @app_commands.describe(query="Nome da musica ou link (YouTube, etc.)")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message(
                "Use em um servidor.", ephemeral=True
            )

        vc = await _ensure_voice(interaction)
        if vc is None:
            return

        await interaction.response.defer()

        try:
            track = await resolve_query(query, requester_id=interaction.user.id)
        except TrackResolveError as exc:
            return await interaction.followup.send(
                embed=_embed("❌ Nao consegui tocar isso", str(exc), color=0xEF4444)
            )

        # Regras do plano: limite de fila e duracao maxima da faixa.
        limits = await self.bot.limits_for_guild(interaction.guild.id)
        player = self.bot.players.get(interaction.guild)

        if limits.max_track_seconds and track.duration > limits.max_track_seconds:
            minutes = limits.max_track_seconds // 60
            return await interaction.followup.send(
                embed=_embed(
                    "🔒 Faixa muito longa para o plano Free",
                    f"O limite e de {minutes} min por faixa. "
                    "Use `/premium` para liberar faixas sem limite.",
                    color=0xF59E0B,
                )
            )

        if limits.queue_limit and player.queue_size >= limits.queue_limit:
            return await interaction.followup.send(
                embed=_embed(
                    "🔒 Fila cheia no plano Free",
                    f"Limite de {limits.queue_limit} faixas. "
                    "Use `/premium` para fila ilimitada.",
                    color=0xF59E0B,
                )
            )

        player.enqueue(track)
        player.start()

        position = player.queue_size
        emb = _embed(
            "🎵 Adicionada à fila" if position > 0 and player.current else "▶️ Tocando agora",
            f"**[{track.title}]({track.webpage_url})**\n`{track.duration_str}`",
        )
        if track.thumbnail:
            emb.set_thumbnail(url=track.thumbnail)
        await interaction.followup.send(
            embed=emb, view=MusicControls(self, interaction.guild.id)
        )

    @app_commands.command(name="skip", description="Pula a faixa atual.")
    async def skip(self, interaction: discord.Interaction) -> None:
        player = self.bot.players.get_if_exists(interaction.guild_id or 0)
        if not player or player.current is None:
            return await interaction.response.send_message("Nada tocando.", ephemeral=True)
        player.skip()
        await interaction.response.send_message("⏭️ Pulei a faixa.")

    @app_commands.command(name="stop", description="Para tudo e limpa a fila.")
    async def stop(self, interaction: discord.Interaction) -> None:
        player = self.bot.players.get_if_exists(interaction.guild_id or 0)
        if player:
            player.stop()
        vc = interaction.guild.voice_client if interaction.guild else None
        if vc:
            await vc.disconnect()
        await interaction.response.send_message("⏹️ Parei e limpei a fila.")

    @app_commands.command(name="pause", description="Pausa a reproducao.")
    async def pause(self, interaction: discord.Interaction) -> None:
        player = self.bot.players.get_if_exists(interaction.guild_id or 0)
        if player and player.pause():
            return await interaction.response.send_message("⏸️ Pausado.")
        await interaction.response.send_message("Nada tocando.", ephemeral=True)

    @app_commands.command(name="resume", description="Retoma a reproducao.")
    async def resume(self, interaction: discord.Interaction) -> None:
        player = self.bot.players.get_if_exists(interaction.guild_id or 0)
        if player and player.resume():
            return await interaction.response.send_message("▶️ Retomado.")
        await interaction.response.send_message("Nada pausado.", ephemeral=True)

    @app_commands.command(name="queue", description="Mostra a fila atual.")
    async def queue(self, interaction: discord.Interaction) -> None:
        player = self.bot.players.get_if_exists(interaction.guild_id or 0)
        if not player or (player.current is None and player.queue_size == 0):
            return await interaction.response.send_message("Fila vazia.", ephemeral=True)

        lines = []
        if player.current:
            lines.append(f"**Tocando:** [{player.current.title}]({player.current.webpage_url})")
        for i, track in enumerate(list(player.queue)[:10], start=1):
            lines.append(f"`{i}.` [{track.title}]({track.webpage_url}) · `{track.duration_str}`")
        if player.queue_size > 10:
            lines.append(f"... e mais {player.queue_size - 10} faixa(s).")

        await interaction.response.send_message(embed=_embed("📜 Fila", "\n".join(lines)))

    @app_commands.command(name="nowplaying", description="Mostra a faixa atual.")
    async def nowplaying(self, interaction: discord.Interaction) -> None:
        player = self.bot.players.get_if_exists(interaction.guild_id or 0)
        if not player or player.current is None:
            return await interaction.response.send_message("Nada tocando.", ephemeral=True)
        track = player.current
        emb = _embed(
            "▶️ Tocando agora",
            f"**[{track.title}]({track.webpage_url})**\n"
            f"`{track.duration_str}` · loop: `{player.loop_mode.value}`",
        )
        if track.thumbnail:
            emb.set_thumbnail(url=track.thumbnail)
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="loop", description="Alterna o modo de repeticao.")
    @app_commands.describe(mode="off, track ou queue")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="Desligado", value="off"),
            app_commands.Choice(name="Faixa", value="track"),
            app_commands.Choice(name="Fila", value="queue"),
        ]
    )
    async def loop(self, interaction: discord.Interaction, mode: app_commands.Choice[str]) -> None:
        player = self.bot.players.get_if_exists(interaction.guild_id or 0)
        if not player:
            return await interaction.response.send_message("Nada tocando.", ephemeral=True)
        player.loop_mode = LoopMode(mode.value)
        await interaction.response.send_message(f"🔁 Loop: `{mode.value}`")


async def setup(bot: MelodyBot) -> None:
    await bot.add_cog(MusicCog(bot))
