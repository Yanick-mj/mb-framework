"""TDD tests for sprint CRUD API — STU-P2S3.5."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_sprint, write_story


class TestCreateSprintAPI:
    def test_create_sprint_json(self, client, tmp_project):
        resp = client.post("/api/sprints/demo", json={
            "name": "New Sprint",
            "goal": "Build things",
            "start_date": "2026-05-10",
            "end_date": "2026-05-12",
            "phase": "Phase 2",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Sprint"
        assert data["status"] == "planned"
        assert data["id"].startswith("sprint-")

    def test_create_sprint_form(self, client, tmp_project):
        resp = client.post("/api/sprints/demo/form", data={
            "name": "Form Sprint",
            "goal": "Test",
            "start_date": "2026-05-10",
            "end_date": "2026-05-12",
            "phase": "Phase 2",
        })
        assert resp.status_code == 201

    def test_create_sprint_404_unknown_project(self, client):
        resp = client.post("/api/sprints/nope", json={
            "name": "X", "goal": "X",
            "start_date": "2026-05-10", "end_date": "2026-05-12",
            "phase": "Phase 1",
        })
        assert resp.status_code == 404

    def test_create_sprint_422_missing_name(self, client, tmp_project):
        resp = client.post("/api/sprints/demo", json={
            "goal": "No name",
            "start_date": "2026-05-10",
            "end_date": "2026-05-12",
            "phase": "Phase 1",
        })
        assert resp.status_code == 422


class TestAddStoryToSprintAPI:
    def test_add_story(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal")
        write_story(tmp_project, "S1", "todo", "Story One")
        resp = client.post("/api/sprints/demo/sprint-1/stories",
                           json={"story_id": "S1"})
        assert resp.status_code == 200
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert "S1" in data["stories"]

    def test_add_story_404_unknown_sprint(self, client, tmp_project):
        write_story(tmp_project, "S1", "todo", "Story")
        resp = client.post("/api/sprints/demo/nope/stories",
                           json={"story_id": "S1"})
        assert resp.status_code == 404


class TestRemoveStoryFromSprintAPI:
    def test_remove_story(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=["S1"])
        write_story(tmp_project, "S1", "todo", "Story One")
        resp = client.delete("/api/sprints/demo/sprint-1/stories/S1")
        assert resp.status_code == 200

    def test_remove_story_404_unknown_sprint(self, client, tmp_project):
        resp = client.delete("/api/sprints/demo/nope/stories/S1")
        assert resp.status_code == 404


class TestCreateSprintFormPartial:
    def test_returns_form_html(self, client, tmp_project):
        resp = client.get("/partials/demo/create-sprint")
        assert resp.status_code == 200
        assert "<form" in resp.text
        assert 'name="name"' in resp.text
        assert 'name="goal"' in resp.text
        assert 'name="start_date"' in resp.text
        assert 'name="end_date"' in resp.text
        assert 'name="phase"' in resp.text

    def test_phase_dropdown_lists_roadmap_phases(self, client, tmp_project):
        from scripts.dashboard.tests.conftest import write_roadmap
        write_roadmap(tmp_project, phases=[
            {"num": "1", "name": "Foundation", "timeframe": "w1-2", "goal": "Base"},
            {"num": "2", "name": "Dashboard", "timeframe": "w3-4", "goal": "UI"},
        ])
        resp = client.get("/partials/demo/create-sprint")
        assert "Phase 1" in resp.text
        assert "Phase 2" in resp.text
