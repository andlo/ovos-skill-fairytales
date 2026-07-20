"""Smoke test: the skill module must import cleanly with only its declared
requirements.txt dependencies installed (catches things like #16, a missing
'requests' dependency that would only surface as a runtime ImportError)."""
from conftest import Tales, StoryFetchError


def test_imports_cleanly():
    assert Tales is not None
    assert issubclass(StoryFetchError, Exception)


def test_tales_is_an_ovos_skill():
    from ovos_workshop.skills import OVOSSkill
    assert issubclass(Tales, OVOSSkill)
