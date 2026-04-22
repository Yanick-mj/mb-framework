"""Tests for tools.py — external tool catalog reader + renderer."""
from pathlib import Path

import yaml
import pytest

from scripts.v2_2 import tools


def _write_catalog(project: Path, data: dict) -> None:
    catalog = project / "tools" / "_catalog.yaml"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(yaml.safe_dump(data))


def test_load_missing_catalog_returns_empty(tmp_project):
    """No tools/_catalog.yaml -> load() returns []."""
    assert tools.load() == []


def test_load_valid_catalog_returns_tools(tmp_project):
    _write_catalog(tmp_project, {
        "version": 1,
        "tools": [
            {"name": "vercel", "actions": ["deploy-preview", "deploy-prod"]},
            {"name": "github", "actions": ["read", "write-pr"]},
        ],
    })
    result = tools.load()
    assert len(result) == 2
    names = {t["name"] for t in result}
    assert names == {"vercel", "github"}


def test_load_malformed_yaml_returns_empty(tmp_project):
    catalog = tmp_project / "tools" / "_catalog.yaml"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(": [\ninvalid {{{\n")
    assert tools.load() == []


def test_load_unexpected_top_level_returns_empty(tmp_project):
    """If YAML root is not a dict or 'tools' is not a list, return []."""
    catalog = tmp_project / "tools" / "_catalog.yaml"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text("version: 1\ntools: not-a-list\n")
    assert tools.load() == []


def test_render_empty_catalog(tmp_project):
    out = tools.render()
    assert "No tools registered" in out
    assert "🔧" in out


def test_render_lists_tools_with_actions(tmp_project):
    _write_catalog(tmp_project, {
        "version": 1,
        "tools": [
            {"name": "vercel", "actions": ["deploy-preview", "deploy-prod"]},
        ],
    })
    out = tools.render()
    assert "🔧" in out
    assert "vercel" in out
    assert "deploy-preview" in out
    assert "deploy-prod" in out


def test_render_handles_tool_without_actions(tmp_project):
    """Tool with no actions key renders gracefully."""
    _write_catalog(tmp_project, {
        "version": 1,
        "tools": [{"name": "placeholder"}],
    })
    out = tools.render()
    assert "placeholder" in out
    assert "(no actions)" in out or "no actions" in out.lower()


def test_get_tool_returns_entry_by_name(tmp_project):
    _write_catalog(tmp_project, {
        "version": 1,
        "tools": [{"name": "vercel", "actions": ["deploy-preview"]}],
    })
    result = tools.get_tool("vercel")
    assert result is not None
    assert result["name"] == "vercel"


def test_get_tool_unknown_returns_none(tmp_project):
    assert tools.get_tool("nonexistent") is None


def test_load_rejects_tools_without_name(tmp_project):
    """Entries without a 'name' are silently skipped (strict v2.1.2-style)."""
    _write_catalog(tmp_project, {
        "version": 1,
        "tools": [
            {"actions": ["x"]},                # no name
            {"name": "ok", "actions": ["y"]},
            {"name": None, "actions": ["z"]},  # null name
            {"name": "", "actions": ["z"]},    # empty name
        ],
    })
    result = tools.load()
    assert len(result) == 1
    assert result[0]["name"] == "ok"


def test_load_rejects_non_dict_entries(tmp_project):
    """Entries that are not dicts are skipped (defensive)."""
    _write_catalog(tmp_project, {
        "version": 1,
        "tools": [
            "not-a-dict-just-a-string",
            42,
            ["nested", "list"],
            {"name": "valid", "actions": ["read"]},
        ],
    })
    result = tools.load()
    assert len(result) == 1
    assert result[0]["name"] == "valid"
