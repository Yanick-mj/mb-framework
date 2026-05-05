"""TDD tests for sprint routes — STU-P2S3.2 + STU-P2S3.3."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_sprint, write_story


class TestSprintsListPage:
    def test_returns_200(self, client, tmp_project):
        resp = client.get("/projects/demo/sprints")
        assert resp.status_code == 200

    def test_shows_sprint_cards(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "CRUD", "Ship CRUD",
                     status="closed", phase="Phase 2")
        resp = client.get("/projects/demo/sprints")
        assert resp.status_code == 200
        assert "CRUD" in resp.text

    def test_active_sprint_has_active_class(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Active One", "Goal",
                     status="active")
        resp = client.get("/projects/demo/sprints")
        assert "active-sprint" in resp.text

    def test_shows_progress_info(self, client, tmp_project):
        write_story(tmp_project, "S1", "done", "Done Story")
        write_story(tmp_project, "S2", "todo", "Todo Story")
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     status="active", stories=["S1", "S2"])
        resp = client.get("/projects/demo/sprints")
        assert "1 / 2" in resp.text or "50%" in resp.text

    def test_empty_state_when_no_sprints(self, client, tmp_project):
        resp = client.get("/projects/demo/sprints")
        assert "no sprint" in resp.text.lower() or "No sprints" in resp.text

    def test_404_unknown_project(self, client):
        resp = client.get("/projects/nope/sprints")
        assert resp.status_code == 404

    def test_sidebar_has_sprints_link(self, client, tmp_project):
        resp = client.get("/projects/demo/sprints")
        assert "/projects/demo/sprints" in resp.text
        assert "Sprints" in resp.text


class TestSprintsPartial:
    def test_returns_sprint_list_html(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        resp = client.get("/partials/demo/sprints")
        assert resp.status_code == 200
        assert "sprint-1" in resp.text.lower() or "Sprint" in resp.text

    def test_404_unknown_project(self, client):
        resp = client.get("/partials/nope/sprints")
        assert resp.status_code == 404
