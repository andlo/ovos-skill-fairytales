"""Tests for HTML parsing (get_title/get_story/get_index) against saved
sample fragments - deliberately not hitting the live site in CI."""
import requests
import pytest
from bs4 import BeautifulSoup

from conftest import StoryFetchError

STORY_HTML = """
<html><body>
<h2 itemprop="name">The Ugly Duckling</h2>
<div class="subtitle">by Hans Christian Andersen</div>
<div itemprop="text">It was so beautiful out in the country.

It was the middle of summer.</div>
</body></html>
"""

INDEX_HTML = """
<html><body>
<ul class="list_link">
  <li><a href="/en/andersen_fairy-tales/the_ugly_duckling">The Ugly Duckling</a></li>
  <li><a href="/en/andersen_fairy-tales/the_little_mermaid">The Little Mermaid</a></li>
</ul>
</body></html>
"""

EMPTY_HTML = "<html><body><p>nothing here</p></body></html>"


def test_get_title(skill, monkeypatch):
    monkeypatch.setattr(skill, "get_soup", lambda url: BeautifulSoup(STORY_HTML, "html.parser"))
    assert skill.get_title("http://example.test/story") == "The Ugly Duckling"


def test_get_subtitle(skill, monkeypatch):
    monkeypatch.setattr(skill, "get_soup", lambda url: BeautifulSoup(STORY_HTML, "html.parser"))
    assert skill.get_subtitle("http://example.test/story") == "by Hans Christian Andersen"


def test_get_title_missing_raises(skill, monkeypatch):
    monkeypatch.setattr(skill, "get_soup", lambda url: BeautifulSoup(EMPTY_HTML, "html.parser"))
    with pytest.raises(StoryFetchError):
        skill.get_title("http://example.test/missing")


def test_get_index(skill, monkeypatch):
    monkeypatch.setattr(skill, "get_soup", lambda url: BeautifulSoup(INDEX_HTML, "html.parser"))
    index = skill.get_index("http://example.test/list")
    assert index == {
        "The Ugly Duckling": "/en/andersen_fairy-tales/the_ugly_duckling",
        "The Little Mermaid": "/en/andersen_fairy-tales/the_little_mermaid",
    }


def test_get_index_missing_raises(skill, monkeypatch):
    monkeypatch.setattr(skill, "get_soup", lambda url: BeautifulSoup(EMPTY_HTML, "html.parser"))
    with pytest.raises(StoryFetchError):
        skill.get_index("http://example.test/list")


def test_get_story_parses_and_caches(skill, monkeypatch):
    calls = []

    def fake_get_soup(url):
        calls.append(url)
        return BeautifulSoup(STORY_HTML, "html.parser")

    monkeypatch.setattr(skill, "get_soup", fake_get_soup)
    text1 = skill.get_story("http://example.test/story")
    text2 = skill.get_story("http://example.test/story")
    assert "beautiful out in the country" in text1
    assert text1 == text2
    assert len(calls) == 1  # second call served from the in-memory cache


def test_get_soup_wraps_request_exception(skill, monkeypatch):
    def fake_get(*a, **kw):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(requests, "get", fake_get)
    with pytest.raises(StoryFetchError):
        skill.get_soup("http://example.test/down")
