"""Configuracao central carregada de variaveis de ambiente (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _get_int(key: str, default: int) -> int:
    raw = os.getenv(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_float(key: str, default: float) -> float:
    raw = os.getenv(key, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_guild_ids() -> list[int]:
    raw = os.getenv("DEV_GUILD_IDS", "").strip()
    if not raw:
        return []
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


@dataclass(frozen=True)
class Settings:
    discord_token: str
    dev_guild_ids: list[int] = field(default_factory=list)
    database_path: str = "data/melodybot.db"

    free_queue_limit: int = 20
    free_max_track_seconds: int = 1800

    payment_provider: str = "none"
    mercadopago_access_token: str = ""
    payment_webhook_base_url: str = ""
    webhook_port: int = 8080
    premium_price_brl: float = 9.90

    ai_provider: str = "none"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"

    ytdl_player_client: str = "android"
    ytdl_cookies_file: str = "data/cookies.txt"

    log_level: str = "INFO"

    @property
    def payments_enabled(self) -> bool:
        return self.payment_provider.lower() not in ("", "none")

    @property
    def ai_enabled(self) -> bool:
        return self.ai_provider.lower() not in ("", "none")

    @classmethod
    def load(cls) -> Settings:
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise RuntimeError(
                "DISCORD_TOKEN nao definido. Copie .env.example para .env e preencha."
            )
        return cls(
            discord_token=token,
            dev_guild_ids=_get_guild_ids(),
            database_path=os.getenv("DATABASE_PATH", "data/melodybot.db").strip(),
            free_queue_limit=_get_int("FREE_QUEUE_LIMIT", 20),
            free_max_track_seconds=_get_int("FREE_MAX_TRACK_SECONDS", 1800),
            payment_provider=os.getenv("PAYMENT_PROVIDER", "none").strip(),
            mercadopago_access_token=os.getenv("MERCADOPAGO_ACCESS_TOKEN", "").strip(),
            payment_webhook_base_url=os.getenv("PAYMENT_WEBHOOK_BASE_URL", "").strip(),
            webhook_port=_get_int("WEBHOOK_PORT", 8080),
            premium_price_brl=_get_float("PREMIUM_PRICE_BRL", 9.90),
            ai_provider=os.getenv("AI_PROVIDER", "none").strip(),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip(),
            ytdl_player_client=os.getenv("YTDL_PLAYER_CLIENT", "android").strip(),
            ytdl_cookies_file=os.getenv("YTDL_COOKIES_FILE", "data/cookies.txt").strip(),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        )
