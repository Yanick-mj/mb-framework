"""Unit tests for dashboard parsers — TDD, tests first."""
from pathlib import Path

import pytest

from scripts.dashboard import parsers
from scripts.dashboard.tests.conftest import register_projects


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
