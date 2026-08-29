"""Camada de acesso a dados (repository) usando SQLite via aiosqlite.

Toda consulta ao banco vive aqui. Cogs e servicos nunca fazem SQL direto.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import aiosqlite

from .plans import Plan

_SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
    guild_id      INTEGER PRIMARY KEY,
    plan          TEXT NOT NULL DEFAULT 'free',
    active_until  TEXT,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id      INTEGER NOT NULL,
    provider      TEXT NOT NULL,
    external_id   TEXT,
    status        TEXT NOT NULL,
    amount        REAL,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS play_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id      INTEGER NOT NULL,
    title         TEXT NOT NULL,
    url           TEXT,
    requester_id  INTEGER,
    played_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_history_guild ON play_history(guild_id);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    """Repository unico do bot. Instancie e chame connect() no startup."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        directory = os.path.dirname(self._path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._db = await aiosqlite.connect(self._path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    @property
    def _conn(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Database nao conectado. Chame connect() primeiro.")
        return self._db

    # --- Subscriptions ---

    async def get_plan(self, guild_id: int) -> Plan:
        """Retorna o plano vigente do servidor, considerando expiracao."""
        async with self._conn.execute(
            "SELECT plan, active_until FROM subscriptions WHERE guild_id = ?",
            (guild_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return Plan.FREE

        plan = Plan(row["plan"])
        if plan == Plan.PREMIUM and row["active_until"]:
            expires = datetime.fromisoformat(row["active_until"])
            if expires < datetime.now(UTC):
                # Expirou: rebaixa para Free.
                await self.set_plan(guild_id, Plan.FREE, active_until=None)
                return Plan.FREE
        return plan

    async def set_plan(
        self, guild_id: int, plan: Plan, active_until: datetime | None
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO subscriptions (guild_id, plan, active_until, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                plan = excluded.plan,
                active_until = excluded.active_until,
                updated_at = excluded.updated_at
            """,
            (
                guild_id,
                plan.value,
                active_until.isoformat() if active_until else None,
                _now(),
            ),
        )
        await self._conn.commit()

    # --- Payments (auditoria) ---

    async def record_payment(
        self,
        guild_id: int,
        provider: str,
        external_id: str | None,
        status: str,
        amount: float | None,
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO payments (guild_id, provider, external_id, status, amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (guild_id, provider, external_id, status, amount, _now()),
        )
        await self._conn.commit()

    # --- Play history (diferencial: memoria do servidor) ---

    async def record_play(
        self, guild_id: int, title: str, url: str | None, requester_id: int | None
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO play_history (guild_id, title, url, requester_id, played_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (guild_id, title, url, requester_id, _now()),
        )
        await self._conn.commit()

    async def recent_titles(self, guild_id: int, limit: int = 15) -> list[str]:
        """Titulos tocados recentemente (para dar contexto de gosto a IA)."""
        async with self._conn.execute(
            """
            SELECT title FROM play_history
            WHERE guild_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (guild_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [row["title"] for row in rows]

    async def top_tracks(self, guild_id: int, limit: int = 10) -> list[tuple[str, int]]:
        async with self._conn.execute(
            """
            SELECT title, COUNT(*) AS plays FROM play_history
            WHERE guild_id = ?
            GROUP BY title
            ORDER BY plays DESC, MAX(id) DESC
            LIMIT ?
            """,
            (guild_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [(row["title"], row["plays"]) for row in rows]

    async def top_requesters(self, guild_id: int, limit: int = 5) -> list[tuple[int, int]]:
        async with self._conn.execute(
            """
            SELECT requester_id, COUNT(*) AS plays FROM play_history
            WHERE guild_id = ? AND requester_id IS NOT NULL
            GROUP BY requester_id
            ORDER BY plays DESC
            LIMIT ?
            """,
            (guild_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [(row["requester_id"], row["plays"]) for row in rows]

    async def total_plays(self, guild_id: int) -> int:
        async with self._conn.execute(
            "SELECT COUNT(*) AS c FROM play_history WHERE guild_id = ?",
            (guild_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return row["c"] if row else 0
