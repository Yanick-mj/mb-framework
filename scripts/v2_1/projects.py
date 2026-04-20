"""Multi-project registry stored at ~/.mb/projects.yaml.

Read/write/render helpers backing /mb:projects and the `mb` shell wrapper.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

import yaml


def registry_path() -> Path:
    """Return ~/.mb/projects.yaml path (respects $HOME override)."""
    return Path.home() / ".mb" / "projects.yaml"


def load() -> List[Dict[str, Any]]:
    """Load projects list from the registry. Returns [] if missing or malformed."""
    path = registry_path()
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return []
    projects = data.get("projects", [])
    if not isinstance(projects, list):
        return []
    return projects


def save(projects: List[Dict[str, Any]]) -> None:
    """Persist projects list to the registry. Creates ~/.mb/ if missing."""
    path = registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(
        {"version": 1, "projects": projects},
        sort_keys=False,
    ))


def add(name: str, path: str, stage: str) -> None:
    """Add or update a project entry (idempotent by name)."""
    current = load()
    current = [p for p in current if p.get("name") != name]
    current.append({"name": name, "path": path, "stage": stage})
    save(current)


def render() -> str:
    """Render a human-readable listing suitable for /mb:projects output."""
    items = load()
    if not items:
        return (
            "No mb projects registered.\n"
            "Run `bash .claude/mb/install.sh` inside a project to register it."
        )
    lines = [f"📁 {len(items)} mb project(s)", ""]
    name_w = max(len(p["name"]) for p in items)
    for p in items:
        lines.append(
            f"  {p['name']:<{name_w}}  stage:{p.get('stage', '?')}  "
            f"{p.get('path', '?')}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
