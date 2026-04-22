"""Tests for memory.py — layered memory accessors."""
from pathlib import Path

import pytest

from scripts.v2_2 import memory


def test_project_layer_returns_path(tmp_project):
    p = memory.project_path("mission.md")
    assert p == tmp_project / "memory" / "project" / "mission.md"


def test_agent_layer_returns_path(tmp_project):
    p = memory.agent_path("fe-dev", "instructions.md")
    assert p == tmp_project / "memory" / "agents" / "fe-dev" / "instructions.md"


def test_story_layer_returns_path(tmp_project):
    p = memory.story_path("STU-46", "handoff.md")
    assert p == tmp_project / "memory" / "stories" / "STU-46" / "handoff.md"


def test_session_layer_returns_path(tmp_project):
    p = memory.session_path("current-turn.md")
    assert p == tmp_project / "memory" / "session" / "current-turn.md"


def test_write_creates_parents(tmp_project):
    memory.write("project", "mission.md", "our mission is ...")
    p = tmp_project / "memory" / "project" / "mission.md"
    assert p.exists()
    assert "mission" in p.read_text()


def test_write_agent_layer_accepts_agent_kw(tmp_project):
    memory.write("agents", "instructions.md", "be kind", agent="fe-dev")
    p = tmp_project / "memory" / "agents" / "fe-dev" / "instructions.md"
    assert p.exists()


def test_write_story_layer_accepts_story_kw(tmp_project):
    memory.write("stories", "handoff.md", "done", story="STU-46")
    p = tmp_project / "memory" / "stories" / "STU-46" / "handoff.md"
    assert p.exists()


def test_read_missing_file_returns_none(tmp_project):
    assert memory.read("project", "doesnotexist.md") is None


def test_read_existing_file_returns_content(tmp_project):
    memory.write("project", "mission.md", "hello")
    assert memory.read("project", "mission.md") == "hello"


def test_write_unknown_layer_raises(tmp_project):
    with pytest.raises(ValueError, match="Invalid layer"):
        memory.write("spaceship", "file.md", "x")
