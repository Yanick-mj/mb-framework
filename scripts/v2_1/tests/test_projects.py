"""Tests for projects.py — multi-project registry reader/writer."""
from pathlib import Path

import yaml
import pytest

from scripts.v2_1 import projects


def test_load_missing_registry_returns_empty(tmp_home):
    """If ~/.mb/projects.yaml does not exist, load() returns []."""
    assert projects.load() == []


def test_load_valid_registry_returns_list(tmp_home):
    """Given a valid yaml, load() returns the projects list."""
    mb_dir = tmp_home / ".mb"
    mb_dir.mkdir()
    (mb_dir / "projects.yaml").write_text(yaml.safe_dump({
        "version": 1,
        "projects": [
            {"name": "demo", "path": "/tmp/demo", "stage": "mvp"},
        ],
    }))
    result = projects.load()
    assert len(result) == 1
    assert result[0]["name"] == "demo"


def test_add_project_creates_registry_if_missing(tmp_home):
    """add() creates ~/.mb/projects.yaml if absent."""
    projects.add(name="demo", path="/tmp/demo", stage="mvp")
    assert (tmp_home / ".mb" / "projects.yaml").exists()
    result = projects.load()
    assert result[0]["name"] == "demo"


def test_add_idempotent_by_name(tmp_home):
    """Adding the same name twice updates, does not duplicate."""
    projects.add(name="demo", path="/tmp/demo", stage="mvp")
    projects.add(name="demo", path="/tmp/demo", stage="pmf")
    result = projects.load()
    assert len(result) == 1
    assert result[0]["stage"] == "pmf"


def test_render_empty_registry_returns_placeholder(tmp_home):
    """render() on empty registry returns a helpful message."""
    out = projects.render()
    assert "No mb projects registered" in out


def test_render_lists_projects_with_stage(tmp_home):
    """render() includes name, stage, path in output."""
    projects.add(name="otoqi", path="/Users/y/otoqi", stage="pmf")
    projects.add(name="iris", path="/Users/y/iris", stage="discovery")
    out = projects.render()
    assert "otoqi" in out
    assert "pmf" in out
    assert "iris" in out
    assert "discovery" in out


def test_load_corrupted_yaml_returns_empty(tmp_home):
    """If projects.yaml contains invalid YAML, load() returns []."""
    mb_dir = tmp_home / ".mb"
    mb_dir.mkdir()
    (mb_dir / "projects.yaml").write_text(": [\ninvalid yaml {{{\n")
    assert projects.load() == []


def test_load_unexpected_structure_returns_empty(tmp_home):
    """If projects key is not a list, load() returns []."""
    mb_dir = tmp_home / ".mb"
    mb_dir.mkdir()
    (mb_dir / "projects.yaml").write_text("version: 1\nprojects: not-a-list\n")
    assert projects.load() == []
