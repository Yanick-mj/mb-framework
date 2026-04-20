"""Tests for deliverables.py — typed, versioned artifact storage."""
from pathlib import Path

import pytest

from scripts.v2_1 import deliverables


def test_deliverable_path_computes_correctly(tmp_project):
    """path() returns the canonical location for a deliverable."""
    p = deliverables.path("STU-46", "PLAN", rev=1)
    assert p == tmp_project / "_bmad-output" / "deliverables" / "STU-46" / "PLAN-rev1.md"


def test_write_creates_parents_and_writes_body(tmp_project):
    """write() creates the story dir and writes the body."""
    path = deliverables.write(
        story_id="STU-46",
        type="PLAN",
        body="# Plan\n\nSome content",
        author="architect",
    )
    assert path.exists()
    content = path.read_text()
    assert "author: architect" in content
    assert "# Plan" in content


def test_next_rev_returns_1_when_none_exist(tmp_project):
    """next_rev() returns 1 if no PLAN-rev*.md exists."""
    assert deliverables.next_rev("STU-46", "PLAN") == 1


def test_next_rev_increments_from_existing(tmp_project):
    """next_rev() returns max(rev) + 1 based on existing files."""
    deliverables.write("STU-46", "PLAN", "v1", author="architect")
    deliverables.write("STU-46", "PLAN", "v2", author="architect")
    assert deliverables.next_rev("STU-46", "PLAN") == 3


def test_list_deliverables_for_story(tmp_project):
    """list_for_story() returns all deliverables for a story, grouped by type."""
    deliverables.write("STU-46", "PLAN", "v1", author="architect")
    deliverables.write("STU-46", "IMPL", "v1", author="fe-dev")
    deliverables.write("STU-46", "PLAN", "v2", author="architect")

    result = deliverables.list_for_story("STU-46")
    assert "PLAN" in result
    assert len(result["PLAN"]) == 2
    assert "IMPL" in result
    assert len(result["IMPL"]) == 1


def test_list_empty_story_returns_empty_dict(tmp_project):
    """list_for_story() returns {} for an unknown story."""
    assert deliverables.list_for_story("STU-999") == {}
