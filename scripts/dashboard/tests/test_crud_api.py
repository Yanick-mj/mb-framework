"""TDD tests for story CRUD API — Sprint 1 Phase 2.

Tests written FIRST. Endpoints don't exist yet.
"""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fastapi.testclient import TestClient
from scripts.dashboard.server import app
from scripts.dashboard.tests.conftest import (
    register_projects, write_story,
)


@pytest.fixture
def client(tmp_home, tmp_project):
    """TestClient with a registered project."""
    register_projects(tmp_home, [
        {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
    ])
    return TestClient(app)


@pytest.fixture
def stories_dir(tmp_project):
    """Ensure stories directory exists and return path."""
    d = tmp_project / "_bmad-output" / "implementation-artifacts" / "stories"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- POST /api/stories ---

class TestCreateStory:
    def test_creates_story_file_on_disk(self, client, tmp_project, stories_dir):
        resp = client.post("/api/stories/demo", json={
            "title": "Fix auth bug",
            "description": "Login broken on Safari",
            "priority": "high",
            "status": "todo",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["story_id"]
        assert data["title"] == "Fix auth bug"
        # Verify file exists on disk
        story_file = stories_dir / f"{data['story_id']}.md"
        assert story_file.exists()

    def test_created_file_has_valid_frontmatter(self, client, tmp_project, stories_dir):
        resp = client.post("/api/stories/demo", json={
            "title": "Add dark mode",
            "description": "Users want dark mode",
            "priority": "medium",
            "status": "todo",
        })
        data = resp.json()
        story_file = stories_dir / f"{data['story_id']}.md"
        text = story_file.read_text()
        # Parse frontmatter
        assert text.startswith("---\n")
        fm_end = text.index("---", 4)
        fm = yaml.safe_load(text[4:fm_end])
        assert fm["title"] == "Add dark mode"
        assert fm["priority"] == "medium"
        assert fm["status"] == "todo"
        assert fm["story_id"] == data["story_id"]

    def test_created_file_has_description_in_body(self, client, tmp_project, stories_dir):
        resp = client.post("/api/stories/demo", json={
            "title": "Test body",
            "description": "This is the description",
            "priority": "low",
            "status": "todo",
        })
        data = resp.json()
        story_file = stories_dir / f"{data['story_id']}.md"
        text = story_file.read_text()
        assert "This is the description" in text

    def test_returns_422_without_title(self, client):
        resp = client.post("/api/stories/demo", json={
            "description": "No title",
            "priority": "medium",
            "status": "todo",
        })
        assert resp.status_code == 422

    def test_returns_404_unknown_project(self, client):
        resp = client.post("/api/stories/unknown", json={
            "title": "Test",
            "description": "x",
            "priority": "medium",
            "status": "todo",
        })
        assert resp.status_code == 404

    def test_generates_unique_story_ids(self, client, tmp_project, stories_dir):
        ids = set()
        for i in range(5):
            resp = client.post("/api/stories/demo", json={
                "title": f"Story {i}",
                "description": f"Desc {i}",
                "priority": "medium",
                "status": "todo",
            })
            ids.add(resp.json()["story_id"])
        assert len(ids) == 5


# --- PUT /api/stories/{id} ---

class TestUpdateStory:
    def test_updates_title(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S1", "todo", "Old Title", "medium")
        resp = client.put("/api/stories/demo/S1", json={
            "title": "New Title",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "New Title"
        # Verify on disk
        text = (stories_dir / "S1.md").read_text()
        fm_end = text.index("---", 4)
        fm = yaml.safe_load(text[4:fm_end])
        assert fm["title"] == "New Title"

    def test_updates_priority(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S2", "todo", "Story", "medium")
        resp = client.put("/api/stories/demo/S2", json={
            "priority": "critical",
        })
        assert resp.status_code == 200
        assert resp.json()["priority"] == "critical"

    def test_updates_status(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S3", "todo", "Story")
        resp = client.put("/api/stories/demo/S3", json={
            "status": "in_progress",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_updates_description(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S4", "todo", "Story")
        resp = client.put("/api/stories/demo/S4", json={
            "description": "Updated description content",
        })
        assert resp.status_code == 200
        text = (stories_dir / "S4.md").read_text()
        assert "Updated description content" in text

    def test_partial_update_preserves_other_fields(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S5", "in_progress", "Keep This", "high")
        resp = client.put("/api/stories/demo/S5", json={
            "priority": "low",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Keep This"
        assert data["status"] == "in_progress"
        assert data["priority"] == "low"

    def test_returns_404_missing_story(self, client, tmp_project):
        resp = client.put("/api/stories/demo/NOPE", json={
            "title": "x",
        })
        assert resp.status_code == 404

    def test_returns_404_unknown_project(self, client):
        resp = client.put("/api/stories/unknown/S1", json={
            "title": "x",
        })
        assert resp.status_code == 404


# --- DELETE /api/stories/{id} ---

class TestDeleteStory:
    def test_deletes_story_file(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "DEL1", "todo", "To Delete")
        assert (stories_dir / "DEL1.md").exists()
        resp = client.delete("/api/stories/demo/DEL1")
        assert resp.status_code == 200
        assert not (stories_dir / "DEL1.md").exists()

    def test_returns_deleted_story_data(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "DEL2", "done", "Was Done", "low")
        resp = client.delete("/api/stories/demo/DEL2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["story_id"] == "DEL2"
        assert data["title"] == "Was Done"

    def test_returns_404_missing_story(self, client, tmp_project):
        resp = client.delete("/api/stories/demo/NOPE")
        assert resp.status_code == 404

    def test_returns_404_unknown_project(self, client):
        resp = client.delete("/api/stories/unknown/S1")
        assert resp.status_code == 404


# --- File locking ---

class TestFileLocking:
    def test_concurrent_writes_dont_corrupt(self, client, tmp_project, stories_dir):
        """Create multiple stories rapidly — no file corruption."""
        for i in range(10):
            resp = client.post("/api/stories/demo", json={
                "title": f"Concurrent {i}",
                "description": f"Desc {i}",
                "priority": "medium",
                "status": "todo",
            })
            assert resp.status_code == 201
        # All files should be valid
        for f in stories_dir.glob("*.md"):
            text = f.read_text()
            assert text.startswith("---\n")
            fm_end = text.index("---", 4)
            fm = yaml.safe_load(text[4:fm_end])
            assert "story_id" in fm
            assert "title" in fm

    def test_atomic_write_no_partial_file(self, client, tmp_project, stories_dir):
        """After write, file is complete (not half-written)."""
        resp = client.post("/api/stories/demo", json={
            "title": "Atomic test",
            "description": "Should be fully written",
            "priority": "high",
            "status": "todo",
        })
        data = resp.json()
        story_file = stories_dir / f"{data['story_id']}.md"
        text = story_file.read_text()
        # File must end with newline (complete write)
        assert text.endswith("\n")
        # Frontmatter must be parseable
        fm_end = text.index("---", 4)
        fm = yaml.safe_load(text[4:fm_end])
        assert fm["title"] == "Atomic test"


# --- Create form partial ---

class TestCreateFormPartial:
    def test_returns_form_html(self, client):
        resp = client.get("/partials/demo/create-story")
        assert resp.status_code == 200
        assert "<form" in resp.text
        assert 'name="title"' in resp.text
        assert 'name="description"' in resp.text
        assert 'name="priority"' in resp.text

    def test_form_targets_api_endpoint(self, client):
        resp = client.get("/partials/demo/create-story")
        assert resp.status_code == 200
        assert "/api/stories/demo/form" in resp.text

    def test_404_unknown_project(self, client):
        resp = client.get("/partials/unknown/create-story")
        assert resp.status_code == 404


# --- Edit form partial ---

class TestEditFormPartial:
    def test_returns_edit_form_with_current_values(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "EDIT1", "todo", "Original Title", "high")
        resp = client.get("/partials/demo/edit-story/EDIT1")
        assert resp.status_code == 200
        assert "<form" in resp.text
        assert "Original Title" in resp.text
        assert 'name="title"' in resp.text

    def test_form_targets_put_endpoint(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "EDIT2", "in_progress", "My Story")
        resp = client.get("/partials/demo/edit-story/EDIT2")
        assert resp.status_code == 200
        assert "/api/stories/demo/EDIT2/form" in resp.text

    def test_returns_404_missing_story(self, client, tmp_project):
        resp = client.get("/partials/demo/edit-story/NOPE")
        assert resp.status_code == 404

    def test_returns_404_unknown_project(self, client):
        resp = client.get("/partials/unknown/edit-story/X")
        assert resp.status_code == 404


# --- Delete button in modal ---

class TestDeleteFromModal:
    def test_story_modal_has_delete_button(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "DEL1", "todo", "Deletable")
        resp = client.get("/partials/demo/story/DEL1")
        assert resp.status_code == 200
        assert "hx-delete" in resp.text
        assert "/api/stories/demo/DEL1" in resp.text
        assert "hx-confirm" in resp.text

    def test_story_modal_has_edit_button(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "E1", "todo", "Editable")
        resp = client.get("/partials/demo/story/E1")
        assert resp.status_code == 200
        assert "/edit-story/E1" in resp.text

    def test_delete_via_api_removes_from_board(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "GONE", "todo", "Will disappear")
        # Confirm it's on the board
        resp = client.get("/partials/demo/board")
        assert "GONE" in resp.text
        # Delete it
        resp = client.delete("/api/stories/demo/GONE")
        assert resp.status_code == 200
        # Gone from board
        resp = client.get("/partials/demo/board")
        assert "GONE" not in resp.text
