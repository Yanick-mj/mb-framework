"""CRUD operations for stories with atomic writes."""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scripts.dashboard.parsers import RUNS_LOG_SUBPATH, SPRINTS_SUBPATH, _parse_frontmatter, load_sprints
from scripts.v2_2._paths import stories_root_for

_SUMMARY_KEYS = ("story_id", "title", "status", "priority")


def _stories_dir(project_path: Path) -> Path:
    d = stories_root_for(project_path)
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
    if "sort_order" in fm:
        clean["sort_order"] = fm["sort_order"]
    return clean


def _story_summary(clean: dict) -> dict[str, Any]:
    """Standard return dict from a cleaned frontmatter."""
    return {k: clean[k] for k in _SUMMARY_KEYS}


def _mutate_story(
    project_path: Path,
    story_id: str,
    mutator: Callable[[dict, str], tuple[dict, str]],
) -> tuple[dict, Path] | None:
    """Find, read, mutate, and write a story. Returns (clean_fm, file_path) or None.

    The mutator receives (frontmatter_dict, body_str) and must return (fm, body).
    """
    story_file = _find_story_file(project_path, story_id)
    if not story_file:
        return None

    result = _read_story(story_file)
    if not result:
        return None
    fm, body = result

    fm, body = mutator(fm, body)

    clean = _clean_fm(fm, story_id)
    _atomic_write(story_file, _build_story_content(clean, body))
    return clean, story_file


# --- Public API ---


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


def update_story(
    project_path: Path,
    story_id: str,
    updates: dict[str, Any],
) -> dict[str, Any] | None:
    """Update an existing story. Returns updated data or None if not found."""
    def mutator(fm: dict, body: str) -> tuple[dict, str]:
        for key in ("title", "priority", "status"):
            if key in updates:
                fm[key] = updates[key]
        if "description" in updates:
            body = _to_description_body(updates["description"])
        return fm, body

    result = _mutate_story(project_path, story_id, mutator)
    if not result:
        return None
    return _story_summary(result[0])


def patch_status(
    project_path: Path,
    story_id: str,
    new_status: str,
) -> dict[str, Any] | None:
    """Update only the status field of a story. Returns updated data or None."""
    old_status = None

    def mutator(fm: dict, body: str) -> tuple[dict, str]:
        nonlocal old_status
        old_status = fm.get("status", "unknown")
        fm["status"] = new_status
        return fm, body

    result = _mutate_story(project_path, story_id, mutator)
    if not result:
        return None
    _log_status_change(project_path, story_id, old_status, new_status)
    return _story_summary(result[0])


def reorder_story(
    project_path: Path,
    story_id: str,
    sort_order: int,
) -> dict[str, Any] | None:
    """Set sort_order on a story for intra-column ordering."""
    def mutator(fm: dict, body: str) -> tuple[dict, str]:
        fm["sort_order"] = sort_order
        return fm, body

    result = _mutate_story(project_path, story_id, mutator)
    if not result:
        return None
    summary = _story_summary(result[0])
    summary["sort_order"] = sort_order
    return summary


def add_comment(
    project_path: Path,
    story_id: str,
    text: str,
) -> dict[str, Any] | None:
    """Append a review comment to a story's body. Returns story data or None."""
    def mutator(fm: dict, body: str) -> tuple[dict, str]:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        body += f"\n\n## Review — {date_str}\n\n{text}"
        return fm, body

    result = _mutate_story(project_path, story_id, mutator)
    if not result:
        return None
    return _story_summary(result[0])


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


def _log_status_change(
    project_path: Path, story_id: str, from_status: str, to_status: str
) -> None:
    """Append a status_change entry to runs.jsonl."""
    log_file = project_path / RUNS_LOG_SUBPATH
    log_file.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "action": "status_change",
        "story": story_id,
        "from_status": from_status,
        "to_status": to_status,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    with log_file.open("a") as f:
        f.write(json.dumps(entry) + "\n")


# --- Sprint CRUD ---


def _sprints_dir(project_path: Path) -> Path:
    d = project_path / SPRINTS_SUBPATH
    d.mkdir(parents=True, exist_ok=True)
    return d


def _next_sprint_id(project_path: Path) -> str:
    """Generate sprint-{max+1} ID."""
    existing = load_sprints(project_path)
    nums = []
    for s in existing:
        try:
            nums.append(int(s["id"].split("-")[1]))
        except (IndexError, ValueError):
            continue
    return f"sprint-{max(nums, default=0) + 1}"


def _write_sprint(project_path: Path, data: dict) -> None:
    """Atomically write a sprint YAML file."""
    _atomic_write(
        _sprints_dir(project_path) / f"{data['id']}.yaml",
        yaml.safe_dump(data, sort_keys=False),
    )


def _close_active_sprints(project_path: Path) -> None:
    """Close any currently active sprints."""
    for sprint in load_sprints(project_path):
        if sprint["status"] == "active":
            sprint["status"] = "closed"
            sprint["end_date"] = str(datetime.now(timezone.utc).date())
            _write_sprint(project_path, sprint)


def create_sprint(
    project_path: Path,
    name: str,
    goal: str,
    start_date: str,
    end_date: str,
    phase: str,
    status: str = "planned",
) -> dict[str, Any]:
    """Create a new sprint YAML file."""
    sprint_id = _next_sprint_id(project_path)
    if status == "active":
        _close_active_sprints(project_path)
    data = {
        "id": sprint_id,
        "name": name,
        "goal": goal,
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
        "phase": phase,
        "stories": [],
    }
    _write_sprint(project_path, data)
    return data


def close_sprint(project_path: Path, sprint_id: str) -> dict | None:
    """Close a sprint: set status=closed and end_date=today."""
    sprint_dir = project_path / SPRINTS_SUBPATH
    f = sprint_dir / f"{sprint_id}.yaml"
    if not f.exists():
        return None
    data = yaml.safe_load(f.read_text())
    if data.get("status") == "closed":
        return None
    data["status"] = "closed"
    data["end_date"] = str(datetime.now(timezone.utc).date())
    _write_sprint(project_path, data)
    return data


def add_story_to_sprint(
    project_path: Path, sprint_id: str, story_id: str
) -> dict | None:
    """Add a story to a sprint. Updates both sprint YAML and story frontmatter."""
    sprint_file = project_path / SPRINTS_SUBPATH / f"{sprint_id}.yaml"
    if not sprint_file.exists():
        return None
    data = yaml.safe_load(sprint_file.read_text())
    if story_id not in data.get("stories", []):
        data.setdefault("stories", []).append(story_id)
        _write_sprint(project_path, data)
    # Update story frontmatter
    story_file = _find_story_file(project_path, story_id)
    if story_file:
        result = _read_story(story_file)
        if result:
            fm, body = result
            fm["sprint"] = sprint_id
            clean = _clean_fm(fm, story_id)
            clean["sprint"] = sprint_id
            _atomic_write(story_file, _build_story_content(clean, body))
    return data


def remove_story_from_sprint(
    project_path: Path, sprint_id: str, story_id: str
) -> dict | None:
    """Remove a story from a sprint. Updates both files."""
    sprint_file = project_path / SPRINTS_SUBPATH / f"{sprint_id}.yaml"
    if not sprint_file.exists():
        return None
    data = yaml.safe_load(sprint_file.read_text())
    stories = data.get("stories", [])
    if story_id in stories:
        stories.remove(story_id)
        data["stories"] = stories
        _write_sprint(project_path, data)
    # Clear sprint from story frontmatter
    story_file = _find_story_file(project_path, story_id)
    if story_file:
        result = _read_story(story_file)
        if result:
            fm, body = result
            fm.pop("sprint", None)
            clean = _clean_fm(fm, story_id)
            _atomic_write(story_file, _build_story_content(clean, body))
    return data
