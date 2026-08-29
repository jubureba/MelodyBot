"""Gerencia um GuildPlayer por servidor."""

from __future__ import annotations

import discord

from .player import GuildPlayer


class PlayerManager:
    def __init__(self) -> None:
        self._players: dict[int, GuildPlayer] = {}

    def get(self, guild: discord.Guild) -> GuildPlayer:
        player = self._players.get(guild.id)
        if player is None:
            player = GuildPlayer(guild)
            self._players[guild.id] = player
        return player

    def get_if_exists(self, guild_id: int) -> GuildPlayer | None:
        return self._players.get(guild_id)

    def remove(self, guild_id: int) -> None:
        player = self._players.pop(guild_id, None)
        if player is not None:
            player.stop()
