"""Tests for skills.py — namespaced skill registry."""
from pathlib import Path

import yaml
import pytest

from scripts.v2_2 import skills


def test_list_empty_registry_returns_empty(tmp_project):
    assert skills.list_registered() == []


def test_register_local_skill_adds_to_registry(tmp_project):
    skill_dir = tmp_project / "skills" / "project" / "otoqi-rls"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: otoqi-rls\n---\n# Skill")

    skills.register(tier="project", key="otoqi-rls", source="local")

    listed = skills.list_registered()
    assert len(listed) == 1
    assert listed[0]["key"] == "project/otoqi-rls"
    assert listed[0]["source"] == "local"


def test_register_missing_skill_dir_raises(tmp_project):
    """Can't register a skill that doesn't exist on disk."""
    with pytest.raises(FileNotFoundError):
        skills.register(tier="project", key="nonexistent", source="local")


def test_register_idempotent(tmp_project):
    skill_dir = tmp_project / "skills" / "project" / "foo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")
    skills.register(tier="project", key="foo", source="local")
    skills.register(tier="project", key="foo", source="local")  # re-register
    assert len(skills.list_registered()) == 1


def test_unregister_removes_entry(tmp_project):
    skill_dir = tmp_project / "skills" / "project" / "foo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# S")
    skills.register(tier="project", key="foo", source="local")
    skills.unregister("project/foo")
    assert skills.list_registered() == []


def test_unregister_unknown_is_noop(tmp_project):
    """Removing a not-registered skill is silent (idempotent)."""
    skills.unregister("project/nonexistent")  # does not raise
    assert skills.list_registered() == []


def test_register_rejects_invalid_tier(tmp_project):
    with pytest.raises(ValueError, match="Invalid tier"):
        skills.register(tier="spaceship", key="x", source="local")


def test_render_shows_emoji(tmp_project):
    out = skills.render()
    assert "📦" in out


def test_render_lists_registered_skills(tmp_project):
    skill_dir = tmp_project / "skills" / "project" / "foo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# S")
    skills.register(tier="project", key="foo", source="local")
    out = skills.render()
    assert "foo" in out
    assert "project" in out
