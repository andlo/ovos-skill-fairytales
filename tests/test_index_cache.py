"""Tests for the on-disk story index cache (#8)."""
import json
import time

from conftest import StoryFetchError


def test_write_then_read_index_cache_roundtrip(skill):
    skill.index = {"Cinderella": {"url": "/x", "author": "Grimm"}}
    skill._write_index_cache()
    cached = skill._read_index_cache()
    assert cached["index"] == skill.index
    assert "timestamp" in cached


def test_read_index_cache_missing_file_returns_none(skill):
    assert skill._read_index_cache() is None


def test_read_index_cache_corrupt_file_returns_none(skill):
    cache_file = skill.file_system.base / skill._index_cache_filename()
    cache_file.write_text("not json")
    assert skill._read_index_cache() is None


def test_refresh_index_uses_fresh_cache_without_scraping(skill, monkeypatch):
    skill.index = {"Cinderella": {"url": "/x", "author": "Grimm"}}
    skill._write_index_cache()
    skill.index = {}

    def fail_if_called():
        raise AssertionError("update_index should not be called when cache is fresh")

    monkeypatch.setattr(skill, "update_index", fail_if_called)
    skill.refresh_index()
    assert skill.index == {"Cinderella": {"url": "/x", "author": "Grimm"}}


def test_refresh_index_falls_back_to_stale_cache_on_scrape_failure(skill, monkeypatch):
    cache_file = skill.file_system.base / skill._index_cache_filename()
    stale = {"timestamp": time.time() - skill.INDEX_CACHE_TTL * 2,
              "index": {"Cinderella": {"url": "/x", "author": "Grimm"}}}
    cache_file.write_text(json.dumps(stale))

    def raise_fetch_error():
        raise StoryFetchError("site is down")

    monkeypatch.setattr(skill, "update_index", raise_fetch_error)
    skill.refresh_index(force=True)
    assert skill.index == stale["index"]
