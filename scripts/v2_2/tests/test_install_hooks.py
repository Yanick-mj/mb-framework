"""Tests for install_hooks.py — idempotent merge into .claude/settings.json."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.v2_2 import install_hooks


MB_DIR = "/opt/mb"


def _settings(tmp_project: Path) -> Path:
    return tmp_project / ".claude" / "settings.json"


def test_merge_adds_hook_when_settings_missing(tmp_project):
    path = _settings(tmp_project)
    result = install_hooks.merge(path, MB_DIR)
    assert result == "added"
    data = json.loads(path.read_text())
    ups = data["hooks"]["UserPromptSubmit"]
    assert len(ups) == 1
    assert "orchestrator-autoinvoke.sh" in ups[0]["hooks"][0]["command"]
    assert ups[0]["hooks"][0]["command"] == f"bash {MB_DIR}/hooks/orchestrator-autoinvoke.sh"


def test_merge_is_idempotent(tmp_project):
    path = _settings(tmp_project)
    install_hooks.merge(path, MB_DIR)
    result = install_hooks.merge(path, MB_DIR)
    assert result == "noop"
    data = json.loads(path.read_text())
    assert len(data["hooks"]["UserPromptSubmit"]) == 1  # no duplicates


def test_merge_updates_when_mb_dir_changes(tmp_project):
    path = _settings(tmp_project)
    install_hooks.merge(path, "/old/path")
    result = install_hooks.merge(path, "/new/path")
    assert result == "updated"
    data = json.loads(path.read_text())
    cmd = data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    assert "/new/path/" in cmd
    assert "/old/path/" not in cmd


def test_merge_preserves_existing_hooks(tmp_project):
    path = _settings(tmp_project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "hooks": {
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": "echo hello"}]}
            ],
            "PreToolUse": [
                {"hooks": [{"type": "command", "command": "echo pre"}]}
            ],
        },
        "otherSetting": "keep me",
    }))

    result = install_hooks.merge(path, MB_DIR)
    assert result == "added"
    data = json.loads(path.read_text())

    # mb hook was appended, not replaced the existing one
    ups = data["hooks"]["UserPromptSubmit"]
    assert len(ups) == 2
    commands = [h["hooks"][0]["command"] for h in ups]
    assert "echo hello" in commands
    assert any("orchestrator-autoinvoke.sh" in c for c in commands)

    # Other hook types and unrelated keys preserved
    assert "PreToolUse" in data["hooks"]
    assert data["otherSetting"] == "keep me"


def test_merge_refuses_invalid_json(tmp_project, capsys):
    path = _settings(tmp_project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json {{{")
    result = install_hooks.merge(path, MB_DIR)
    assert result == "noop"
    err = capsys.readouterr().err
    assert "invalid JSON" in err


def test_remove_deletes_only_mb_hook(tmp_project):
    path = _settings(tmp_project)
    install_hooks.merge(path, MB_DIR)
    # Add a non-mb hook afterwards
    data = json.loads(path.read_text())
    data["hooks"]["UserPromptSubmit"].append(
        {"hooks": [{"type": "command", "command": "echo other"}]}
    )
    path.write_text(json.dumps(data))

    result = install_hooks.remove(path)
    assert result == "removed"
    data = json.loads(path.read_text())
    remaining = data["hooks"]["UserPromptSubmit"]
    assert len(remaining) == 1
    assert "echo other" in remaining[0]["hooks"][0]["command"]


def test_remove_noop_when_no_mb_hook(tmp_project):
    path = _settings(tmp_project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "echo other"}]}]}
    }))
    result = install_hooks.remove(path)
    assert result == "noop"


def test_remove_cleans_empty_hooks_section(tmp_project):
    path = _settings(tmp_project)
    install_hooks.merge(path, MB_DIR)
    install_hooks.remove(path)
    # After removing the only hook, settings.json should no longer exist
    # (or the hooks section should be pruned)
    if path.exists():
        data = json.loads(path.read_text())
        assert "hooks" not in data or not data["hooks"]
