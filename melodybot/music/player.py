"""Player por servidor: fila, reproducao sequencial, loop e controles."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from enum import Enum

import discord

from .track import Track, make_audio_source

log = logging.getLogger("melodybot.player")


class LoopMode(str, Enum):
    OFF = "off"
    TRACK = "track"
    QUEUE = "queue"


class GuildPlayer:
    """Mantem o estado de musica de um unico servidor."""

    def __init__(self, guild: discord.Guild) -> None:
        self.guild = guild
        self.queue: deque[Track] = deque()
        self.current: Track | None = None
        self.loop_mode: LoopMode = LoopMode.OFF
        self.volume: float = 0.5

        self._next = asyncio.Event()
        self._task: asyncio.Task | None = None

    # --- Ciclo de vida ---

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._player_loop())

    def stop(self) -> None:
        self.queue.clear()
        self.current = None
        self.loop_mode = LoopMode.OFF
        vc = self.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None

    # --- Fila ---

    def enqueue(self, track: Track) -> None:
        self.queue.append(track)

    def clear_queue(self) -> None:
        self.queue.clear()

    @property
    def queue_size(self) -> int:
        return len(self.queue)

    # --- Controles ---

    def skip(self) -> None:
        vc = self.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()  # dispara o _next, avancando a fila

    def pause(self) -> bool:
        vc = self.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            return True
        return False

    def resume(self) -> bool:
        vc = self.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            return True
        return False

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(volume, 2.0))
        vc = self.guild.voice_client
        if vc and isinstance(vc.source, discord.PCMVolumeTransformer):
            vc.source.volume = self.volume

    # --- Loop interno de reproducao ---

    def _on_track_end(self, error: Exception | None) -> None:
        if error:
            log.warning("Erro na reproducao (%s): %s", self.guild.id, error)
        self.guild._state.loop.call_soon_threadsafe(self._next.set)

    async def _player_loop(self) -> None:
        try:
            while True:
                self._next.clear()

                next_track = self._pick_next()
                if next_track is None:
                    # Fila vazia: encerra o loop; sera recriado no proximo play.
                    self.current = None
                    return

                self.current = next_track
                vc = self.guild.voice_client
                if vc is None:
                    return

                source = make_audio_source(next_track, self.volume)
                vc.play(source, after=self._on_track_end)
                log.info("Tocando em %s: %s", self.guild.id, next_track.title)

                await self._next.wait()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            log.exception("Falha no player loop de %s", self.guild.id)

    def _pick_next(self) -> Track | None:
        if self.loop_mode == LoopMode.TRACK and self.current is not None:
            return self.current
        if self.loop_mode == LoopMode.QUEUE and self.current is not None:
            self.queue.append(self.current)
        if self.queue:
            return self.queue.popleft()
        return None
