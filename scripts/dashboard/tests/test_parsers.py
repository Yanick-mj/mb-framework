"""Unit tests for dashboard parsers — TDD, tests first."""
from pathlib import Path

import pytest

from scripts.dashboard import parsers
from scripts.dashboard.tests.conftest import (
    register_projects, write_story, write_backlog_story, write_runs, write_roadmap,
)


class TestProjectContext:
    def test_overrides_project_root(self, tmp_project):
        target = Path("/tmp/fake-project")
        with parsers.project_context(target):
            from scripts.v2_2 import _paths
            assert _paths.project_root() == target

    def test_restores_after_exit(self, tmp_project):
        from scripts.v2_2 import _paths
        original = _paths.project_root()
        with parsers.project_context(Path("/tmp/other")):
            pass
        assert _paths.project_root() == original

    def test_restores_on_exception(self, tmp_project):
        from scripts.v2_2 import _paths
        original = _paths.project_root()
        with pytest.raises(ValueError):
            with parsers.project_context(Path("/tmp/other")):
                raise ValueError("boom")
        assert _paths.project_root() == original


class TestLoadProjects:
    def test_returns_empty_when_no_registry(self, tmp_home):
        assert parsers.load_projects() == []

    def test_returns_project_list(self, tmp_home):
        register_projects(tmp_home, [
            {"name": "demo", "path": "/tmp/demo", "stage": "mvp"},
        ])
        result = parsers.load_projects()
        assert len(result) == 1
        assert result[0]["name"] == "demo"


class TestGetStageData:
    def test_reads_stage_yaml(self, tmp_project):
        result = parsers.get_stage_data(tmp_project)
        assert result["stage"] == "mvp"
        assert result["since"] == "2026-04-19"

    def test_missing_file_returns_unknown(self, tmp_path):
        result = parsers.get_stage_data(tmp_path)
        assert result["stage"] == "unknown"
        assert result["since"] is None


class TestGetStoryStats:
    def test_counts_by_status(self, tmp_project):
        write_story(tmp_project, "S1", "todo")
        write_story(tmp_project, "S2", "todo")
        write_story(tmp_project, "S3", "in_progress")
        write_story(tmp_project, "S4", "done")
        result = parsers.get_story_stats(tmp_project)
        assert result["total"] == 4
        assert result["todo"] == 2
        assert result["in_progress"] == 1
        assert result["done"] == 1
        assert result["backlog"] == 0

    def test_empty_project(self, tmp_project):
        result = parsers.get_story_stats(tmp_project)
        assert result["total"] == 0


class TestGetBoardData:
    def test_returns_enriched_stories_by_column(self, tmp_project):
        write_story(tmp_project, "S1", "todo", "My Title", "high", ["frontend"])
        result = parsers.get_board_data(tmp_project)
        assert "todo" in result
        assert len(result["todo"]) == 1
        card = result["todo"][0]
        assert card["story_id"] == "S1"
        assert card["title"] == "My Title"
        assert card["priority"] == "high"
        assert card["labels"] == ["frontend"]

    def test_includes_backlog_dir_stories(self, tmp_project):
        write_backlog_story(tmp_project, "B1", "backlog", "Backlog Item")
        result = parsers.get_board_data(tmp_project)
        assert len(result["backlog"]) == 1
        assert result["backlog"][0]["story_id"] == "B1"

    def test_empty_project_returns_empty_columns(self, tmp_project):
        result = parsers.get_board_data(tmp_project)
        for col in ["backlog", "todo", "in_progress", "in_review", "done"]:
            assert result[col] == []

    def test_stories_without_labels_get_empty_list(self, tmp_project):
        write_story(tmp_project, "S1", "todo", "No Labels")
        card = parsers.get_board_data(tmp_project)["todo"][0]
        assert card["labels"] == []


class TestGetRecentRuns:
    def test_returns_runs_newest_first(self, tmp_project):
        write_runs(tmp_project, count=3)
        result = parsers.get_recent_runs(tmp_project, limit=2)
        assert len(result) == 2
        assert result[0]["run_id"] == "run002"

    def test_empty_project_returns_empty(self, tmp_project):
        result = parsers.get_recent_runs(tmp_project)
        assert result == []


class TestGetStoryDetail:
    def test_returns_full_story(self, tmp_project):
        write_story(tmp_project, "S1", "todo", "Build Widget", "high")
        result = parsers.get_story_detail(tmp_project, "S1")
        assert result is not None
        assert result["story_id"] == "S1"
        assert result["title"] == "Build Widget"
        assert result["priority"] == "high"
        assert result["status"] == "todo"
        assert "why" in result["sections"]
        assert "scope" in result["sections"]
        assert "acceptance_criteria" in result["sections"]

    def test_acceptance_criteria_parsed(self, tmp_project):
        write_story(tmp_project, "S1", "todo")
        result = parsers.get_story_detail(tmp_project, "S1")
        ac = result["sections"]["acceptance_criteria"]
        assert len(ac) == 2
        assert ac[0]["done"] is False
        assert ac[1]["done"] is True

    def test_missing_story_returns_none(self, tmp_project):
        result = parsers.get_story_detail(tmp_project, "NOPE")
        assert result is None

    def test_finds_story_in_backlog(self, tmp_project):
        write_backlog_story(tmp_project, "B1", "backlog", "Backlog Thing")
        result = parsers.get_story_detail(tmp_project, "B1")
        assert result is not None
        assert result["story_id"] == "B1"


class TestGetInboxData:
    def test_counts_actionable_items(self, tmp_project):
        write_story(tmp_project, "S1", "in_review")
        write_story(tmp_project, "S2", "blocked")
        write_story(tmp_project, "S3", "done")
        result = parsers.get_inbox_data(tmp_project)
        assert result["total"] == 2
        assert len(result["in_review"]) == 1
        assert len(result["blocked"]) == 1
        assert len(result["approvals"]) == 0

    def test_empty_inbox(self, tmp_project):
        result = parsers.get_inbox_data(tmp_project)
        assert result["total"] == 0


class TestGetRoadmapData:
    def test_parses_mission(self, tmp_project):
        write_roadmap(tmp_project, mission="Build the best thing ever.")
        result = parsers.get_roadmap_data(tmp_project)
        assert result["mission"] == "Build the best thing ever."

    def test_parses_phases(self, tmp_project):
        write_roadmap(tmp_project, mission="Ship it.", phases=[
            {
                "num": 1, "name": "Foundation", "timeframe": "weeks 1-2",
                "goal": "Get the basics working",
                "tracks": [["Backend", "API endpoints", "Alice"], ["Frontend", "UI components", "Bob"]],
                "exit": "All tests green",
            },
            {
                "num": 2, "name": "Polish", "timeframe": "weeks 3-4",
                "goal": "Make it beautiful",
                "tracks": [["Design", "Visual polish", "Carol"]],
                "exit": "User approval",
            },
        ])
        result = parsers.get_roadmap_data(tmp_project)
        assert len(result["phases"]) == 2
        p1 = result["phases"][0]
        assert p1["name"] == "Foundation"
        assert p1["goal"] == "Get the basics working"
        assert len(p1["tracks"]) == 2
        assert p1["tracks"][0] == {"track": "Backend", "work": "API endpoints", "owner": "Alice"}
        assert p1["exit"] == "All tests green"
        assert p1["current"] is True
        p2 = result["phases"][1]
        assert p2["current"] is False

    def test_missing_roadmap_returns_empty(self, tmp_project):
        result = parsers.get_roadmap_data(tmp_project)
        assert result["mission"] == ""
        assert result["phases"] == []
        assert result["raw"] == ""

    def test_fallback_raw_for_non_standard_format(self, tmp_project):
        (tmp_project / "_roadmap.md").write_text("# My Custom Roadmap\n\nJust some freeform text.\n")
        result = parsers.get_roadmap_data(tmp_project)
        assert result["mission"] == ""
        assert result["phases"] == []
        assert "freeform text" in result["raw"]
