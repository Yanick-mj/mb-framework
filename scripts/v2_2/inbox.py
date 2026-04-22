"""Unified blocker view: in_review stories + blocked stories + pending approvals.

Backs /mb:inbox. Morning standup in 30s:
- Which stories need review attention?
- Which are blocked?
- What approvals are waiting on the user?
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

import yaml

from scripts.v2_2 import _paths


ACTIONABLE_STATUSES = {"in_review", "blocked"}

_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)


def _parse_frontmatter(text: str) -> dict:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _scan_stories() -> List[dict]:
    root = _paths.stories_root()
    if not root.exists():
        return []
    out: List[dict] = []
    for f in sorted(root.glob("*.md")):
        fm = _parse_frontmatter(f.read_text())
        if fm.get("status") in ACTIONABLE_STATUSES:
            fm["_path"] = f
            out.append(fm)
    return out


def _scan_approvals() -> List[dict]:
    d = _paths.memory_root() / "approvals-pending"
    if not d.exists():
        return []
    out: List[dict] = []
    for f in sorted(d.glob("*.md")):
        fm = _parse_frontmatter(f.read_text())
        fm["_name"] = f.stem
        fm["_path"] = f
        out.append(fm)
    return out


def render() -> str:
    stories = _scan_stories()
    approvals = _scan_approvals()
    total = len(stories) + len(approvals)

    if total == 0:
        return (
            "📥 Inbox: nothing to review.\n"
            "(No stories in review/blocked, no approvals pending.)"
        )

    lines = [f"📥 Inbox — {total} item(s)", ""]

    in_review = [s for s in stories if s.get("status") == "in_review"]
    blocked = [s for s in stories if s.get("status") == "blocked"]

    if in_review:
        lines.append(f"🟡 In Review ({len(in_review)})")
        for s in in_review:
            lines.append(f"  {s.get('story_id', '?'):<10} {s.get('title', '')}")
        lines.append("")

    if blocked:
        lines.append(f"🚧 Blocked ({len(blocked)})")
        for s in blocked:
            lines.append(f"  {s.get('story_id', '?'):<10} {s.get('title', '')}")
        lines.append("")

    if approvals:
        lines.append(f"⏳ Approvals pending ({len(approvals)})")
        for a in approvals:
            lines.append(f"  {a['_name']:<30} {a.get('kind', '')}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
