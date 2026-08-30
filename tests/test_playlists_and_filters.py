"""Testes de playlists salvas e do modulo de filtros de audio."""

from __future__ import annotations

import pytest

from melodybot.database import Database
from melodybot.music.filters import AudioFilter, ffmpeg_options


@pytest.fixture
async def db(tmp_path):
    database = Database(str(tmp_path / "pl.db"))
    await database.connect()
    yield database
    await database.close()


async def test_save_and_load_playlist(db):
    items = [("Musica A", "http://a"), ("Musica B", "http://b")]
    n = await db.save_playlist(1, "rock", items)
    assert n == 2
    loaded = await db.get_playlist_items(1, "rock")
    assert loaded == items


async def test_save_replaces_same_name(db):
    await db.save_playlist(1, "x", [("a", "u1")])
    await db.save_playlist(1, "x", [("b", "u2"), ("c", "u3")])
    loaded = await db.get_playlist_items(1, "x")
    assert [t for t, _ in loaded] == ["b", "c"]


async def test_list_playlists_counts(db):
    await db.save_playlist(1, "p1", [("a", "u")])
    await db.save_playlist(1, "p2", [("a", "u"), ("b", "u")])
    listing = dict(await db.list_playlists(1))
    assert listing == {"p1": 1, "p2": 2}


async def test_delete_playlist(db):
    await db.save_playlist(1, "temp", [("a", "u")])
    assert await db.delete_playlist(1, "temp") is True
    assert await db.delete_playlist(1, "temp") is False
    assert await db.get_playlist_items(1, "temp") == []


async def test_playlists_are_per_guild(db):
    await db.save_playlist(1, "mine", [("a", "u")])
    assert await db.list_playlists(2) == []


def test_ffmpeg_options_none_has_no_filter():
    opts = ffmpeg_options(AudioFilter.NONE)
    assert "-af" not in opts["options"]


def test_ffmpeg_options_bassboost_applies_filter():
    opts = ffmpeg_options(AudioFilter.BASSBOOST)
    assert "-af" in opts["options"]
    assert "bass=" in opts["options"]


def test_ffmpeg_options_keeps_reconnect():
    opts = ffmpeg_options(AudioFilter.NIGHTCORE)
    assert "reconnect" in opts["before_options"]
