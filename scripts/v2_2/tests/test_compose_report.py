"""Tests for compose_report.py — composed SKILL.md size + rejection monitor.

Scaffold in Task 0 to enable early observability. Real G6 tests add more cases.
"""
import json

import pytest

from scripts.v2_2 import compose_report


def _write_composed_skill(project, name: str, body: str) -> None:
    d = project / ".claude" / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(body, encoding="utf-8")


# =================================================================
# scan_sizes
# =================================================================

def test_scan_sizes_empty_returns_empty_list(tmp_project):
    """No .claude/skills/ yet → empty result, no crash."""
    assert compose_report.scan_sizes() == []


def test_scan_sizes_flags_ok_below_thresholds(tmp_project):
    _write_composed_skill(tmp_project, "mb-small", "line\n" * 100)  # 100 lines
    results = compose_report.scan_sizes()
    assert len(results) == 1
    assert results[0]["flag"] == "ok"


def test_scan_sizes_flags_warning_between_thresholds(tmp_project):
    _write_composed_skill(tmp_project, "mb-mid", "line\n" * 700)  # 700 lines
    results = compose_report.scan_sizes()
    assert results[0]["flag"] == "warning"


def test_scan_sizes_flags_critical_above_thresholds(tmp_project):
    _write_composed_skill(tmp_project, "mb-huge", "x\n" * 1500)  # 1500 lines
    results = compose_report.scan_sizes()
    assert results[0]["flag"] == "critical"


def test_scan_sizes_handles_mixed_flags(tmp_project):
    _write_composed_skill(tmp_project, "mb-small", "x\n" * 100)
    _write_composed_skill(tmp_project, "mb-mid", "x\n" * 700)
    _write_composed_skill(tmp_project, "mb-huge", "x\n" * 1500)
    results = compose_report.scan_sizes()
    flags = {r["name"]: r["flag"] for r in results}
    assert flags == {"mb-small": "ok", "mb-mid": "warning", "mb-huge": "critical"}


def test_scan_sizes_skips_entries_without_skill_md(tmp_project):
    """Entries in .claude/skills/ without SKILL.md inside are skipped."""
    d = tmp_project / ".claude" / "skills" / "mb-empty-dir"
    d.mkdir(parents=True)
    # No SKILL.md inside
    _write_composed_skill(tmp_project, "mb-normal", "x\n" * 100)
    results = compose_report.scan_sizes()
    assert len(results) == 1
    assert results[0]["name"] == "mb-normal"


# =================================================================
# log_rejection / load_rejections
# =================================================================

def test_log_rejection_creates_jsonl_entry(tmp_project):
    compose_report.log_rejection(
        skill="mb-fe-dev", reason="too_large",
        context="composed at install", bytes_size=120_000,
    )
    log = tmp_project / "memory" / "claude-skill-rejections.jsonl"
    assert log.exists()
    entry = json.loads(log.read_text().strip())
    assert entry["skill"] == "mb-fe-dev"
    assert entry["reason"] == "too_large"
    assert entry["bytes"] == 120_000
    assert "ts" in entry


def test_log_rejection_creates_memory_dir_if_missing(tmp_path, monkeypatch):
    """If memory/ doesn't exist yet, log_rejection creates it."""
    bare = tmp_path / "bare"
    bare.mkdir()
    monkeypatch.chdir(bare)
    compose_report.log_rejection(skill="mb-x", reason="test")
    assert (bare / "memory" / "claude-skill-rejections.jsonl").exists()


def test_load_rejections_missing_log_returns_empty(tmp_project):
    assert compose_report.load_rejections() == []


def test_load_rejections_returns_newest_first(tmp_project):
    compose_report.log_rejection(skill="a", reason="x")
    compose_report.log_rejection(skill="b", reason="x")
    compose_report.log_rejection(skill="c", reason="x")
    entries = compose_report.load_rejections(limit=10)
    assert [e["skill"] for e in entries] == ["c", "b", "a"]


def test_load_rejections_limit_respected(tmp_project):
    for name in ["a", "b", "c", "d", "e"]:
        compose_report.log_rejection(skill=name, reason="x")
    entries = compose_report.load_rejections(limit=3)
    assert len(entries) == 3
    assert [e["skill"] for e in entries] == ["e", "d", "c"]


def test_load_rejections_skips_corrupted_lines(tmp_project):
    """Malformed JSONL lines are silently skipped; valid ones load fine."""
    compose_report.log_rejection(skill="good", reason="ok")
    log = tmp_project / "memory" / "claude-skill-rejections.jsonl"
    with log.open("a", encoding="utf-8") as f:
        f.write("this is not json\n")
    compose_report.log_rejection(skill="also-good", reason="ok")
    entries = compose_report.load_rejections(limit=10)
    assert len(entries) == 2
    assert [e["skill"] for e in entries] == ["also-good", "good"]


# =================================================================
# render (integration)
# =================================================================

def test_render_no_skills_placeholder(tmp_project):
    out = compose_report.render()
    assert "no .claude/skills/" in out.lower() or "composed yet" in out.lower()


def test_render_surfaces_warnings_and_critics(tmp_project):
    _write_composed_skill(tmp_project, "mb-mid", "x\n" * 700)
    _write_composed_skill(tmp_project, "mb-huge", "x\n" * 1500)
    out = compose_report.render()
    assert "mb-mid" in out
    assert "mb-huge" in out
    assert "warning" in out.lower() or "⚠" in out
    assert "critical" in out.lower() or "🔴" in out


def test_render_surfaces_rejections(tmp_project):
    _write_composed_skill(tmp_project, "mb-normal", "x\n" * 100)
    compose_report.log_rejection(
        skill="mb-fe-dev", reason="too_large", bytes_size=150_000
    )
    out = compose_report.render()
    assert "mb-fe-dev" in out
    assert "too_large" in out
    assert "rejection" in out.lower()
