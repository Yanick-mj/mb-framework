"""Shared pytest fixtures for v2.1 scripts."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Prepend the scripts/ parent to sys.path so `from scripts.v2_1 import ...` works
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


@pytest.fixture
def tmp_home(monkeypatch):
    """Redirect ~/.mb/ to a tmpdir so tests never touch real $HOME."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("HOME", tmpdir)
        yield Path(tmpdir)


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal mb project layout and cd into it."""
    project = tmp_path / "demo-project"
    project.mkdir()
    (project / "mb-stage.yaml").write_text("stage: mvp\nsince: 2026-04-19\n")
    (project / "memory").mkdir()
    (project / "_bmad-output").mkdir()
    os.chdir(project)
    return project
