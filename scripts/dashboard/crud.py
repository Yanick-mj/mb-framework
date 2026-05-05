"""CRUD operations for stories with atomic writes."""
from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

import yaml

from scripts.dashboard.parsers import STORIES_SUBPATH, _parse_frontmatter


def _stories_dir(project_path: Path) -> Path:
    d = project_path / STORIES_SUBPATH
    d.mkdir(parents=True, exist_ok=True)
    return d


def _generate_story_id() -> str:
    return f"S-{uuid.uuid4().hex[:8]}"


def _atomic_write(path: Path, content: str) -> None:
    """Write atomically via temp file + rename (POSIX atomic on same FS)."""
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), suffix=".tmp", prefix=".story_"
    )
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def _build_story_content(fm: dict, body: str = "") -> str:
    """Build markdown content with frontmatter + body."""
    parts = ["---", yaml.safe_dump(fm, sort_keys=False).rstrip(), "---", ""]
    if body:
        parts += [body, ""]
    return "\n".join(parts) + "\n"


def _to_description_body(description: str) -> str:
    return f"## Description\n\n{description}" if description else ""


def create_story(
    project_path: Path,
    title: str,
    description: str = "",
    priority: str = "medium",
    status: str = "todo",
) -> dict[str, Any]:
    """Create a new story file and return its data."""
    story_id = _generate_story_id()
    d = _stories_dir(project_path)

    fm = {
        "story_id": story_id,
        "title": title,
        "status": status,
        "priority": priority,
    }

    content = _build_story_content(fm, _to_description_body(description))
    _atomic_write(d / f"{story_id}.md", content)

    return {
        "story_id": story_id,
        "title": title,
        "status": status,
        "priority": priority,
        "description": description,
    }


def _find_story_file(project_path: Path, story_id: str) -> Path | None:
    """Find a story file by story_id across all locations.

    Fast path: exact filename match. Fallback: frontmatter scan.
    """
    for directory in (_stories_dir(project_path), project_path / "_backlog"):
        exact = directory / f"{story_id}.md"
        if exact.exists():
            return exact
        if directory.exists():
            for f in directory.glob("*.md"):
                fm = _parse_frontmatter(f.read_text())
                if fm.get("story_id") == story_id:
                    return f
    return None


def _read_story(story_file: Path) -> tuple[dict, str] | None:
    """Read a story file and return (frontmatter, body) or None."""
    try:
        text = story_file.read_text()
    except FileNotFoundError:
        return None
    fm = _parse_frontmatter(text)
    if not fm:
        return None
    parts = text.split("---", 2)
    body = parts[2].strip() if len(parts) >= 3 else ""
    return fm, body


def _clean_fm(fm: dict, story_id: str) -> dict:
    """Extract only the known frontmatter fields."""
    clean = {
        "story_id": fm.get("story_id", story_id),
        "title": fm.get("title", ""),
        "status": fm.get("status", "todo"),
        "priority": fm.get("priority", "medium"),
    }
    if fm.get("labels"):
        clean["labels"] = fm["labels"]
    return clean


def update_story(
    project_path: Path,
    story_id: str,
    updates: dict[str, Any],
) -> dict[str, Any] | None:
    """Update an existing story. Returns updated data or None if not found."""
    story_file = _find_story_file(project_path, story_id)
    if not story_file:
        return None

    result = _read_story(story_file)
    if not result:
        return None
    fm, body = result

    for key in ("title", "priority", "status"):
        if key in updates:
            fm[key] = updates[key]

    if "description" in updates:
        body = _to_description_body(updates["description"])

    clean = _clean_fm(fm, story_id)
    _atomic_write(story_file, _build_story_content(clean, body))

    return {k: clean[k] for k in ("story_id", "title", "status", "priority")}


def delete_story(
    project_path: Path,
    story_id: str,
) -> dict[str, Any] | None:
    """Delete a story file. Returns its data before deletion or None if not found."""
    story_file = _find_story_file(project_path, story_id)
    if not story_file:
        return None

    result = _read_story(story_file)
    if not result:
        return None
    fm, _ = result

    story_file.unlink()

    return {
        "story_id": fm.get("story_id", story_id),
        "title": fm.get("title", ""),
        "status": fm.get("status", "unknown"),
        "priority": fm.get("priority", "medium"),
    }
