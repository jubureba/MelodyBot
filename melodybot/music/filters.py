"""Filtros de audio (feature Premium) aplicados via FFmpeg afilter."""

from __future__ import annotations

from enum import Enum


class AudioFilter(str, Enum):
    NONE = "none"
    BASSBOOST = "bassboost"
    NIGHTCORE = "nightcore"
    VAPORWAVE = "vaporwave"
    EIGHT_D = "8d"
    TREBLE = "treble"


# Cadeia de filtros -a- FFmpeg (-af). NONE = sem filtro.
_FILTER_CHAINS: dict[AudioFilter, str] = {
    AudioFilter.NONE: "",
    AudioFilter.BASSBOOST: "bass=g=12,dynaudnorm=f=200",
    AudioFilter.NIGHTCORE: "aresample=48000,asetrate=48000*1.25,atempo=1.06",
    AudioFilter.VAPORWAVE: "aresample=48000,asetrate=48000*0.82,atempo=1.05",
    AudioFilter.EIGHT_D: "apulsator=hz=0.09",
    AudioFilter.TREBLE: "treble=g=8",
}

FILTER_LABELS: dict[AudioFilter, str] = {
    AudioFilter.NONE: "Nenhum",
    AudioFilter.BASSBOOST: "🔊 Bass Boost",
    AudioFilter.NIGHTCORE: "⚡ Nightcore",
    AudioFilter.VAPORWAVE: "🌴 Vaporwave",
    AudioFilter.EIGHT_D: "🎧 8D",
    AudioFilter.TREBLE: "✨ Treble",
}


def ffmpeg_options(audio_filter: AudioFilter) -> dict[str, str]:
    """Monta as opcoes do FFmpegPCMAudio para o filtro escolhido."""
    opts: dict[str, str] = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }
    chain = _FILTER_CHAINS.get(audio_filter, "")
    if chain:
        opts["options"] = f"-vn -af {chain}"
    return opts
