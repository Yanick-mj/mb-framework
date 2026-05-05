"""Data layer for the dashboard — wraps existing v2.1/v2.2 parsers.

All functions return plain dicts/lists. No FastAPI dependency.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

import re

import yaml

from scripts.v2_2 import _paths

_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)


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


def _parse_frontmatter(text: str) -> dict:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _scan_all_stories(path: Path) -> list[dict]:
    """Scan both _bmad-output stories and _backlog for story files."""
    stories = []
    stories_dir = path / "_bmad-output" / "implementation-artifacts" / "stories"
    if stories_dir.exists():
        for f in sorted(stories_dir.glob("*.md")):
            fm = _parse_frontmatter(f.read_text())
            if fm:
                fm.setdefault("labels", [])
                fm["_path"] = str(f)
                stories.append(fm)
    backlog_dir = path / "_backlog"
    if backlog_dir.exists():
        for f in sorted(backlog_dir.glob("*.md")):
            fm = _parse_frontmatter(f.read_text())
            if fm and fm.get("story_id"):
                fm.setdefault("labels", [])
                fm["_path"] = str(f)
                stories.append(fm)
    return stories


def get_board_data(path: Path) -> dict[str, list[dict]]:
    """Group stories into kanban columns with enriched card data."""
    from scripts.v2_2.board import COLUMNS
    groups: dict[str, list[dict]] = {c: [] for c in COLUMNS}
    for story in _scan_all_stories(path):
        status = story.get("status")
        if status in groups:
            groups[status].append({
                "story_id": story.get("story_id", "?"),
                "title": story.get("title", ""),
                "status": status,
                "priority": story.get("priority", "medium"),
                "labels": story.get("labels") or [],
            })
    return groups
