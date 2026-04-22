"""Tests for board.py — ASCII kanban renderer."""
from pathlib import Path

import pytest

from scripts.v2_2 import board


def _write_story(root: Path, story_id: str, status: str, title: str = "T") -> None:
    d = root / "_bmad-output" / "implementation-artifacts" / "stories"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{story_id}.md").write_text(
        f"---\nstory_id: {story_id}\ntitle: {title}\nstatus: {status}\n---\n"
    )


def test_board_empty_returns_placeholder(tmp_project):
    out = board.render()
    assert "🎯" in out
    assert "no stories" in out.lower()


def test_board_groups_stories_by_status(tmp_project):
    _write_story(tmp_project, "STU-1", "backlog")
    _write_story(tmp_project, "STU-2", "todo")
    _write_story(tmp_project, "STU-3", "in_progress")
    _write_story(tmp_project, "STU-4", "in_review")
    _write_story(tmp_project, "STU-5", "done")
    out = board.render()
    assert "STU-1" in out
    assert "STU-5" in out


def test_board_column_headers_present(tmp_project):
    _write_story(tmp_project, "STU-1", "todo")
    out = board.render()
    assert "BACKLOG" in out.upper()
    assert "TODO" in out.upper()
    assert "IN PROG" in out.upper() or "IN_PROGRESS" in out.upper()
    assert "REVIEW" in out.upper()
    assert "DONE" in out.upper()


def test_board_shows_counts_per_column(tmp_project):
    _write_story(tmp_project, "STU-1", "todo")
    _write_story(tmp_project, "STU-2", "todo")
    _write_story(tmp_project, "STU-3", "done")
    out = board.render()
    # Counts should appear: 2 todos, 1 done
    assert "2" in out
    assert "1" in out


def test_board_ignores_unknown_status(tmp_project):
    """Stories with a non-standard status are skipped (strict like M10)."""
    _write_story(tmp_project, "STU-1", "todo")
    _write_story(tmp_project, "STU-2", "waiting-for-moon")
    out = board.render()
    assert "STU-1" in out
    assert "STU-2" not in out
