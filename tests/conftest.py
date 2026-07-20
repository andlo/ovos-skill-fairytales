"""Shared pytest fixtures for the fairytales skill test suite.

We avoid instantiating Tales through OVOSSkill's normal __init__ (which
needs a live messagebus connection) - instead we build a bare instance with
Tales.__new__() and attach just the attributes the methods under test
actually use (log, settings, lang, file_system, index, cache).

The skill's code lives in the repo-root __init__.py (that's the OVOS skill
packaging convention), so we load it directly by file path rather than via
a package import - this works whether or not the skill has been
`pip install -e .`-ed into the environment.
"""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_INIT_PATH = Path(__file__).resolve().parents[1] / "__init__.py"
_spec = importlib.util.spec_from_file_location("fairytales_skill", _INIT_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

Tales = _module.Tales
StoryFetchError = _module.StoryFetchError
class FakeFileSystem:
    """Minimal stand-in for OVOS's FileSystemAccess, backed by a real
    temp directory so open()/exists() behave exactly like the real thing."""

    def __init__(self, base):
        self.base = base
        self.path = str(base)

    def exists(self, name):
        return (self.base / name).exists()

    def open(self, name, mode="r"):
        return open(self.base / name, mode)


@pytest.fixture
def skill(tmp_path, monkeypatch):
    s = Tales.__new__(Tales)
    s.log = MagicMock()
    s.skill_id = "ovos-skill-fairytales.test"
    s.status = MagicMock()
    s._bus = MagicMock()
    # settings is a property backed by _settings on OVOSSkill; set the
    # private attribute directly to avoid needing a full skill init
    s._settings = {}
    # lang is a read-only computed property on OVOSSkill (derived from
    # config/message context); replace it with a plain class attribute so
    # individual tests can just do `skill.lang = "..."` like normal
    monkeypatch.setattr(Tales, "lang", "en-us", raising=False)
    s.file_system = FakeFileSystem(tmp_path)
    s.index = {}
    s._story_text_cache = {}
    return s
