"""Backlog + roadmap helpers for mb v2.1.

Filesystem conventions (all optional — degrade gracefully):
    {cwd}/_roadmap.md              — strategic roadmap (free-form markdown)
    {cwd}/_backlog/STU-*.md        — backlog stories not yet scheduled

Each backlog story is a markdown file with YAML frontmatter:

    ---
    story_id: STU-52
    title: Add Stripe checkout
    priority: critical | high | medium | low
    created: 2026-04-19
    ---

Malformed frontmatter, missing story_id, or invalid YAML are silently skipped
so a stray draft never breaks /mb:backlog.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

import yaml


# Lower value = higher priority in render order.
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_DEFAULT_PRIORITY = "medium"


def _backlog_dir() -> Path:
    return Path.cwd() / "_backlog"


def _roadmap_path() -> Path:
    return Path.cwd() / "_roadmap.md"


def _parse_frontmatter(text: str) -> dict:
    """Extract the YAML frontmatter block. Returns {} if missing or invalid."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def list_backlog() -> List[dict]:
    """Return backlog stories with frontmatter metadata, priority-sorted.

    - Missing or empty _backlog/ → []
    - Files without story_id are skipped
    - Files with malformed YAML are skipped
    - Default priority is 'medium'
    """
    d = _backlog_dir()
    if not d.exists():
        return []
    items: List[dict] = []
    for f in sorted(d.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm = _parse_frontmatter(content)
        if "story_id" not in fm:
            continue
        fm["_path"] = f
        items.append(fm)

    def sort_key(entry: dict):
        prio = entry.get("priority", _DEFAULT_PRIORITY)
        return _PRIORITY_ORDER.get(prio, _PRIORITY_ORDER[_DEFAULT_PRIORITY])

    items.sort(key=sort_key)
    return items


def render_backlog() -> str:
    """Human-readable priority-sorted backlog for /mb:backlog."""
    items = list_backlog()
    if not items:
        return (
            "No stories in _backlog/.\n"
            "Create one with the template at .claude/mb/templates/backlog-story.md"
        )
    lines = [f"📋 {len(items)} story(ies) in backlog", ""]
    # Compute paddings for alignment
    pri_w = max(len(i.get("priority", _DEFAULT_PRIORITY)) for i in items)
    id_w = max(len(i["story_id"]) for i in items)
    for i in items:
        prio = i.get("priority", _DEFAULT_PRIORITY)
        lines.append(
            f"  [{prio:<{pri_w}}] {i['story_id']:<{id_w}}  {i.get('title', '')}"
        )
    return "\n".join(lines)


def read_roadmap() -> str:
    """Return the _roadmap.md body or a helpful placeholder."""
    p = _roadmap_path()
    if not p.exists():
        return (
            "No _roadmap.md at project root yet.\n"
            "Create one from .claude/mb/templates/roadmap.md"
        )
    return p.read_text(encoding="utf-8")


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "backlog"
    if cmd == "roadmap":
        print(read_roadmap())
    else:
        print(render_backlog())
