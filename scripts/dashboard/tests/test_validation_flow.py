"""TDD tests for validation flow — Sprint 2 S2.3."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_story


class TestValidationButtons:
    def test_approve_button_shown_for_in_review(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "V1", "in_review", "Review Me")
        resp = client.get("/partials/demo/story/V1")
        assert resp.status_code == 200
        assert "Approve" in resp.text

    def test_request_changes_button_shown_for_in_review(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "V2", "in_review", "Review Me")
        resp = client.get("/partials/demo/story/V2")
        assert resp.status_code == 200
        assert "Request Changes" in resp.text or "Request changes" in resp.text

    def test_buttons_hidden_for_todo(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "V3", "todo", "Not In Review")
        resp = client.get("/partials/demo/story/V3")
        assert resp.status_code == 200
        assert "Approve" not in resp.text

    def test_buttons_hidden_for_done(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "V4", "done", "Already Done")
        resp = client.get("/partials/demo/story/V4")
        assert resp.status_code == 200
        assert "Approve" not in resp.text


class TestCommentEndpoint:
    def test_post_comment_appends_to_story(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "C1", "in_review", "Comment Test")
        resp = client.post("/api/stories/demo/C1/comment", json={
            "text": "Needs more error handling",
        })
        assert resp.status_code == 200
        text = (stories_dir / "C1.md").read_text()
        assert "## Review" in text
        assert "Needs more error handling" in text

    def test_comment_on_missing_story_returns_404(self, client, tmp_project):
        resp = client.post("/api/stories/demo/NOPE/comment", json={
            "text": "Hello",
        })
        assert resp.status_code == 404

    def test_empty_comment_returns_422(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "C2", "in_review", "Story")
        resp = client.post("/api/stories/demo/C2/comment", json={
            "text": "",
        })
        assert resp.status_code == 422

    def test_comment_preserves_frontmatter(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "C3", "in_review", "Keep FM", "high")
        client.post("/api/stories/demo/C3/comment", json={
            "text": "Review note",
        })
        text = (stories_dir / "C3.md").read_text()
        fm_end = text.index("---", 4)
        fm = yaml.safe_load(text[4:fm_end])
        assert fm["title"] == "Keep FM"
        assert fm["priority"] == "high"


class TestApproveFlow:
    def test_approve_sets_status_to_done(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "A1", "in_review", "Approve Me")
        resp = client.patch("/api/stories/demo/A1/status", json={"status": "done"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

    def test_request_changes_sets_in_progress(self, client, tmp_project, stories_dir):
        write_story(tmp_project, "A2", "in_review", "Needs Work")
        resp = client.patch("/api/stories/demo/A2/status", json={"status": "in_progress"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"
