"""Tests for migrate_stories.py — add status: to legacy stories."""
from pathlib import Path

import pytest

from scripts.v2_2 import migrate_stories


def _write_story(dir: Path, name: str, frontmatter_body: str) -> Path:
    dir.mkdir(parents=True, exist_ok=True)
    f = dir / name
    f.write_text(f"---\n{frontmatter_body}\n---\n# Body\n")
    return f


def test_adds_todo_status_to_stories_dir(tmp_project):
    s = _write_story(
        tmp_project / "_mb-output" / "implementation-artifacts" / "stories",
        "STU-1.md",
        "story_id: STU-1\ntitle: X",
    )
    migrate_stories.run(dry_run=False)
    assert "status: todo" in s.read_text()


def test_adds_backlog_status_to_backlog_dir(tmp_project):
    s = _write_story(
        tmp_project / "_backlog", "STU-2.md",
        "story_id: STU-2\ntitle: Y",
    )
    migrate_stories.run(dry_run=False)
    assert "status: backlog" in s.read_text()


def test_preserves_existing_status(tmp_project):
    s = _write_story(
        tmp_project / "_mb-output" / "implementation-artifacts" / "stories",
        "STU-3.md",
        "story_id: STU-3\nstatus: done",
    )
    migrate_stories.run(dry_run=False)
    assert "status: done" in s.read_text()
    assert s.read_text().count("status:") == 1


def test_dry_run_does_not_modify(tmp_project):
    s = _write_story(
        tmp_project / "_backlog", "STU-4.md", "story_id: STU-4",
    )
    report = migrate_stories.run(dry_run=True)
    assert len(report.updated) == 1
    assert "status:" not in s.read_text().split("---")[1]


def test_skips_files_without_frontmatter(tmp_project):
    d = tmp_project / "_backlog"
    d.mkdir()
    f = d / "not-a-story.md"
    f.write_text("# Just markdown, no frontmatter\n")
    report = migrate_stories.run(dry_run=False)
    assert str(f) in report.no_frontmatter
