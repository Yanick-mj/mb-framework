"""Unit tests for dashboard parsers — TDD, tests first."""
from pathlib import Path

import pytest

from scripts.dashboard import parsers
from scripts.dashboard.tests.conftest import (
    register_projects, write_story, write_backlog_story,
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
