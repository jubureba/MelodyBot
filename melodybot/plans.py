"""Definicao de planos e regras de features (monetizacao)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Plan(str, Enum):
    FREE = "free"
    PREMIUM = "premium"


@dataclass(frozen=True)
class PlanLimits:
    """Limites e features de um plano.

    queue_limit / max_track_seconds: 0 = ilimitado.
    """

    queue_limit: int
    max_track_seconds: int
    audio_filters: bool
    saved_playlists: bool
    priority_support: bool


# Free usa limites configuraveis via .env; Premium libera tudo.
def build_plan_table(free_queue_limit: int, free_max_track_seconds: int) -> dict[Plan, PlanLimits]:
    return {
        Plan.FREE: PlanLimits(
            queue_limit=free_queue_limit,
            max_track_seconds=free_max_track_seconds,
            audio_filters=False,
            saved_playlists=False,
            priority_support=False,
        ),
        Plan.PREMIUM: PlanLimits(
            queue_limit=0,
            max_track_seconds=0,
            audio_filters=True,
            saved_playlists=True,
            priority_support=True,
        ),
    }


PLAN_LABELS = {
    Plan.FREE: "Free",
    Plan.PREMIUM: "Premium",
}
