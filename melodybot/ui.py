"""Componentes visuais: o painel unico do player e embeds auxiliares."""

from __future__ import annotations

import discord

from .music.player import GuildPlayer, LoopMode
from .music.track import Track

# Paleta
ACCENT = 0x5865F2  # blurple
GOLD = 0xFACC15
WARN = 0xF59E0B
ERROR = 0xED4245
OK = 0x57F287

LOOP_LABEL = {
    LoopMode.OFF: "off",
    LoopMode.TRACK: "faixa 🔂",
    LoopMode.QUEUE: "fila 🔁",
}


def simple(title: str, description: str = "", color: int = ACCENT) -> discord.Embed:
    emb = discord.Embed(color=color)
    emb.description = f"**{title}**" if not description else f"**{title}**\n{description}"
    return emb


def player_panel(
    player: GuildPlayer, paused: bool = False, pending: Track | None = None
) -> discord.Embed:
    """Um unico embed que representa o estado do player: tocando + fila.

    Esse mesmo embed e editado conforme a musica avanca. `pending` cobre a
    janela em que o loop async ainda nao definiu `current` (evita o falso
    "fila encerrada" logo apos o /play).
    """
    current: Track | None = player.current or pending

    if current is None:
        emb = discord.Embed(color=ACCENT)
        emb.description = "⏹️ **Fila encerrada**\nUse `/play` para tocar algo."
        return emb

    status = "⏸️" if paused else "▶️"
    emb = discord.Embed(color=ACCENT)
    emb.description = (
        f"{status} **Tocando agora**\n"
        f"### [{current.title}]({current.webpage_url})\n"
        f"`{current.duration_str}`"
    )
    if player.loop_mode != LoopMode.OFF:
        emb.description += f" · loop `{LOOP_LABEL[player.loop_mode]}`"

    # A faixa "pending" ja esta na fila (foi enfileirada), mas e a que esta
    # comecando a tocar — nao deve aparecer duplicada na lista "Na fila".
    queued = [t for t in player.queue if t is not pending]

    upcoming = queued[:10]
    if upcoming:
        lines = [
            f"`{i}.` [{t.title}]({t.webpage_url}) `{t.duration_str}`"
            for i, t in enumerate(upcoming, start=1)
        ]
        emb.add_field(name="📜 Na fila", value="\n".join(lines), inline=False)

    total = len(queued)
    if current.thumbnail:
        emb.set_thumbnail(url=current.thumbnail)

    footer = f"{total} na fila" if total else "fim da fila"
    if total > 10:
        footer = f"{total} na fila (mostrando 10)"
    emb.set_footer(text=footer)
    return emb
