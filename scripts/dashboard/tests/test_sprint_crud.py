"""TDD tests for sprint CRUD — STU-P2S3.1."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_sprint, write_story


class TestCreateSprint:
    def test_creates_yaml_file(self, tmp_project):
        from scripts.dashboard.crud import create_sprint
        result = create_sprint(tmp_project, name="Sprint 1", goal="Ship it",
                               start_date="2026-05-01", end_date="2026-05-03",
                               phase="Phase 1")
        assert result["id"].startswith("sprint-")
        f = tmp_project / "_sprints" / f"{result['id']}.yaml"
        assert f.exists()
        data = yaml.safe_load(f.read_text())
        assert data["name"] == "Sprint 1"
        assert data["goal"] == "Ship it"
        assert data["status"] == "planned"

    def test_auto_increments_id(self, tmp_project):
        from scripts.dashboard.crud import create_sprint
        write_sprint(tmp_project, "sprint-1", "First", "Goal")
        write_sprint(tmp_project, "sprint-2", "Second", "Goal")
        result = create_sprint(tmp_project, name="Third", goal="Goal",
                               start_date="2026-05-07", end_date="2026-05-09",
                               phase="Phase 1")
        assert result["id"] == "sprint-3"


class TestCloseSprint:
    def test_sets_status_closed(self, tmp_project):
        from scripts.dashboard.crud import close_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        result = close_sprint(tmp_project, "sprint-1")
        assert result["status"] == "closed"
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert data["status"] == "closed"

    def test_sets_end_date_to_today(self, tmp_project):
        from scripts.dashboard.crud import close_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        result = close_sprint(tmp_project, "sprint-1")
        assert result["end_date"] is not None

    def test_returns_none_for_unknown(self, tmp_project):
        from scripts.dashboard.crud import close_sprint
        assert close_sprint(tmp_project, "nope") is None

    def test_cannot_close_already_closed(self, tmp_project):
        from scripts.dashboard.crud import close_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="closed")
        assert close_sprint(tmp_project, "sprint-1") is None


class TestAddStoryToSprint:
    def test_updates_sprint_yaml(self, tmp_project):
        from scripts.dashboard.crud import add_story_to_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=[])
        write_story(tmp_project, "S1", "todo", "Story One")
        result = add_story_to_sprint(tmp_project, "sprint-1", "S1")
        assert result is not None
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert "S1" in data["stories"]

    def test_updates_story_frontmatter(self, tmp_project):
        from scripts.dashboard.crud import add_story_to_sprint
        from scripts.dashboard.parsers import _parse_frontmatter
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=[])
        write_story(tmp_project, "S1", "todo", "Story One")
        add_story_to_sprint(tmp_project, "sprint-1", "S1")
        story_file = tmp_project / "_mb-output" / "implementation-artifacts" / "stories" / "S1.md"
        fm = _parse_frontmatter(story_file.read_text())
        assert fm.get("sprint") == "sprint-1"

    def test_no_duplicate_if_already_in_sprint(self, tmp_project):
        from scripts.dashboard.crud import add_story_to_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=["S1"])
        write_story(tmp_project, "S1", "todo", "Story One")
        add_story_to_sprint(tmp_project, "sprint-1", "S1")
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert data["stories"].count("S1") == 1

    def test_returns_none_unknown_sprint(self, tmp_project):
        from scripts.dashboard.crud import add_story_to_sprint
        write_story(tmp_project, "S1", "todo", "Story")
        assert add_story_to_sprint(tmp_project, "nope", "S1") is None


class TestRemoveStoryFromSprint:
    def test_removes_from_sprint_yaml(self, tmp_project):
        from scripts.dashboard.crud import remove_story_from_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=["S1", "S2"])
        write_story(tmp_project, "S1", "todo", "Story One")
        result = remove_story_from_sprint(tmp_project, "sprint-1", "S1")
        assert result is not None
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert "S1" not in data["stories"]
        assert "S2" in data["stories"]

    def test_clears_story_sprint_field(self, tmp_project):
        from scripts.dashboard.crud import remove_story_from_sprint
        from scripts.dashboard.parsers import _parse_frontmatter
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=["S1"])
        write_story(tmp_project, "S1", "todo", "Story One")
        # First add the sprint field
        story_file = tmp_project / "_mb-output" / "implementation-artifacts" / "stories" / "S1.md"
        text = story_file.read_text()
        text = text.replace("status: todo", "status: todo\nsprint: sprint-1")
        story_file.write_text(text)
        remove_story_from_sprint(tmp_project, "sprint-1", "S1")
        fm = _parse_frontmatter(story_file.read_text())
        assert "sprint" not in fm

    def test_returns_none_unknown_sprint(self, tmp_project):
        from scripts.dashboard.crud import remove_story_from_sprint
        assert remove_story_from_sprint(tmp_project, "nope", "S1") is None


class TestActiveSprintConstraint:
    def test_only_one_active_allowed(self, tmp_project):
        from scripts.dashboard.crud import create_sprint
        write_sprint(tmp_project, "sprint-1", "Active", "Goal", status="active")
        result = create_sprint(tmp_project, name="New", goal="Goal",
                               start_date="2026-05-04", end_date="2026-05-06",
                               phase="Phase 1", status="active")
        # Creating second active sprint should auto-close the first
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert data["status"] == "closed"
        assert result["status"] == "active"
