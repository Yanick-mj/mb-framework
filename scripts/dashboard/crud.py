"""CRUD operations for stories with atomic writes and file locking."""
from __future__ import annotations

import fcntl
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

import yaml

from scripts.dashboard.parsers import _parse_frontmatter


def _stories_dir(project_path: Path) -> Path:
    d = project_path / "_bmad-output" / "implementation-artifacts" / "stories"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _generate_story_id() -> str:
    return f"S-{uuid.uuid4().hex[:8]}"


def _atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically using temp file + rename."""
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), suffix=".tmp", prefix=".story_"
    )
    try:
        with os.fdopen(fd, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)
        os.rename(tmp_path, str(path))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _build_story_content(fm: dict, description: str = "") -> str:
    """Build markdown content with frontmatter + body."""
    lines = ["---"]
    lines.append(yaml.safe_dump(fm, sort_keys=False).rstrip())
    lines.append("---")
    lines.append("")
    if description:
        lines.append("## Description")
        lines.append("")
        lines.append(description)
        lines.append("")
    return "\n".join(lines) + "\n"


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

    content = _build_story_content(fm, description)
    _atomic_write(d / f"{story_id}.md", content)

    return {
        "story_id": story_id,
        "title": title,
        "status": status,
        "priority": priority,
        "description": description,
    }


def _find_story_file(project_path: Path, story_id: str) -> Path | None:
    """Find a story file by story_id across all locations."""
    # Check stories dir (exact match first)
    d = _stories_dir(project_path)
    exact = d / f"{story_id}.md"
    if exact.exists():
        return exact
    # Scan stories dir for matching frontmatter
    for f in d.glob("*.md"):
        fm = _parse_frontmatter(f.read_text())
        if fm.get("story_id") == story_id:
            return f
    # Check backlog dir
    backlog = project_path / "_backlog"
    if backlog.exists():
        for f in backlog.glob("*.md"):
            fm = _parse_frontmatter(f.read_text())
            if fm.get("story_id") == story_id:
                return f
    return None


def update_story(
    project_path: Path,
    story_id: str,
    updates: dict[str, Any],
) -> dict[str, Any] | None:
    """Update an existing story. Returns updated data or None if not found."""
    story_file = _find_story_file(project_path, story_id)

    if not story_file:
        return None

    text = story_file.read_text()
    fm = _parse_frontmatter(text)
    if not fm:
        return None

    # Extract body (everything after frontmatter)
    body = ""
    parts = text.split("---", 2)
    if len(parts) >= 3:
        body = parts[2].strip()

    # Apply updates to frontmatter fields
    for key in ("title", "priority", "status"):
        if key in updates:
            fm[key] = updates[key]

    # Handle description update
    if "description" in updates:
        body = f"## Description\n\n{updates['description']}"

    # Rebuild content
    lines = ["---"]
    # Only keep known fields in frontmatter
    clean_fm = {
        "story_id": fm.get("story_id", story_id),
        "title": fm.get("title", ""),
        "status": fm.get("status", "todo"),
        "priority": fm.get("priority", "medium"),
    }
    if fm.get("labels"):
        clean_fm["labels"] = fm["labels"]
    lines.append(yaml.safe_dump(clean_fm, sort_keys=False).rstrip())
    lines.append("---")
    lines.append("")
    if body:
        lines.append(body)
        lines.append("")

    content = "\n".join(lines) + "\n"
    _atomic_write(story_file, content)

    return {
        "story_id": clean_fm["story_id"],
        "title": clean_fm["title"],
        "status": clean_fm["status"],
        "priority": clean_fm["priority"],
    }


def delete_story(
    project_path: Path,
    story_id: str,
) -> dict[str, Any] | None:
    """Delete a story file. Returns its data before deletion or None if not found."""
    story_file = _find_story_file(project_path, story_id)

    if not story_file:
        return None

    text = story_file.read_text()
    fm = _parse_frontmatter(text)

    story_file.unlink()

    return {
        "story_id": fm.get("story_id", story_id),
        "title": fm.get("title", ""),
        "status": fm.get("status", "unknown"),
        "priority": fm.get("priority", "medium"),
    }
