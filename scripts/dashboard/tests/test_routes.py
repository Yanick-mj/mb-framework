"""Integration tests for dashboard routes via FastAPI TestClient."""
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
