"""TDD tests for intra-column reorder — vertical drag-drop.

Cards within a column can be reordered. Order persists via sort_order
in frontmatter. Board renders cards sorted by sort_order.
"""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fastapi.testclient import TestClient
from scripts.dashboard.server import app
from scripts.dashboard.tests.conftest import register_projects, write_story


@pytest.fixture
def client(tmp_home, tmp_project):
    register_projects(tmp_home, [
        {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
    ])
    return TestClient(app)


@pytest.fixture
def stories_dir(tmp_project):
    d = tmp_project / "_bmad-output" / "implementation-artifacts" / "stories"
    d.mkdir(parents=True, exist_ok=True)
    return d


class TestReorderEndpoint:
    def test_patch_sort_order(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "A", "todo", "First")
        resp = client.patch("/api/stories/demo/A/reorder", json={"sort_order": 2})
        assert resp.status_code == 200
        assert resp.json()["sort_order"] == 2

    def test_sort_order_persisted_in_frontmatter(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "B", "todo", "Second")
        client.patch("/api/stories/demo/B/reorder", json={"sort_order": 5})
        text = (stories_dir / "B.md").read_text()
        fm_end = text.index("---", 4)
        fm = yaml.safe_load(text[4:fm_end])
        assert fm["sort_order"] == 5

    def test_preserves_other_fields(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "C", "in_progress", "Keep Me", "high")
        client.patch("/api/stories/demo/C/reorder", json={"sort_order": 1})
        text = (stories_dir / "C.md").read_text()
        fm_end = text.index("---", 4)
        fm = yaml.safe_load(text[4:fm_end])
        assert fm["title"] == "Keep Me"
        assert fm["priority"] == "high"
        assert fm["status"] == "in_progress"

    def test_not_found_returns_404(self, client, tmp_project):
        resp = client.patch("/api/stories/demo/NOPE/reorder", json={"sort_order": 1})
        assert resp.status_code == 404

    def test_unknown_project_returns_404(self, client):
        resp = client.patch("/api/stories/unknown/X/reorder", json={"sort_order": 1})
        assert resp.status_code == 404


class TestBoardSortOrder:
    def test_board_renders_cards_sorted_by_sort_order(self, client, tmp_project, stories_dir):
        """Card with sort_order=1 appears before sort_order=2 in HTML."""
        write_story(tmp_project, "Z", "todo", "Should be second")
        write_story(tmp_project, "A", "todo", "Should be first")
        # Set sort_order: A=1, Z=2
        client.patch("/api/stories/demo/A/reorder", json={"sort_order": 1})
        client.patch("/api/stories/demo/Z/reorder", json={"sort_order": 2})
        resp = client.get("/partials/demo/board")
        text = resp.text
        pos_a = text.index('data-story-id="A"')
        pos_z = text.index('data-story-id="Z"')
        assert pos_a < pos_z, "A (sort_order=1) should appear before Z (sort_order=2)"

    def test_cards_without_sort_order_come_after_sorted(self, client, tmp_project, stories_dir):
        """Cards with no sort_order default to end."""
        write_story(tmp_project, "SORTED", "todo", "Has order")
        write_story(tmp_project, "UNSORTED", "todo", "No order")
        client.patch("/api/stories/demo/SORTED/reorder", json={"sort_order": 1})
        resp = client.get("/partials/demo/board")
        text = resp.text
        pos_sorted = text.index('data-story-id="SORTED"')
        pos_unsorted = text.index('data-story-id="UNSORTED"')
        assert pos_sorted < pos_unsorted
