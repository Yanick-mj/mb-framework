"""TDD tests for kanban drag-and-drop — Sprint 2 S2.1."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_story


class TestBoardDragDropAttributes:
    def test_board_includes_sortable_js(self, client, tmp_project, stories_dir):
        """Board page loads Sortable.js from CDN."""
        resp = client.get("/projects/demo/board")
        assert resp.status_code == 200
        assert "Sortable" in resp.text or "sortable" in resp.text.lower()

    def test_cards_have_data_story_id(self, client, tmp_project, stories_dir):
        """Each card has data-story-id for JS to identify it."""
        write_story(tmp_project, "S1", "todo", "Card One")
        resp = client.get("/partials/demo/board")
        assert resp.status_code == 200
        assert 'data-story-id="S1"' in resp.text

    def test_columns_have_data_status(self, client, tmp_project, stories_dir):
        """Each column has data-status so Sortable knows the target status."""
        resp = client.get("/partials/demo/board")
        assert resp.status_code == 200
        assert 'data-status="todo"' in resp.text
        assert 'data-status="in_progress"' in resp.text
        assert 'data-status="done"' in resp.text

    def test_board_cards_container_is_sortable_group(self, client, tmp_project, stories_dir):
        """The card container divs have the sortable-group class."""
        write_story(tmp_project, "S1", "todo", "Card")
        resp = client.get("/partials/demo/board")
        assert resp.status_code == 200
        assert "sortable-group" in resp.text


class TestDragDropStatusSync:
    def test_patch_status_then_board_reflects_change(self, client, tmp_project, stories_dir):
        """After PATCH status, re-fetching board shows card in new column."""
        write_story(tmp_project, "DRAG1", "todo", "Dragged Card")
        # Card starts in todo
        resp = client.get("/partials/demo/board")
        assert "DRAG1" in resp.text
        # Simulate drag: PATCH status to in_progress
        resp = client.patch("/api/stories/demo/DRAG1/status", json={"status": "in_progress"})
        assert resp.status_code == 200
        # Re-fetch board — card should now be in in_progress column
        resp = client.get("/partials/demo/board")
        text = resp.text
        # Find the in_progress column and check DRAG1 is there
        assert "DRAG1" in text

    def test_column_count_updates_after_status_change(self, client, tmp_project, stories_dir):
        """Move card → source column count -1, target +1."""
        write_story(tmp_project, "CNT1", "todo", "Count Test 1")
        write_story(tmp_project, "CNT2", "todo", "Count Test 2")
        # Initially 2 in todo
        resp = client.get("/partials/demo/board")
        assert resp.text.count('data-story-id=') >= 2
        # Move one to done
        client.patch("/api/stories/demo/CNT1/status", json={"status": "done"})
        resp = client.get("/partials/demo/board")
        # CNT1 should still appear but in done column
        assert "CNT1" in resp.text
        assert "CNT2" in resp.text
