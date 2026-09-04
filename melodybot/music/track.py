"""Representacao de uma faixa e extracao de metadados via yt-dlp."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

import discord
import yt_dlp

from .filters import AudioFilter, ffmpeg_options

# Client do "player" do YouTube usado pelo yt-dlp. Em IPs de datacenter (cloud),
# o YouTube costuma exigir login ("Sign in to confirm you're not a bot"); usar
# um client alternativo (android/ios/tv) geralmente contorna sem cookies.
_YTDL_PLAYER_CLIENT = os.getenv("YTDL_PLAYER_CLIENT", "android").strip() or "android"

# Arquivo de cookies (formato Netscape) opcional. Se existir, e usado para
# autenticar no YouTube e evitar o bloqueio antibot. Nunca comite este arquivo.
_YTDL_COOKIES_FILE = os.getenv("YTDL_COOKIES_FILE", "data/cookies.txt").strip()

# Opcoes do yt-dlp: pega so o melhor audio, sem baixar o arquivo (streaming).
_YTDL_OPTS: dict = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "skip_download": True,
    "extractor_args": {"youtube": {"player_client": [_YTDL_PLAYER_CLIENT]}},
}

# So anexa o cookiefile se o arquivo realmente existir (evita erro do yt-dlp).
if _YTDL_COOKIES_FILE and os.path.isfile(_YTDL_COOKIES_FILE):
    _YTDL_OPTS["cookiefile"] = _YTDL_COOKIES_FILE

_ytdl = yt_dlp.YoutubeDL(_YTDL_OPTS)


@dataclass
class Track:
    title: str
    url: str  # URL de streaming (audio)
    webpage_url: str  # link "humano" (ex: pagina do YouTube)
    duration: int  # segundos
    thumbnail: str | None
    requester_id: int

    @property
    def duration_str(self) -> str:
        if not self.duration:
            return "ao vivo"
        minutes, seconds = divmod(self.duration, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


class TrackResolveError(Exception):
    """Erro ao resolver uma busca/URL em uma faixa tocavel."""


async def resolve_query(query: str, requester_id: int) -> Track:
    """Resolve uma busca textual ou URL em um Track pronto para tocar."""
    loop = asyncio.get_running_loop()
    try:
        data = await loop.run_in_executor(
            None, lambda: _ytdl.extract_info(query, download=False)
        )
    except Exception as exc:  # noqa: BLE001 - yt-dlp lanca varios tipos
        raise TrackResolveError(str(exc)) from exc

    if data is None:
        raise TrackResolveError("Nenhum resultado encontrado.")

    # Buscas retornam uma lista em "entries".
    if "entries" in data:
        entries = [e for e in data["entries"] if e]
        if not entries:
            raise TrackResolveError("Nenhum resultado encontrado.")
        data = entries[0]

    stream_url = data.get("url")
    if not stream_url:
        raise TrackResolveError("Nao foi possivel obter o audio dessa faixa.")

    return Track(
        title=data.get("title", "Desconhecido"),
        url=stream_url,
        webpage_url=data.get("webpage_url", query),
        duration=int(data.get("duration") or 0),
        thumbnail=data.get("thumbnail"),
        requester_id=requester_id,
    )


def make_audio_source(
    track: Track,
    volume: float = 0.5,
    audio_filter: AudioFilter = AudioFilter.NONE,
) -> discord.AudioSource:
    """Cria a fonte de audio FFmpeg para um Track, com filtro opcional."""
    source = discord.FFmpegPCMAudio(track.url, **ffmpeg_options(audio_filter))
    return discord.PCMVolumeTransformer(source, volume=volume)
