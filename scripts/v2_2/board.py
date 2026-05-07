"""ASCII kanban board for /mb:board.

Reads stories from the mb output dir (default ``_mb-output/``, legacy
fallback ``_bmad-output/``) under ``implementation-artifacts/stories/*.md``
and groups by status. Only the 5 canonical statuses render; anything else
is skipped silently (same strict approach as backlog priority in v2.1.2).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import yaml

from scripts.v2_2 import _paths


COLUMNS = ["backlog", "todo", "in_progress", "in_review", "done"]
COLUMN_HEADERS = {
    "backlog": "BACKLOG",
    "todo": "TODO",
    "in_progress": "IN PROG",
    "in_review": "REVIEW",
    "done": "DONE",
}
COL_WIDTH = 14

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


def _group_by_status() -> Dict[str, List[dict]]:
    root = _paths.stories_root()
    groups: Dict[str, List[dict]] = {c: [] for c in COLUMNS}
    if not root.exists():
        return groups
    for f in sorted(root.glob("*.md")):
        fm = _parse_frontmatter(f.read_text())
        status = fm.get("status")
        if status in groups:
            groups[status].append(fm)
    return groups


def render() -> str:
    groups = _group_by_status()
    total = sum(len(v) for v in groups.values())
    if total == 0:
        return "🎯 No stories yet.\nCreate one in _backlog/ or _mb-output/implementation-artifacts/stories/."

    # Header row
    header = ""
    for col in COLUMNS:
        label = f"{COLUMN_HEADERS[col]} ({len(groups[col])})"
        header += f"│ {label:<{COL_WIDTH}} "
    header += "│"

    # Body rows (each col stacked vertically)
    max_rows = max(len(v) for v in groups.values())
    body_lines = []
    for i in range(max_rows):
        line = ""
        for col in COLUMNS:
            entry = groups[col][i] if i < len(groups[col]) else None
            if entry is None:
                line += f"│ {'':<{COL_WIDTH}} "
            else:
                label = f"{entry.get('story_id', '?')}"
                line += f"│ {label:<{COL_WIDTH}} "
        line += "│"
        body_lines.append(line)

    top_border = (
        "┌"
        + ("─" * (COL_WIDTH + 2) + "┬") * (len(COLUMNS) - 1)
        + ("─" * (COL_WIDTH + 2))
        + "┐"
    )
    mid_border = (
        "├"
        + ("─" * (COL_WIDTH + 2) + "┼") * (len(COLUMNS) - 1)
        + ("─" * (COL_WIDTH + 2))
        + "┤"
    )
    bot_border = (
        "└"
        + ("─" * (COL_WIDTH + 2) + "┴") * (len(COLUMNS) - 1)
        + ("─" * (COL_WIDTH + 2))
        + "┘"
    )

    out = [f"🎯 Board ({total} stories)", ""]
    out.append(top_border)
    out.append(header)
    out.append(mid_border)
    out.extend(body_lines)
    out.append(bot_border)
    return "\n".join(out)


if __name__ == "__main__":
    print(render())
