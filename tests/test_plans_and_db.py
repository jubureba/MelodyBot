"""Testes da camada de planos e do repository (SQLite em memoria/temp)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from melodybot.database import Database
from melodybot.plans import Plan, build_plan_table


def test_plan_table_free_vs_premium():
    table = build_plan_table(free_queue_limit=20, free_max_track_seconds=1800)
    assert table[Plan.FREE].queue_limit == 20
    assert table[Plan.FREE].audio_filters is False
    # Premium: tudo liberado (0 = ilimitado).
    assert table[Plan.PREMIUM].queue_limit == 0
    assert table[Plan.PREMIUM].audio_filters is True


@pytest.fixture
async def db(tmp_path):
    database = Database(str(tmp_path / "test.db"))
    await database.connect()
    yield database
    await database.close()


async def test_default_plan_is_free(db):
    assert await db.get_plan(123) == Plan.FREE


async def test_set_and_get_premium(db):
    until = datetime.now(UTC) + timedelta(days=30)
    await db.set_plan(123, Plan.PREMIUM, until)
    assert await db.get_plan(123) == Plan.PREMIUM


async def test_expired_premium_downgrades_to_free(db):
    past = datetime.now(UTC) - timedelta(days=1)
    await db.set_plan(123, Plan.PREMIUM, past)
    # get_plan deve detectar expiracao e rebaixar.
    assert await db.get_plan(123) == Plan.FREE


async def test_record_payment(db):
    await db.record_payment(123, "mercadopago", "abc", "approved", 9.90)
    # Sem erro = ok; a leitura detalhada nao faz parte da API publica.
