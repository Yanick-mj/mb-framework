"""TDD tests for sprint data model — STU-P2S3.1."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_sprint, write_story


class TestLoadSprints:
    def test_returns_empty_list_when_no_sprints(self, tmp_project):
        from scripts.dashboard.parsers import load_sprints
        assert load_sprints(tmp_project) == []

    def test_returns_sprints_sorted_by_start_date(self, tmp_project):
        from scripts.dashboard.parsers import load_sprints
        write_sprint(tmp_project, "sprint-2", "Second", "Goal B",
                     start_date="2026-05-04")
        write_sprint(tmp_project, "sprint-1", "First", "Goal A",
                     start_date="2026-05-01")
        result = load_sprints(tmp_project)
        assert len(result) == 2
        assert result[0]["id"] == "sprint-1"
        assert result[1]["id"] == "sprint-2"

    def test_sprint_has_all_fields(self, tmp_project):
        from scripts.dashboard.parsers import load_sprints
        write_sprint(tmp_project, "sprint-1", "My Sprint", "Build things",
                     status="active", phase="Phase 2",
                     start_date="2026-05-01", end_date="2026-05-03",
                     stories=["S1", "S2"])
        result = load_sprints(tmp_project)
        s = result[0]
        assert s["id"] == "sprint-1"
        assert s["name"] == "My Sprint"
        assert s["goal"] == "Build things"
        assert s["status"] == "active"
        assert s["phase"] == "Phase 2"
        assert s["stories"] == ["S1", "S2"]

    def test_ignores_non_yaml_files(self, tmp_project):
        from scripts.dashboard.parsers import load_sprints
        d = tmp_project / "_sprints"
        d.mkdir(parents=True, exist_ok=True)
        (d / "README.md").write_text("# Sprints")
        write_sprint(tmp_project, "sprint-1", "Real", "Goal")
        result = load_sprints(tmp_project)
        assert len(result) == 1

    def test_ignores_malformed_yaml(self, tmp_project):
        from scripts.dashboard.parsers import load_sprints
        d = tmp_project / "_sprints"
        d.mkdir(parents=True, exist_ok=True)
        (d / "bad.yaml").write_text(":::: not valid yaml {{{")
        write_sprint(tmp_project, "sprint-1", "Good", "Goal")
        result = load_sprints(tmp_project)
        assert len(result) == 1


class TestGetSprint:
    def test_returns_sprint_by_id(self, tmp_project):
        from scripts.dashboard.parsers import get_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint One", "Goal")
        result = get_sprint(tmp_project, "sprint-1")
        assert result is not None
        assert result["id"] == "sprint-1"
        assert result["name"] == "Sprint One"

    def test_returns_none_for_unknown_id(self, tmp_project):
        from scripts.dashboard.parsers import get_sprint
        assert get_sprint(tmp_project, "nope") is None

    def test_resolves_story_objects(self, tmp_project):
        from scripts.dashboard.parsers import get_sprint
        write_story(tmp_project, "S1", "done", "Story One", "high")
        write_story(tmp_project, "S2", "todo", "Story Two", "medium")
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     stories=["S1", "S2"])
        result = get_sprint(tmp_project, "sprint-1")
        resolved = result["resolved_stories"]
        assert len(resolved) == 2
        assert resolved[0]["story_id"] == "S1"
        assert resolved[0]["title"] == "Story One"
        assert resolved[0]["status"] == "done"

    def test_unresolved_stories_included_as_stubs(self, tmp_project):
        from scripts.dashboard.parsers import get_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     stories=["MISSING"])
        result = get_sprint(tmp_project, "sprint-1")
        resolved = result["resolved_stories"]
        assert len(resolved) == 1
        assert resolved[0]["story_id"] == "MISSING"
        assert resolved[0]["status"] == "unknown"


class TestGetSprintsData:
    def test_returns_sprints_with_completion(self, tmp_project):
        from scripts.dashboard.parsers import get_sprints_data
        write_story(tmp_project, "S1", "done", "Done")
        write_story(tmp_project, "S2", "todo", "Todo")
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     status="active", stories=["S1", "S2"])
        result = get_sprints_data(tmp_project)
        assert len(result) == 1
        s = result[0]
        assert s["done_count"] == 1
        assert s["total_count"] == 2
        assert s["pct"] == 50

    def test_active_sprint_first(self, tmp_project):
        from scripts.dashboard.parsers import get_sprints_data
        write_sprint(tmp_project, "sprint-1", "Old", "Goal",
                     status="closed", start_date="2026-05-01")
        write_sprint(tmp_project, "sprint-2", "Active", "Goal",
                     status="active", start_date="2026-05-04")
        write_sprint(tmp_project, "sprint-3", "New", "Goal",
                     status="planned", start_date="2026-05-07")
        result = get_sprints_data(tmp_project)
        assert result[0]["status"] == "active"

    def test_empty_sprint_zero_pct(self, tmp_project):
        from scripts.dashboard.parsers import get_sprints_data
        write_sprint(tmp_project, "sprint-1", "Empty", "Goal")
        result = get_sprints_data(tmp_project)
        assert result[0]["pct"] == 0
        assert result[0]["total_count"] == 0
