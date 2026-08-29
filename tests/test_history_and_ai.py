"""Testes do historico do servidor e do parser da IA."""

from __future__ import annotations

import pytest

from melodybot.ai.gemini import GeminiAIProvider
from melodybot.database import Database


@pytest.fixture
async def db(tmp_path):
    database = Database(str(tmp_path / "hist.db"))
    await database.connect()
    yield database
    await database.close()


async def test_history_records_and_totals(db):
    await db.record_play(1, "Musica A", "http://a", 100)
    await db.record_play(1, "Musica A", "http://a", 100)
    await db.record_play(1, "Musica B", "http://b", 200)
    assert await db.total_plays(1) == 3


async def test_top_tracks_ordering(db):
    for _ in range(3):
        await db.record_play(1, "Hit", "u", 1)
    await db.record_play(1, "Outra", "u", 1)
    top = await db.top_tracks(1, limit=5)
    assert top[0] == ("Hit", 3)


async def test_top_requesters(db):
    await db.record_play(1, "x", "u", 100)
    await db.record_play(1, "y", "u", 100)
    await db.record_play(1, "z", "u", 200)
    reqs = await db.top_requesters(1, limit=5)
    assert reqs[0] == (100, 2)


async def test_recent_titles_order(db):
    await db.record_play(1, "primeira", "u", 1)
    await db.record_play(1, "segunda", "u", 1)
    recent = await db.recent_titles(1, limit=10)
    assert recent[0] == "segunda"  # mais recente primeiro


def test_gemini_parse_valid_json():
    text = 'Aqui vai: ["Artista - Musica 1", "Outro - Musica 2"] pronto'
    result = GeminiAIProvider._parse(text, count=5)
    assert result == ["Artista - Musica 1", "Outro - Musica 2"]


def test_gemini_parse_respects_count():
    text = '["a - 1", "b - 2", "c - 3"]'
    assert GeminiAIProvider._parse(text, count=2) == ["a - 1", "b - 2"]


def test_gemini_parse_garbage_returns_empty():
    assert GeminiAIProvider._parse("sem json aqui", count=5) == []
