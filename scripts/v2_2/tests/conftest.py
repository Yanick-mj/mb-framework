"""Shared pytest fixtures for v2.2 scripts.

Mirrors the conventions from scripts/v2_1/tests/conftest.py so tests across
v2.1 and v2.2 behave identically. Additional fixtures specific to v2.2
(tmp_project_with_mb_installed) support the 3-layer agent split tests.
"""
import sys
import tempfile
from pathlib import Path

import pytest

# Make `from scripts.v2_2 import ...` importable
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


@pytest.fixture
def tmp_home(monkeypatch):
    """Redirect ~ to a tmpdir so tests never touch real $HOME."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("HOME", tmpdir)
        yield Path(tmpdir)


@pytest.fixture
def tmp_project(tmp_path, monkeypatch):
    """Create a minimal mb project layout and cd into it."""
    project = tmp_path / "demo-project"
    project.mkdir()
    (project / "mb-stage.yaml").write_text("stage: pmf\nsince: 2026-04-19\n")
    (project / "memory").mkdir()
    (project / "_bmad-output").mkdir()
    (project / "agents").mkdir()
    monkeypatch.chdir(project)
    return project


@pytest.fixture
def tmp_mvp_project(tmp_path, monkeypatch):
    """tmp_project but stage=mvp — for testing stage-permissive RBAC."""
    project = tmp_path / "demo-mvp"
    project.mkdir()
    (project / "mb-stage.yaml").write_text("stage: mvp\nsince: 2026-04-19\n")
    (project / "memory").mkdir()
    (project / "_bmad-output").mkdir()
    monkeypatch.chdir(project)
    return project


@pytest.fixture
def tmp_project_with_mb_installed(tmp_path, monkeypatch):
    """tmp_project with a minimal `.claude/mb/` skeleton.

    Used by agent_loader / compose_report tests that need the framework
    layout (agents/, skills/) present. Tests can populate agents/skills
    directly after fixture setup.
    """
    project = tmp_path / "demo-project"
    project.mkdir()
    (project / "mb-stage.yaml").write_text("stage: pmf\nsince: 2026-04-19\n")
    (project / "memory").mkdir()
    (project / "_bmad-output").mkdir()

    mb_dir = project / ".claude" / "mb"
    (mb_dir / "agents").mkdir(parents=True)
    (mb_dir / "skills" / "core").mkdir(parents=True)

    monkeypatch.chdir(project)
    return project
