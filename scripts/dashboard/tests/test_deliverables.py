"""TDD tests for deliverable viewer — Sprint 2 S2.4."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_story


def _write_deliverable(tmp_project: Path, story_id: str, filename: str, content: str) -> Path:
    """Write a deliverable file for a story."""
    d = tmp_project / "_bmad-output" / "deliverables" / story_id
    d.mkdir(parents=True, exist_ok=True)
    f = d / filename
    f.write_text(content)
    return f


class TestDeliverablesList:
    def test_returns_list_of_files(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S1", "in_review", "Story One")
        _write_deliverable(tmp_project, "S1", "PLAN-rev1.md", "# Plan\nDo stuff.")
        _write_deliverable(tmp_project, "S1", "IMPL-rev1.md", "# Impl\nCode here.")
        resp = client.get("/api/stories/demo/S1/deliverables")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        filenames = [d["filename"] for d in data]
        assert "PLAN-rev1.md" in filenames
        assert "IMPL-rev1.md" in filenames

    def test_empty_list_when_no_deliverables(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S2", "todo", "No Deliverables")
        resp = client.get("/api/stories/demo/S2/deliverables")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_404_unknown_project(self, client):
        resp = client.get("/api/stories/unknown/S1/deliverables")
        assert resp.status_code == 404

    def test_404_unknown_story(self, client, tmp_project, stories_dir):
        resp = client.get("/api/stories/demo/NOPE/deliverables")
        assert resp.status_code == 404


class TestDeliverableContent:
    def test_renders_markdown_as_html(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S1", "in_review", "Story")
        _write_deliverable(tmp_project, "S1", "PLAN-rev1.md", "# Plan\n\nSome **bold** text.")
        resp = client.get("/api/stories/demo/S1/deliverables/PLAN-rev1.md")
        assert resp.status_code == 200
        data = resp.json()
        assert "<h1>" in data["html"] or "<strong>" in data["html"]
        assert "bold" in data["html"]

    def test_404_missing_file(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S1", "in_review", "Story")
        resp = client.get("/api/stories/demo/S1/deliverables/NOPE.md")
        assert resp.status_code == 404

    def test_returns_raw_content(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S1", "in_review", "Story")
        _write_deliverable(tmp_project, "S1", "PLAN-rev1.md", "# Raw Plan")
        resp = client.get("/api/stories/demo/S1/deliverables/PLAN-rev1.md")
        assert resp.status_code == 200
        assert resp.json()["raw"] == "# Raw Plan"


class TestStoryModalDeliverables:
    def test_modal_has_deliverables_tab(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S1", "in_review", "Story With Deliverables")
        _write_deliverable(tmp_project, "S1", "PLAN-rev1.md", "# Plan")
        resp = client.get("/partials/demo/story/S1")
        assert resp.status_code == 200
        assert "Deliverables" in resp.text or "deliverables" in resp.text.lower()

    def test_modal_shows_empty_state_when_no_deliverables(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "S2", "todo", "No Deliverables")
        resp = client.get("/partials/demo/story/S2")
        assert resp.status_code == 200
