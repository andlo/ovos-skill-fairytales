"""Tests for cross-collection title disambiguation (#12) and the language
fallback in update_index() (#6, re-verified against the current
{title: {url, author}} index shape)."""


def test_merge_index_no_collision_keeps_plain_titles(skill):
    skill._merge_index({"The Ugly Duckling": "/a"}, "Andersen")
    skill._merge_index({"Cinderella": "/g"}, "Grimm")
    assert skill.index["The Ugly Duckling"] == {"url": "/a", "author": "Andersen"}
    assert skill.index["Cinderella"] == {"url": "/g", "author": "Grimm"}


def test_merge_index_disambiguates_title_collision(skill):
    skill._merge_index({"Cinderella": "/andersen-version"}, "Andersen")
    skill._merge_index({"Cinderella": "/grimm-version"}, "Grimm")

    assert "Cinderella" not in skill.index
    assert skill.index["Cinderella - Andersen"] == {"url": "/andersen-version", "author": "Andersen"}
    assert skill.index["Cinderella - Grimm"] == {"url": "/grimm-version", "author": "Grimm"}


def test_merge_index_same_author_reindexed_twice_does_not_disambiguate(skill):
    # re-running _merge_index for the *same* author (e.g. a cache refresh)
    # should just update the url, not spuriously split into "title - author"
    skill._merge_index({"Cinderella": "/old-url"}, "Grimm")
    skill._merge_index({"Cinderella": "/new-url"}, "Grimm")
    assert skill.index["Cinderella"] == {"url": "/new-url", "author": "Grimm"}


def test_update_index_falls_back_to_english_for_unsupported_language(skill, monkeypatch):
    skill.lang = "xx-xx"  # not one of the 7 supported languages
    requested_urls = []

    def fake_get_index(url):
        requested_urls.append(url)
        return {}

    monkeypatch.setattr(skill, "get_index", fake_get_index)
    skill.update_index()

    assert any("andersen_fairy-tales" in url for url in requested_urls), requested_urls
    assert any("grimm_fairy-tales" in url for url in requested_urls), requested_urls


def test_update_index_uses_matching_language(skill, monkeypatch):
    skill.lang = "da-dk"
    requested_urls = []

    def fake_get_index(url):
        requested_urls.append(url)
        return {}

    monkeypatch.setattr(skill, "get_index", fake_get_index)
    skill.update_index()

    assert any("andersen_fortaellinger" in url for url in requested_urls), requested_urls
    assert any("grimm_eventyr" in url for url in requested_urls), requested_urls


def test_update_index_skips_andersen_for_grimm_only_language(skill, monkeypatch):
    # Portuguese (#31): grimmstories.com has it, andersenstories.com
    # doesn't - update_index() must not KeyError trying to look up a
    # Portuguese Andersen URL that doesn't exist, and should only fetch
    # from Grimm.
    skill.lang = "pt-pt"
    requested_urls = []

    def fake_get_index(url):
        requested_urls.append(url)
        return {}

    monkeypatch.setattr(skill, "get_index", fake_get_index)
    skill.update_index()

    assert requested_urls == ["https://www.grimmstories.com/pt/grimm_contos/list"]
