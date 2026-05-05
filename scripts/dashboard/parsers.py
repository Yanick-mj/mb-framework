"""Data layer for the dashboard — wraps existing v2.1/v2.2 parsers.

All functions return plain dicts/lists. No FastAPI dependency.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

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
