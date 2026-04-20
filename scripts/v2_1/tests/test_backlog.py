"""Tests for backlog.py — scan _backlog/ + read _roadmap.md."""
from pathlib import Path

import pytest

from scripts.v2_1 import backlog


def test_list_backlog_empty_no_dir(tmp_project):
    """If _backlog/ is absent, list_backlog() returns []."""
    assert backlog.list_backlog() == []


def test_list_backlog_empty_dir_returns_empty(tmp_project):
    """If _backlog/ exists but contains no .md files, list is empty."""
    (tmp_project / "_backlog").mkdir()
    assert backlog.list_backlog() == []


def test_list_backlog_returns_story_metadata(tmp_project):
    """A single story file is parsed from frontmatter."""
    (tmp_project / "_backlog").mkdir()
    (tmp_project / "_backlog" / "STU-52-add-stripe.md").write_text(
        "---\n"
        "story_id: STU-52\n"
        "title: Add Stripe checkout\n"
        "priority: high\n"
        "---\n\n"
        "# Body\n"
    )
    items = backlog.list_backlog()
    assert len(items) == 1
    assert items[0]["story_id"] == "STU-52"
    assert items[0]["priority"] == "high"
    assert items[0]["title"] == "Add Stripe checkout"


def test_list_backlog_sorts_by_priority(tmp_project):
    """Stories come back in critical -> high -> medium -> low order."""
    bk = tmp_project / "_backlog"
    bk.mkdir()
    (bk / "a.md").write_text("---\nstory_id: A\npriority: low\n---\n")
    (bk / "b.md").write_text("---\nstory_id: B\npriority: high\n---\n")
    (bk / "c.md").write_text("---\nstory_id: C\npriority: medium\n---\n")
    (bk / "d.md").write_text("---\nstory_id: D\npriority: critical\n---\n")
    items = backlog.list_backlog()
    assert [i["story_id"] for i in items] == ["D", "B", "C", "A"]


def test_list_backlog_default_priority_is_medium(tmp_project):
    """Stories without a priority field sort as 'medium'."""
    bk = tmp_project / "_backlog"
    bk.mkdir()
    (bk / "a.md").write_text("---\nstory_id: A\npriority: low\n---\n")
    (bk / "b.md").write_text("---\nstory_id: B\n---\n")  # no priority
    (bk / "c.md").write_text("---\nstory_id: C\npriority: high\n---\n")
    items = backlog.list_backlog()
    assert [i["story_id"] for i in items] == ["C", "B", "A"]


def test_list_backlog_ignores_malformed_yaml(tmp_project):
    """Files with invalid frontmatter are silently skipped."""
    bk = tmp_project / "_backlog"
    bk.mkdir()
    (bk / "good.md").write_text("---\nstory_id: OK\npriority: high\n---\n")
    (bk / "bad.md").write_text("---\nstory_id: [unclosed list\n---\n")
    (bk / "no-frontmatter.md").write_text("# Just a plain md\n")
    items = backlog.list_backlog()
    assert len(items) == 1
    assert items[0]["story_id"] == "OK"


def test_render_backlog_empty_returns_placeholder(tmp_project):
    out = backlog.render_backlog()
    assert "No stories" in out


def test_render_backlog_shows_priority_and_title(tmp_project):
    bk = tmp_project / "_backlog"
    bk.mkdir()
    (bk / "a.md").write_text(
        "---\nstory_id: STU-99\ntitle: Hello\npriority: high\n---\n"
    )
    out = backlog.render_backlog()
    assert "STU-99" in out
    assert "Hello" in out
    assert "high" in out


def test_read_roadmap_missing_returns_placeholder(tmp_project):
    out = backlog.read_roadmap()
    assert "No _roadmap.md" in out


def test_read_roadmap_returns_body(tmp_project):
    (tmp_project / "_roadmap.md").write_text("# Roadmap\n\nPhase 1 done.")
    out = backlog.read_roadmap()
    assert "Phase 1 done" in out
