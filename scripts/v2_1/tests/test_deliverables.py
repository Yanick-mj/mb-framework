"""Tests for deliverables.py — typed, versioned artifact storage."""
from pathlib import Path

import pytest

from scripts.v2_1 import deliverables


def test_deliverable_path_computes_correctly(tmp_project):
    """path() returns the canonical location for a deliverable."""
    p = deliverables.path("STU-46", "PLAN", rev=1)
    assert p == tmp_project / "_mb-output" / "deliverables" / "STU-46" / "PLAN-rev1.md"


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
    deliverables.write("STU-46", "PLAN", body="first plan", author="architect")
    deliverables.write("STU-46", "PLAN", body="refined plan", author="architect")
    assert deliverables.next_rev("STU-46", "PLAN") == 3


def test_list_deliverables_for_story(tmp_project):
    """list_for_story() returns all deliverables for a story, grouped by type."""
    deliverables.write("STU-46", "PLAN", body="p1", author="architect")
    deliverables.write("STU-46", "IMPL", body="i1", author="fe-dev")
    deliverables.write("STU-46", "PLAN", body="p2", author="architect")

    result = deliverables.list_for_story("STU-46")
    assert "PLAN" in result
    assert len(result["PLAN"]) == 2
    assert "IMPL" in result
    assert len(result["IMPL"]) == 1


def test_list_empty_story_returns_empty_dict(tmp_project):
    """list_for_story() returns {} for an unknown story."""
    assert deliverables.list_for_story("STU-999") == {}


def test_path_rejects_invalid_type(tmp_project):
    """path() raises ValueError for an unknown type."""
    with pytest.raises(ValueError, match="Invalid type"):
        deliverables.path("STU-46", "GARBAGE", 1)


def test_next_rev_rejects_invalid_type(tmp_project):
    """next_rev() raises ValueError for an unknown type."""
    with pytest.raises(ValueError, match="Invalid type"):
        deliverables.next_rev("STU-46", "GARBAGE")


def test_list_for_story_ignores_invalid_types(tmp_project):
    """list_for_story() skips files that don't match VALID_TYPES."""
    story_dir = tmp_project / "_mb-output" / "deliverables" / "STU-46"
    story_dir.mkdir(parents=True)
    (story_dir / "PLAN-rev1.md").write_text("valid")
    (story_dir / "JUNK-rev1.md").write_text("stray file")
    result = deliverables.list_for_story("STU-46")
    assert "PLAN" in result
    assert "JUNK" not in result


def test_write_does_not_clobber_existing_rev(tmp_project):
    """If an explicit rev clashes (race condition), write() auto-increments.

    Simulates the race: two agents each compute next_rev()=1, both try to write
    rev=1. The second call must NOT overwrite — it should land on rev=2.
    """
    deliverables.write(
        story_id="STU-46", type="PLAN", body="first", author="a"
    )
    path2 = deliverables.write(
        story_id="STU-46", type="PLAN", body="second", author="b", rev=1
    )
    assert path2.name == "PLAN-rev2.md"
    first = deliverables.path("STU-46", "PLAN", 1).read_text()
    second = path2.read_text()
    assert "first" in first
    assert "second" in second


def test_path_rejects_path_traversal_in_story_id(tmp_project):
    """story_id with path separators or parent refs must be rejected.

    Defense-in-depth: mb is Claude-Code-local today but if it ever accepts
    untrusted input (web UI, remote trigger), unsanitized story_id would let
    an attacker write outside the _mb-output/deliverables/ sandbox.
    """
    for bad in [
        "../../etc/passwd",
        "../escape",
        "STU-46/subdir",         # contains slash
        "STU-46\x00null",        # null byte
        ".",                     # cwd reference
        "",                      # empty
        "STU 46",                # space
        "STU-46; rm -rf /",      # shell meta
    ]:
        with pytest.raises(ValueError, match="story_id"):
            deliverables.path(bad, "PLAN", 1)


def test_next_rev_rejects_path_traversal(tmp_project):
    for bad in ["../etc", "foo/bar"]:
        with pytest.raises(ValueError, match="story_id"):
            deliverables.next_rev(bad, "PLAN")


def test_write_rejects_path_traversal(tmp_project):
    with pytest.raises(ValueError, match="story_id"):
        deliverables.write(
            story_id="../escape", type="PLAN", body="x", author="a"
        )


def test_list_for_story_rejects_path_traversal(tmp_project):
    with pytest.raises(ValueError, match="story_id"):
        deliverables.list_for_story("../etc")


def test_render_list_uses_emoji(tmp_project):
    """render_list() output carries the deliverables emoji in both states."""
    # Empty path
    assert "📦" in deliverables.render_list("STU-999")
    # Non-empty path
    deliverables.write("STU-46", "PLAN", body="x", author="a")
    assert "📦" in deliverables.render_list("STU-46")


def test_write_with_explicit_unique_rev_uses_it(tmp_project):
    """Explicit rev that doesn't clash is honored verbatim."""
    path = deliverables.write(
        story_id="STU-46", type="PLAN", body="x", author="a", rev=5
    )
    assert path.name == "PLAN-rev5.md"
