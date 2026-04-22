"""Tests for rbac.py — agent × tool × action permission check, stage-aware.

The core promise (per v2.2 plan C2):
  - discovery / mvp + no permissions.yaml → PERMISSIVE default (allow)
  - pmf / scale + no permissions.yaml     → STRICT default (deny)
  - permissions.yaml present             → enforced strictly at every stage

Every check() auto-writes a JSONL audit entry to memory/tool-audit.jsonl
unless audit=False is passed.
"""
from pathlib import Path

import json
import yaml
import pytest

from scripts.v2_2 import rbac


def _write_perms(project: Path, data: dict) -> None:
    perms = project / "memory" / "permissions.yaml"
    perms.parent.mkdir(parents=True, exist_ok=True)
    perms.write_text(yaml.safe_dump(data))


# =================================================================
# load() — config parsing
# =================================================================

def test_load_missing_permissions_returns_empty_dict(tmp_project):
    """No permissions.yaml → load() returns {}."""
    assert rbac.load() == {}


def test_load_malformed_yaml_returns_empty(tmp_project):
    perms = tmp_project / "memory" / "permissions.yaml"
    perms.parent.mkdir(parents=True, exist_ok=True)
    perms.write_text(": [\ninvalid {{{\n")
    assert rbac.load() == {}


def test_load_unexpected_structure_returns_empty(tmp_project):
    """If 'permissions' key is absent or not a dict, return {}."""
    _write_perms(tmp_project, {"version": 1})                  # no 'permissions'
    assert rbac.load() == {}


# =================================================================
# check() — stage-aware defaults (C2 promise)
# =================================================================

def test_check_deny_by_default_on_empty_config_at_pmf(tmp_project):
    """At stage=pmf with no permissions.yaml, all checks DENY (strict)."""
    # tmp_project fixture sets stage=pmf
    result = rbac.check("fe-dev", "vercel", "deploy-prod")
    assert result.allowed is False
    assert "no permissions configured" in result.reason.lower()


def test_check_permissive_at_mvp_when_no_config(tmp_mvp_project):
    """At stage=mvp with no permissions.yaml, all checks ALLOW (permissive)."""
    result = rbac.check("fe-dev", "vercel", "deploy-prod")
    assert result.allowed is True
    assert "permissive" in result.reason.lower()
    assert "mvp" in result.reason.lower()


def test_check_permissive_at_discovery_when_no_config(tmp_path, monkeypatch):
    """At stage=discovery with no permissions.yaml, all checks ALLOW."""
    project = tmp_path / "disc"
    project.mkdir()
    (project / "mb-stage.yaml").write_text("stage: discovery\nsince: 2026-04-19\n")
    (project / "memory").mkdir()
    monkeypatch.chdir(project)
    result = rbac.check("fe-dev", "vercel", "deploy-prod")
    assert result.allowed is True


def test_check_strict_at_scale_when_no_config(tmp_path, monkeypatch):
    """At stage=scale with no permissions.yaml, all checks DENY."""
    project = tmp_path / "sc"
    project.mkdir()
    (project / "mb-stage.yaml").write_text("stage: scale\nsince: 2026-04-19\n")
    (project / "memory").mkdir()
    monkeypatch.chdir(project)
    result = rbac.check("fe-dev", "vercel", "deploy-prod")
    assert result.allowed is False


def test_check_strict_at_mvp_when_perms_explicitly_defined(tmp_mvp_project):
    """Once permissions.yaml exists, strict enforcement at every stage.

    Permissive default only kicks in when the file is ABSENT.
    """
    _write_perms(tmp_mvp_project, {
        "permissions": {
            "fe-dev": [{"tool": "vercel", "actions": ["deploy-preview"]}],
        },
    })
    result = rbac.check("fe-dev", "vercel", "deploy-prod")
    assert result.allowed is False
    assert "not allowed" in result.reason.lower() or "denied" in result.reason.lower()


# =================================================================
# check() — allow/deny paths
# =================================================================

def test_check_allow_when_action_listed_flat(tmp_project):
    _write_perms(tmp_project, {
        "permissions": {
            "devops": [{"tool": "vercel", "actions": ["deploy-prod"]}],
        },
    })
    result = rbac.check("devops", "vercel", "deploy-prod")
    assert result.allowed is True


def test_check_deny_when_action_not_listed(tmp_project):
    _write_perms(tmp_project, {
        "permissions": {
            "fe-dev": [{"tool": "vercel", "actions": ["deploy-preview"]}],
        },
    })
    result = rbac.check("fe-dev", "vercel", "deploy-prod")
    assert result.allowed is False


def test_check_deny_when_tool_not_listed_for_agent(tmp_project):
    _write_perms(tmp_project, {
        "permissions": {"fe-dev": []},
    })
    result = rbac.check("fe-dev", "supabase", "write")
    assert result.allowed is False


def test_check_deny_when_agent_not_in_config(tmp_project):
    """Agent absent from permissions → DENY (partial config still applies)."""
    _write_perms(tmp_project, {
        "permissions": {"devops": [{"tool": "vercel", "actions": ["deploy-prod"]}]},
    })
    result = rbac.check("fe-dev", "vercel", "deploy-preview")
    assert result.allowed is False


# =================================================================
# check() — stage-keyed actions
# =================================================================

def test_check_per_stage_mapping(tmp_project):
    """actions dict keyed by stage — mvp vs pmf vs scale lists differ."""
    _write_perms(tmp_project, {
        "permissions": {
            "be-dev": [{
                "tool": "supabase",
                "actions": {
                    "discovery": [],
                    "mvp": ["read", "write"],
                    "pmf": ["read"],
                    "scale": ["read"],
                },
            }],
        },
    })
    # tmp_project fixture = pmf
    assert rbac.check("be-dev", "supabase", "read").allowed is True
    assert rbac.check("be-dev", "supabase", "write").allowed is False


def test_check_per_stage_falls_back_to_empty_if_stage_key_missing(tmp_project):
    """Stage dict without current stage → no allowed actions → deny."""
    _write_perms(tmp_project, {
        "permissions": {
            "be-dev": [{
                "tool": "supabase",
                "actions": {"mvp": ["read"]},  # no 'pmf'/'scale'
            }],
        },
    })
    # tmp_project = pmf, not in the dict
    result = rbac.check("be-dev", "supabase", "read")
    assert result.allowed is False


def test_check_flat_actions_applies_at_every_stage(tmp_mvp_project):
    """actions as plain list → same allowance all stages."""
    _write_perms(tmp_mvp_project, {
        "permissions": {
            "fe-dev": [{"tool": "github", "actions": ["read", "write-pr"]}],
        },
    })
    result = rbac.check("fe-dev", "github", "read")
    assert result.allowed is True


# =================================================================
# audit() + auto-audit from check()
# =================================================================

def test_audit_append_writes_jsonl(tmp_project):
    rbac.audit(
        agent="fe-dev", tool="vercel", action="deploy-preview",
        allowed=True, reason="explicit allow",
    )
    log = tmp_project / "memory" / "tool-audit.jsonl"
    assert log.exists()
    entry = json.loads(log.read_text().strip())
    assert entry["agent"] == "fe-dev"
    assert entry["allowed"] is True
    assert "ts" in entry
    assert "audit_id" in entry


def test_check_auto_audits_by_default(tmp_project):
    """check() appends an audit entry automatically."""
    _write_perms(tmp_project, {
        "permissions": {
            "fe-dev": [{"tool": "vercel", "actions": ["deploy-preview"]}],
        },
    })
    rbac.check("fe-dev", "vercel", "deploy-preview")
    log = tmp_project / "memory" / "tool-audit.jsonl"
    assert log.exists()
    content = log.read_text().strip()
    assert content  # non-empty
    entry = json.loads(content)
    assert entry["allowed"] is True


def test_check_audit_opt_out(tmp_project):
    """check(..., audit=False) skips the audit write."""
    rbac.check("fe-dev", "vercel", "deploy-prod", audit=False)
    log = tmp_project / "memory" / "tool-audit.jsonl"
    assert not log.exists()


def test_audit_multiple_entries_append(tmp_project):
    """Multiple audit writes accumulate (JSONL append-only)."""
    rbac.audit(agent="a", tool="t", action="x", allowed=True, reason="ok")
    rbac.audit(agent="b", tool="t", action="y", allowed=False, reason="no")
    log = tmp_project / "memory" / "tool-audit.jsonl"
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 2


# =================================================================
# render_audit()
# =================================================================

def test_render_audit_empty_shows_placeholder(tmp_project):
    out = rbac.render_audit(limit=5)
    assert "🔒" in out
    assert "no" in out.lower() or "empty" in out.lower() or "entries" in out.lower()


def test_render_audit_shows_recent_decisions_newest_first(tmp_project):
    # Use distinctive agent names to avoid collisions with header words
    rbac.audit(agent="older-agent", tool="t", action="x", allowed=True, reason="ok")
    rbac.audit(agent="newer-agent", tool="t", action="y", allowed=False, reason="no")
    out = rbac.render_audit(limit=5)
    assert "🔒" in out
    assert "older-agent" in out and "newer-agent" in out
    # Newest first: newer-agent should appear before older-agent
    assert out.index("newer-agent") < out.index("older-agent")


def test_render_audit_uses_icons_per_decision(tmp_project):
    rbac.audit(agent="a", tool="t", action="x", allowed=True, reason="ok")
    rbac.audit(agent="b", tool="t", action="y", allowed=False, reason="no")
    out = rbac.render_audit(limit=5)
    # Allowed → ✅, denied → 🔴
    assert "✅" in out
    assert "🔴" in out


def test_render_audit_skips_corrupted_lines(tmp_project):
    rbac.audit(agent="good", tool="t", action="x", allowed=True, reason="ok")
    log = tmp_project / "memory" / "tool-audit.jsonl"
    with log.open("a", encoding="utf-8") as f:
        f.write("not json\n")
    rbac.audit(agent="also-good", tool="t", action="y", allowed=False, reason="no")
    out = rbac.render_audit(limit=5)
    assert "good" in out
    assert "also-good" in out
