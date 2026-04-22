"""Tests for MB_NO_EMOJI=1 fallback across all render functions."""
import os

import pytest


@pytest.fixture
def no_emoji(monkeypatch):
    monkeypatch.setenv("MB_NO_EMOJI", "1")
    yield


@pytest.fixture
def with_emoji(monkeypatch):
    monkeypatch.delenv("MB_NO_EMOJI", raising=False)
    yield


def test_projects_render_ascii_fallback(no_emoji, tmp_home):
    from scripts.v2_1 import projects
    projects.add(name="a", path="/x", stage="mvp")
    out = projects.render()
    assert "[PROJECTS]" in out
    assert "📁" not in out


def test_projects_render_uses_emoji_by_default(with_emoji, tmp_home):
    from scripts.v2_1 import projects
    projects.add(name="a", path="/x", stage="mvp")
    out = projects.render()
    assert "📁" in out


def test_backlog_render_ascii_fallback(no_emoji, tmp_project):
    from scripts.v2_1 import backlog
    bk = tmp_project / "_backlog"
    bk.mkdir()
    (bk / "a.md").write_text("---\nstory_id: A\npriority: high\n---\n")
    out = backlog.render_backlog()
    assert "[BACKLOG]" in out
    assert "📋" not in out


def test_deliverables_render_ascii_fallback(no_emoji, tmp_project):
    from scripts.v2_1 import deliverables
    out = deliverables.render_list("STU-999")
    assert "[DELIVERABLES]" in out
    assert "📦" not in out


def test_runs_render_ascii_fallback(no_emoji, tmp_project):
    from scripts.v2_1 import runs
    out = runs.render_recent()
    assert "[RUNS]" in out
    assert "🏃" not in out


def test_tree_render_ascii_fallback(no_emoji, tmp_project):
    from scripts.v2_1 import tree
    out = tree.render()
    assert "[TREE]" in out
    assert "🌲" not in out


def test_mb_no_emoji_respects_zero(monkeypatch, tmp_home):
    """MB_NO_EMOJI=0 or unset → emoji on."""
    from scripts.v2_1 import projects
    monkeypatch.setenv("MB_NO_EMOJI", "0")
    projects.add(name="a", path="/x", stage="mvp")
    out = projects.render()
    assert "📁" in out
