"""TDD tests for PATCH /api/stories/{id}/status — Sprint 2 S2.2.

Tests written FIRST. Endpoint doesn't exist yet.
"""
import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fastapi.testclient import TestClient
from scripts.dashboard.server import app
from scripts.dashboard.tests.conftest import (
    register_projects, write_story, write_runs,
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
    d = tmp_project / "_bmad-output" / "implementation-artifacts" / "stories"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- PATCH /api/stories/{name}/{story_id}/status ---

class TestPatchStatus:
    def test_updates_status_in_frontmatter(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S1", "todo", "Fix bug")
        resp = client.patch("/api/stories/demo/S1/status", json={"status": "in_progress"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "in_progress"
        # Verify on disk
        text = (stories_dir / "S1.md").read_text()
        fm_end = text.index("---", 4)
        fm = yaml.safe_load(text[4:fm_end])
        assert fm["status"] == "in_progress"

    def test_preserves_other_fields(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S2", "todo", "Keep Title", "high")
        resp = client.patch("/api/stories/demo/S2/status", json={"status": "done"})
        assert resp.status_code == 200
        text = (stories_dir / "S2.md").read_text()
        fm_end = text.index("---", 4)
        fm = yaml.safe_load(text[4:fm_end])
        assert fm["title"] == "Keep Title"
        assert fm["priority"] == "high"
        assert fm["story_id"] == "S2"

    def test_invalid_status_returns_422(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S3", "todo", "Story")
        resp = client.patch("/api/stories/demo/S3/status", json={"status": "invalid"})
        assert resp.status_code == 422

    def test_not_found_returns_404(self, client, tmp_project):
        resp = client.patch("/api/stories/demo/NOPE/status", json={"status": "done"})
        assert resp.status_code == 404

    def test_unknown_project_returns_404(self, client):
        resp = client.patch("/api/stories/unknown/S1/status", json={"status": "done"})
        assert resp.status_code == 404

    def test_returns_story_data(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S4", "in_review", "Review Me", "critical")
        resp = client.patch("/api/stories/demo/S4/status", json={"status": "done"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["story_id"] == "S4"
        assert data["title"] == "Review Me"
        assert data["status"] == "done"
        assert data["priority"] == "critical"

    def test_all_valid_statuses_accepted(self, client, tmp_project, stories_dir):
        for i, status in enumerate(["backlog", "todo", "in_progress", "in_review", "done"]):
            sid = f"ST{i}"
            write_story(tmp_project, sid, "todo", f"Story {i}")
            resp = client.patch(f"/api/stories/demo/{sid}/status", json={"status": status})
            assert resp.status_code == 200, f"Failed for status={status}"
            assert resp.json()["status"] == status

    def test_logs_status_transition(self, client, tmp_project, stories_dir):
        runs_file = tmp_project / "memory" / "agents" / "_common" / "runs.jsonl"
        runs_file.parent.mkdir(parents=True, exist_ok=True)
        write_story(tmp_project, "S5", "todo", "Log test")
        client.patch("/api/stories/demo/S5/status", json={"status": "in_progress"})
        assert runs_file.exists()
        lines = runs_file.read_text().strip().splitlines()
        last = json.loads(lines[-1])
        assert last["action"] == "status_change"
        assert last["story"] == "S5"
        assert last["from_status"] == "todo"
        assert last["to_status"] == "in_progress"
