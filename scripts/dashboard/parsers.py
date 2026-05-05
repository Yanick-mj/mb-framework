"""Data layer for the dashboard — wraps existing v2.1/v2.2 parsers.

All functions return plain dicts/lists. No FastAPI dependency.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml

from scripts.v2_2 import _paths


@contextmanager
def project_context(path: Path):
    """Temporarily override _paths.project_root() to point at `path`."""
    original = _paths.project_root

    _paths.project_root = lambda: path
    try:
        yield
    finally:
        _paths.project_root = original


def load_projects() -> list[dict[str, Any]]:
    """Load registered projects from ~/.mb/projects.yaml."""
    from scripts.v2_1 import projects
    return projects.load()


def get_stage_data(path: Path) -> dict[str, Any]:
    """Read mb-stage.yaml from project root."""
    stage_file = path / "mb-stage.yaml"
    if not stage_file.exists():
        return {"stage": "unknown", "since": None}
    try:
        data = yaml.safe_load(stage_file.read_text()) or {}
    except yaml.YAMLError:
        return {"stage": "unknown", "since": None}
    return {
        "stage": data.get("stage", "unknown"),
        "since": str(data["since"]) if "since" in data else None,
    }


def get_story_stats(path: Path) -> dict[str, int]:
    """Count stories by status using board._group_by_status()."""
    from scripts.v2_2 import board
    with project_context(path):
        groups = board._group_by_status()
    result = {col: len(stories) for col, stories in groups.items()}
    result["total"] = sum(result.values())
    return result
