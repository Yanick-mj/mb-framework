"""Tests for tree.py — story parent/child ASCII renderer."""
from pathlib import Path

import pytest

from scripts.v2_1 import tree


def _write_story(root: Path, story_id: str, title: str, parent: str | None = None,
                 children: list[str] | None = None):
    stories_dir = root / "_bmad-output" / "implementation-artifacts" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    fm = ["---", f"story_id: {story_id}", f"title: {title}"]
    if parent:
        fm.append(f"parent_story: {parent}")
    if children:
        fm.append(f"children: [{', '.join(children)}]")
    fm.append("---")
    fm.append(f"\n# {title}\n")
    (stories_dir / f"{story_id}.md").write_text("\n".join(fm))


def test_scan_stories_empty_returns_empty_list(tmp_project):
    assert tree.scan_stories() == []


def test_scan_stories_reads_frontmatter(tmp_project):
    _write_story(tmp_project, "STU-1", "Root")
    _write_story(tmp_project, "STU-2", "Child", parent="STU-1")
    stories = tree.scan_stories()
    assert len(stories) == 2
    ids = {s["story_id"] for s in stories}
    assert ids == {"STU-1", "STU-2"}


def test_render_tree_simple_parent_child(tmp_project):
    _write_story(tmp_project, "STU-1", "Root")
    _write_story(tmp_project, "STU-2", "Child", parent="STU-1")
    output = tree.render()
    assert "STU-1" in output
    assert "STU-2" in output
    # Child should be indented below parent
    lines = output.splitlines()
    stu1_idx = next(i for i, l in enumerate(lines) if "STU-1" in l)
    stu2_idx = next(i for i, l in enumerate(lines) if "STU-2" in l)
    assert stu2_idx > stu1_idx


def test_render_tree_focused_on_story(tmp_project):
    _write_story(tmp_project, "STU-1", "Root")
    _write_story(tmp_project, "STU-2", "Child", parent="STU-1")
    _write_story(tmp_project, "STU-3", "Grandchild", parent="STU-2")
    output = tree.render(focus="STU-2")
    assert "STU-2" in output
    assert "STU-3" in output
    # Should show focus marker
    assert "←" in output or "*" in output


def test_render_tree_orphan_story(tmp_project):
    """Stories without parent appear at root level."""
    _write_story(tmp_project, "STU-1", "Orphan")
    output = tree.render()
    assert "STU-1" in output


def test_cycle_does_not_crash(tmp_project):
    """Mutual parent references render [CYCLE] instead of infinite recursion."""
    _write_story(tmp_project, "STU-1", "A", parent="STU-2")
    _write_story(tmp_project, "STU-2", "B", parent="STU-1")
    output = tree.render()  # should not raise RecursionError
    assert "[CYCLE]" in output


def test_missing_parent_promotes_to_root(tmp_project):
    """Story referencing non-existent parent appears at root level."""
    _write_story(tmp_project, "STU-5", "Orphaned child", parent="STU-99")
    output = tree.render()
    assert "STU-5" in output


def test_malformed_yaml_skips_file(tmp_project):
    """Story file with broken YAML is silently skipped."""
    stories_dir = tmp_project / "_bmad-output" / "implementation-artifacts" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    (stories_dir / "bad.md").write_text("---\n: [\ninvalid {{{\n---\n# Bad\n")
    _write_story(tmp_project, "STU-1", "Good")
    stories = tree.scan_stories()
    assert len(stories) == 1
    assert stories[0]["story_id"] == "STU-1"
