"""Integration tests for dashboard routes via FastAPI TestClient."""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fastapi.testclient import TestClient
from scripts.dashboard.server import app
from scripts.dashboard.tests.conftest import (
    register_projects, write_story, write_runs, write_roadmap,
)


class TestRootRedirect:
    def test_redirects_to_first_project_overview(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        client = TestClient(app, follow_redirects=False)
        resp = client.get("/")
        assert resp.status_code == 307
        assert "/projects/demo/overview" in resp.headers["location"]

    def test_no_projects_returns_200_with_message(self, tmp_home):
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        assert "no project" in resp.text.lower()


class TestOverviewPage:
    def test_returns_200_with_stage(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        client = TestClient(app)
        resp = client.get("/projects/demo/overview")
        assert resp.status_code == 200
        assert "mvp" in resp.text.lower()

    def test_unknown_project_returns_404(self, tmp_home):
        client = TestClient(app)
        resp = client.get("/projects/nope/overview")
        assert resp.status_code == 404


class TestBoardPage:
    def test_returns_200_with_columns(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        write_story(tmp_project, "S1", "todo", "My Story")
        client = TestClient(app)
        resp = client.get("/projects/demo/board")
        assert resp.status_code == 200
        assert "S1" in resp.text

    def test_unknown_project_returns_404(self, tmp_home):
        client = TestClient(app)
        resp = client.get("/projects/nope/board")
        assert resp.status_code == 404


class TestPartials:
    @pytest.fixture(autouse=True)
    def setup_project(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        self.project_path = tmp_project
        self.client = TestClient(app)

    def test_stage_partial(self):
        resp = self.client.get("/partials/demo/stage")
        assert resp.status_code == 200
        assert "mvp" in resp.text.lower()

    def test_stats_partial(self):
        write_story(self.project_path, "S1", "todo")
        resp = self.client.get("/partials/demo/stats")
        assert resp.status_code == 200

    def test_runs_partial(self):
        write_runs(self.project_path, count=2)
        resp = self.client.get("/partials/demo/runs")
        assert resp.status_code == 200

    def test_board_partial(self):
        write_story(self.project_path, "S1", "todo", "Board Card")
        resp = self.client.get("/partials/demo/board")
        assert resp.status_code == 200
        assert "S1" in resp.text

    def test_inbox_count_partial(self):
        resp = self.client.get("/partials/demo/inbox-count")
        assert resp.status_code == 200

    def test_story_modal_returns_detail(self):
        write_story(self.project_path, "S1", "todo", "My Story", "high")
        resp = self.client.get("/partials/demo/story/S1")
        assert resp.status_code == 200
        assert "My Story" in resp.text

    def test_story_modal_404_if_missing(self):
        resp = self.client.get("/partials/demo/story/NOPE")
        assert resp.status_code == 404

    def test_partial_404_unknown_project(self):
        resp = self.client.get("/partials/nope/stage")
        assert resp.status_code == 404


class TestRoadmapPage:
    def test_returns_200_with_mission(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        write_roadmap(tmp_project, mission="Build greatness.")
        client = TestClient(app)
        resp = client.get("/projects/demo/roadmap")
        assert resp.status_code == 200
        assert "Build greatness" in resp.text

    def test_unknown_project_returns_404(self, tmp_home):
        client = TestClient(app)
        resp = client.get("/projects/nope/roadmap")
        assert resp.status_code == 404

    def test_missing_roadmap_returns_200(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        client = TestClient(app)
        resp = client.get("/projects/demo/roadmap")
        assert resp.status_code == 200


class TestRoadmapPartial:
    def test_roadmap_partial(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        write_roadmap(tmp_project, mission="Ship it.", phases=[
            {"num": 1, "name": "Foundation", "timeframe": "weeks 1-2",
             "goal": "Basics", "tracks": [["BE", "API", "Alice"]], "exit": "Tests green"},
        ])
        client = TestClient(app)
        resp = client.get("/partials/demo/roadmap")
        assert resp.status_code == 200
        assert "Foundation" in resp.text
