"""Tests for inbox.py — unified blocker view."""
from pathlib import Path

import pytest

from scripts.v2_2 import inbox


def _write_story(root: Path, story_id: str, status: str, title: str = "") -> None:
    d = root / "_bmad-output" / "implementation-artifacts" / "stories"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{story_id}.md").write_text(
        f"---\nstory_id: {story_id}\ntitle: {title or story_id}\n"
        f"status: {status}\n---\n# Body\n"
    )


def _write_approval(project: Path, name: str) -> None:
    d = project / "memory" / "approvals-pending"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.md").write_text(f"---\nkind: {name}\n---\n")


def test_inbox_empty_returns_placeholder(tmp_project):
    out = inbox.render()
    assert "📥" in out
    assert "nothing" in out.lower()


def test_inbox_lists_in_review_stories(tmp_project):
    _write_story(tmp_project, "STU-1", "in_review", "Refactor auth")
    out = inbox.render()
    assert "STU-1" in out
    assert "Refactor auth" in out


def test_inbox_lists_blocked_stories(tmp_project):
    _write_story(tmp_project, "STU-2", "blocked", "Stuck task")
    out = inbox.render()
    assert "STU-2" in out
    assert "blocked" in out.lower() or "🚧" in out


def test_inbox_lists_pending_approvals(tmp_project):
    _write_approval(tmp_project, "hire-lead-dev")
    out = inbox.render()
    assert "hire-lead-dev" in out
    assert "approval" in out.lower() or "⏳" in out


def test_inbox_counts_items(tmp_project):
    _write_story(tmp_project, "STU-1", "in_review")
    _write_story(tmp_project, "STU-2", "blocked")
    _write_approval(tmp_project, "decision-x")
    out = inbox.render()
    assert "3" in out  # total count somewhere


def test_inbox_ignores_done_and_todo_stories(tmp_project):
    _write_story(tmp_project, "STU-1", "done", "Done task")
    _write_story(tmp_project, "STU-2", "todo", "Todo task")
    _write_story(tmp_project, "STU-3", "in_review", "Review me")
    out = inbox.render()
    assert "STU-3" in out
    assert "STU-1" not in out
    assert "STU-2" not in out
