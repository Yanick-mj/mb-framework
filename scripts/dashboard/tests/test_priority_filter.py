"""TDD tests for priority filter on board."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_story


class TestBoardFilterPartial:
    def test_no_filter_returns_all(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "H1", "todo", "High", "high")
        write_story(tmp_project, "L1", "todo", "Low", "low")
        resp = client.get("/partials/demo/board")
        assert "H1" in resp.text
        assert "L1" in resp.text

    def test_filter_high_shows_only_high(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "H1", "todo", "High", "high")
        write_story(tmp_project, "L1", "todo", "Low", "low")
        resp = client.get("/partials/demo/board?priority=high")
        assert resp.status_code == 200
        assert "H1" in resp.text
        assert "L1" not in resp.text

    def test_filter_critical_shows_only_critical(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "C1", "todo", "Critical", "critical")
        write_story(tmp_project, "M1", "todo", "Medium", "medium")
        resp = client.get("/partials/demo/board?priority=critical")
        assert "C1" in resp.text
        assert "M1" not in resp.text

    def test_filter_medium_across_columns(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "M1", "todo", "Med Todo", "medium")
        write_story(tmp_project, "M2", "in_progress", "Med IP", "medium")
        write_story(tmp_project, "H1", "todo", "High Todo", "high")
        resp = client.get("/partials/demo/board?priority=medium")
        assert "M1" in resp.text
        assert "M2" in resp.text
        assert "H1" not in resp.text

    def test_filter_no_match_returns_empty_columns(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "L1", "todo", "Low", "low")
        resp = client.get("/partials/demo/board?priority=critical")
        assert resp.status_code == 200
        assert "L1" not in resp.text


class TestBoardPageFilter:
    def test_board_page_has_filter_buttons(self, client, tmp_project, stories_dir):
        resp = client.get("/projects/demo/board")
        assert resp.status_code == 200
        assert "priority" in resp.text.lower()
        # Should have filter options
        assert "critical" in resp.text.lower()
        assert "high" in resp.text.lower()

    def test_board_page_with_priority_param(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "H1", "todo", "High", "high")
        write_story(tmp_project, "L1", "todo", "Low", "low")
        resp = client.get("/projects/demo/board?priority=high")
        assert resp.status_code == 200
        assert "H1" in resp.text
        assert "L1" not in resp.text
