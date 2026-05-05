"""Data layer for the dashboard — wraps existing v2.1/v2.2 parsers.

All functions return plain dicts/lists. No FastAPI dependency.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import re

import yaml

from scripts.v2_2 import _paths

STORIES_SUBPATH = Path("_bmad-output") / "implementation-artifacts" / "stories"

_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)


@contextmanager
def project_context(path: Path):
    """Temporarily override _paths.project_root() and cwd to point at `path`."""
    original_fn = _paths.project_root
    original_cwd = Path.cwd()
    changed_dir = False

    _paths.project_root = lambda: path
    if path.is_dir():
        os.chdir(path)
        changed_dir = True
    try:
        yield
    finally:
        _paths.project_root = original_fn
        if changed_dir:
            os.chdir(original_cwd)


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
    """Count stories by status (including _backlog/)."""
    from scripts.v2_2.board import COLUMNS
    result: dict[str, int] = {c: 0 for c in COLUMNS}
    for story in _scan_all_stories(path):
        status = story.get("status")
        if status in result:
            result[status] += 1
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
    stories_dir = path / STORIES_SUBPATH
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


def get_board_data(path: Path, priority_filter: str | None = None) -> dict[str, list[dict]]:
    """Group stories into kanban columns with enriched card data."""
    from scripts.v2_2.board import COLUMNS
    groups: dict[str, list[dict]] = {c: [] for c in COLUMNS}
    for story in _scan_all_stories(path):
        status = story.get("status")
        if status not in groups:
            continue
        if priority_filter and story.get("priority") != priority_filter:
            continue
        groups[status].append({
            "story_id": story.get("story_id", "?"),
            "title": story.get("title", ""),
            "status": status,
            "priority": story.get("priority", "medium"),
            "labels": story.get("labels") or [],
            "sort_order": story.get("sort_order", 999999),
        })
    # Sort each column by sort_order (lower first)
    for col in groups:
        groups[col].sort(key=lambda s: s["sort_order"])
    return groups


def get_recent_runs(path: Path, limit: int = 5) -> list[dict]:
    """Load recent agent runs from runs.jsonl (newest first)."""
    # Check v2.2 path first, fall back to v2.1
    v2_2 = path / "memory" / "agents" / "_common" / "runs.jsonl"
    v2_1 = path / "memory" / "runs.jsonl"
    log_path = v2_2 if (v2_2.parent.exists() or v2_2.exists()) else v2_1
    if not log_path.exists():
        return []
    entries = []
    for line in log_path.read_text().strip().splitlines():
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    entries.reverse()
    return entries[:limit]


def get_story_detail(path: Path, story_id: str) -> dict[str, Any] | None:
    """Find and parse a single story by its story_id."""
    for story in _scan_all_stories(path):
        if story.get("story_id") == story_id:
            file_path = Path(story["_path"])
            text = file_path.read_text()
            sections = _parse_sections(text)
            return {
                "story_id": story.get("story_id"),
                "title": story.get("title", ""),
                "priority": story.get("priority", "medium"),
                "status": story.get("status", "unknown"),
                "created": str(story.get("created", "")),
                "sections": sections,
            }
    return None


def _parse_sections(text: str) -> dict[str, Any]:
    """Extract Why, Scope, Acceptance criteria from story body."""
    body = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)
    sections: dict[str, Any] = {"why": "", "scope": "", "description": "", "acceptance_criteria": []}
    parts = re.split(r"^## (.+)$", body, flags=re.MULTILINE)
    for i in range(1, len(parts) - 1, 2):
        header = parts[i].strip().lower()
        content = parts[i + 1].strip()
        if "why" in header:
            sections["why"] = content
        elif "scope" in header:
            sections["scope"] = content
        elif "description" in header:
            sections["description"] = content
        elif "acceptance" in header or "criteria" in header:
            sections["acceptance_criteria"] = _parse_checklist(content)
    return sections


def _parse_checklist(text: str) -> list[dict[str, Any]]:
    """Parse markdown checklist items."""
    items = []
    for m in re.finditer(r"- \[([ xX])\] (.+)", text):
        items.append({
            "done": m.group(1).lower() == "x",
            "text": m.group(2).strip(),
        })
    return items


def get_roadmap_data(path: Path) -> dict[str, Any]:
    """Parse _roadmap.md into structured roadmap data."""
    roadmap_file = path / "_roadmap.md"
    if not roadmap_file.exists():
        return {"mission": "", "phases": [], "raw": ""}

    text = roadmap_file.read_text()
    mission = _extract_roadmap_mission(text)
    phases = _extract_roadmap_phases(text)

    return {
        "mission": mission,
        "phases": phases,
        "raw": text if not mission and not phases else "",
    }


def _extract_roadmap_mission(text: str) -> str:
    """Extract text under ## Mission header."""
    m = re.search(r"^## Mission\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return ""
    return m.group(1).strip().strip("<!-- -->").strip()


def _extract_roadmap_phases(text: str) -> list[dict[str, Any]]:
    """Extract ### Phase N sections with goal, tracks table, exit criteria."""
    phases = []
    pattern = r"^### Phase (\d+\w*)\s*[—–-]\s*(.+?)(?:\(([^)]+)\))?\s*$"
    parts = re.split(pattern, text, flags=re.MULTILINE)
    for i in range(1, len(parts) - 3, 4):
        num = parts[i].strip()
        name = parts[i + 1].strip()
        timeframe = (parts[i + 2] or "").strip()
        body = parts[i + 3]

        goal = ""
        gm = re.search(r"\*\*Goal:\*\*\s*(.+)", body)
        if gm:
            goal = gm.group(1).strip()

        tracks = []
        table_rows = re.findall(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|$", body, re.MULTILINE)
        for row in table_rows:
            cells = [c.strip() for c in row]
            if cells[0].startswith("---") or cells[0].lower() == "track":
                continue
            tracks.append({"track": cells[0], "work": cells[1], "owner": cells[2]})

        exit_criteria = ""
        em = re.search(r"\*\*Exit criteria:\*\*\s*(.+)", body)
        if em:
            exit_criteria = em.group(1).strip()

        phases.append({
            "num": num,
            "name": name,
            "timeframe": timeframe,
            "goal": goal,
            "tracks": tracks,
            "exit": exit_criteria,
            "current": len(phases) == 0,
        })

    return phases


DELIVERABLES_SUBPATH = Path("_bmad-output") / "deliverables"


def get_deliverables_list(path: Path, story_id: str) -> list[dict[str, str]]:
    """List deliverable files for a story."""
    d = path / DELIVERABLES_SUBPATH / story_id
    if not d.exists():
        return []
    files = sorted(f for f in d.iterdir() if f.is_file())
    return [{"filename": f.name} for f in files]


def get_deliverable_content(path: Path, story_id: str, filename: str) -> dict[str, str] | None:
    """Read a deliverable file and return raw + rendered HTML."""
    f = path / DELIVERABLES_SUBPATH / story_id / filename
    if not f.exists():
        return None
    raw = f.read_text()
    try:
        import markdown
        html = markdown.markdown(raw, extensions=["fenced_code", "tables"])
    except ImportError:
        html = f"<pre>{raw}</pre>"
    return {"filename": filename, "raw": raw, "html": html}


def get_inbox_data(path: Path) -> dict[str, Any]:
    """Get actionable items: in_review + blocked + approvals."""
    from scripts.v2_2 import inbox
    with project_context(path):
        stories = inbox._scan_stories()
        approvals = inbox._scan_approvals()

    in_review = [s for s in stories if s.get("status") == "in_review"]
    blocked = [s for s in stories if s.get("status") == "blocked"]

    return {
        "in_review": in_review,
        "blocked": blocked,
        "approvals": approvals,
        "total": len(in_review) + len(blocked) + len(approvals),
    }
