"""Comandos de musica (slash) com painel unico e auto-atualizavel."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from .. import ui
from ..bot import MelodyBot
from ..music.player import GuildPlayer, LoopMode
from ..music.track import TrackResolveError, resolve_query

log = logging.getLogger("melodybot.cogs.music")


async def _ensure_voice(interaction: discord.Interaction) -> discord.VoiceClient | None:
    user = interaction.user
    if not isinstance(user, discord.Member) or user.voice is None or user.voice.channel is None:
        await interaction.response.send_message(
            embed=ui.simple("🎧 Entra num canal de voz primeiro!", color=ui.WARN),
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
    """Botoes anexados ao painel unico. Editam a propria mensagem."""

    def __init__(self, cog: MusicCog, guild_id: int) -> None:
        super().__init__(timeout=None)
        self._cog = cog
        self._guild_id = guild_id

    def _player(self) -> GuildPlayer | None:
        return self._cog.bot.players.get_if_exists(self._guild_id)

    async def _refresh(self, interaction: discord.Interaction, paused: bool = False) -> None:
        player = self._player()
        if player is None:
            return await interaction.response.defer()
        await interaction.response.edit_message(
            embed=ui.player_panel(player, paused=paused), view=self
        )

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.secondary)
    async def pause_resume(self, interaction: discord.Interaction, _b: discord.ui.Button):
        player = self._player()
        if not player:
            return await interaction.response.defer()
        paused = not player.resume()
        if paused:
            player.pause()
        await self._refresh(interaction, paused=paused)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, _b: discord.ui.Button):
        player = self._player()
        if player:
            player.skip()
        # o on_change do player cuida de atualizar o painel; so confirmamos.
        await interaction.response.defer()

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.secondary)
    async def stop(self, interaction: discord.Interaction, _b: discord.ui.Button):
        player = self._player()
        if player:
            player.stop()
            player.panel_message = None
        vc = interaction.guild.voice_client if interaction.guild else None
        if vc:
            await vc.disconnect()
        await interaction.response.edit_message(
            embed=ui.simple("⏹️ Parei e sai do canal", color=ui.OK), view=None
        )


class MusicCog(commands.Cog):
    def __init__(self, bot: MelodyBot) -> None:
        self.bot = bot
        # Ultima faixa registrada por guild (evita duplicar no historico).
        self._last_recorded: dict[int, object] = {}
        # Guilds com autoplay ligado (feature Premium).
        self.autoplay_guilds: set[int] = set()
        # Evita disparar autoplay concorrente na mesma guild.
        self._autoplay_busy: set[int] = set()

    async def _maybe_autoplay(self, player: GuildPlayer) -> None:
        """Se autoplay estiver ligado e a fila baixa, enfileira faixa relacionada via IA."""
        gid = player.guild.id
        if gid not in self.autoplay_guilds:
            return
        if not self.bot.ai.enabled:
            return
        if player.queue_size > 0 or gid in self._autoplay_busy:
            return

        self._autoplay_busy.add(gid)
        try:
            recent = await self.bot.db.recent_titles(gid, limit=10)
            mood = "continuacao natural do que o servidor vem ouvindo"
            suggestions = await self.bot.ai.suggest_tracks(mood, count=2, context=recent)
            for query in suggestions:
                try:
                    track = await resolve_query(query, requester_id=self.bot.user.id)
                except TrackResolveError:
                    continue
                player.enqueue(track)
        finally:
            self._autoplay_busy.discard(gid)

    def _attach_change_handler(self, player: GuildPlayer) -> None:
        """Liga o callback que atualiza o painel quando a faixa muda."""
        if player.on_change is not None:
            return

        async def _on_change(p: GuildPlayer) -> None:
            # Registra no historico do servidor quando uma faixa comeca.
            if p.current is not None and p.current is not self._last_recorded.get(p.guild.id):
                self._last_recorded[p.guild.id] = p.current
                await self.bot.db.record_play(
                    guild_id=p.guild.id,
                    title=p.current.title,
                    url=p.current.webpage_url,
                    requester_id=p.current.requester_id,
                )
                await self._maybe_autoplay(p)

            if p.panel_message is None:
                return
            try:
                await p.panel_message.edit(
                    embed=ui.player_panel(p),
                    view=MusicControls(self, p.guild.id) if p.current else None,
                )
            except discord.NotFound:
                p.panel_message = None

        player.on_change = _on_change

    @app_commands.command(name="play", description="Toca uma musica (busca ou URL).")
    @app_commands.describe(query="Nome da musica ou link (YouTube, etc.)")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)

        vc = await _ensure_voice(interaction)
        if vc is None:
            return

        await interaction.response.defer()

        try:
            track = await resolve_query(query, requester_id=interaction.user.id)
        except TrackResolveError as exc:
            return await interaction.followup.send(
                embed=ui.simple("❌ Não consegui tocar isso", str(exc), color=ui.ERROR)
            )

        limits = await self.bot.limits_for_guild(interaction.guild.id)
        player = self.bot.players.get(interaction.guild)
        self._attach_change_handler(player)

        if limits.max_track_seconds and track.duration > limits.max_track_seconds:
            minutes = limits.max_track_seconds // 60
            return await interaction.followup.send(
                embed=ui.simple(
                    "🔒 Faixa muito longa (plano Free)",
                    f"Limite de **{minutes} min** por faixa. Use `/premium`.",
                    color=ui.WARN,
                )
            )

        if limits.queue_limit and player.queue_size >= limits.queue_limit:
            return await interaction.followup.send(
                embed=ui.simple(
                    "🔒 Fila cheia (plano Free)",
                    f"Limite de **{limits.queue_limit} faixas**. Use `/premium`.",
                    color=ui.WARN,
                )
            )

        already_playing = player.current is not None
        player.enqueue(track)

        # Painel unico: envia e registra a mensagem ANTES de dar start, para que
        # o on_change (disparado pelo loop) ja encontre o painel e o atualize
        # com o estado real. O embed inicial mostra a faixa recem-adicionada.
        view = MusicControls(self, interaction.guild.id)
        panel = ui.player_panel(player, pending=None if already_playing else track)
        msg = await interaction.followup.send(embed=panel, view=view, wait=True)
        await self._reset_panel(player, msg)

        player.start()

    async def _reset_panel(self, player: GuildPlayer, new_msg: discord.Message) -> None:
        """Apaga o painel antigo (se houver) e adota o novo como unico."""
        old = player.panel_message
        player.panel_message = new_msg
        if old is not None and old.id != new_msg.id:
            try:
                await old.delete()
            except discord.HTTPException:
                pass

    # --- Comandos utilitarios (respostas efemeras, nao poluem o canal) ---

    @app_commands.command(name="skip", description="Pula a faixa (vote-skip democratico).")
    async def skip(self, interaction: discord.Interaction) -> None:
        player = self.bot.players.get_if_exists(interaction.guild_id or 0)
        if not player or player.current is None:
            return await interaction.response.send_message("Nada tocando.", ephemeral=True)

        guild = interaction.guild
        vc = guild.voice_client if guild else None
        listeners = self._human_listeners(vc)

        # Quem pediu a musica, ou canal com <=2 humanos: pula direto.
        requester_id = player.current.requester_id
        if listeners <= 2 or interaction.user.id == requester_id:
            player.skip()
            return await interaction.response.send_message(
                embed=ui.simple("⏭️ Pulando…", color=ui.OK), ephemeral=True
            )

        # Caso contrario: vote-skip por maioria.
        needed = listeners // 2 + 1
        votes = player.skip_votes
        if interaction.user.id in votes:
            return await interaction.response.send_message(
                embed=ui.simple("🗳️ Você já votou para pular.", color=ui.WARN),
                ephemeral=True,
            )
        votes.add(interaction.user.id)

        if len(votes) >= needed:
            player.skip()
            return await interaction.response.send_message(
                embed=ui.simple("⏭️ Votação aprovada — pulando!", color=ui.OK)
            )
        await interaction.response.send_message(
            embed=ui.simple(
                "🗳️ Voto registrado",
                f"`{len(votes)}/{needed}` votos para pular.",
                color=ui.ACCENT,
            )
        )

    @staticmethod
    def _human_listeners(vc: discord.VoiceClient | None) -> int:
        if vc is None or vc.channel is None:
            return 0
        return sum(1 for m in vc.channel.members if not m.bot)

    @app_commands.command(name="stop", description="Para tudo e limpa a fila.")
    async def stop(self, interaction: discord.Interaction) -> None:
        player = self.bot.players.get_if_exists(interaction.guild_id or 0)
        if player:
            if player.panel_message is not None:
                try:
                    await player.panel_message.edit(
                        embed=ui.simple("⏹️ Parado", color=ui.OK), view=None
                    )
                except discord.HTTPException:
                    pass
                player.panel_message = None
            player.stop()
        vc = interaction.guild.voice_client if interaction.guild else None
        if vc:
            await vc.disconnect()
        await interaction.response.send_message(
            embed=ui.simple("⏹️ Parei e limpei a fila", color=ui.OK), ephemeral=True
        )

    @app_commands.command(name="queue", description="Mostra a fila atual.")
    async def queue(self, interaction: discord.Interaction) -> None:
        player = self.bot.players.get_if_exists(interaction.guild_id or 0)
        if not player or (player.current is None and player.queue_size == 0):
            return await interaction.response.send_message("Fila vazia.", ephemeral=True)
        await interaction.response.send_message(
            embed=ui.player_panel(player), ephemeral=True
        )

    @app_commands.command(name="loop", description="Alterna o modo de repeticao.")
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
        # Atualiza o painel para refletir o loop.
        if player.panel_message is not None:
            try:
                await player.panel_message.edit(embed=ui.player_panel(player))
            except discord.HTTPException:
                pass
        await interaction.response.send_message(
            embed=ui.simple(f"🔁 Loop: {ui.LOOP_LABEL[player.loop_mode]}", color=ui.OK),
            ephemeral=True,
        )


async def setup(bot: MelodyBot) -> None:
    await bot.add_cog(MusicCog(bot))
