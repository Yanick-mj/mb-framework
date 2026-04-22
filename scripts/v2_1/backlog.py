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

try:
    import yaml
except ImportError:  # pragma: no cover
    import sys
    print(
        "⚠️  mb-framework needs PyYAML.\nFix: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)


# Lower value = higher priority in render order.
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_DEFAULT_PRIORITY = "medium"


def _backlog_dir() -> Path:
    return Path.cwd() / "_backlog"


def _roadmap_path() -> Path:
    return Path.cwd() / "_roadmap.md"


def _parse_frontmatter(text: str) -> dict:
    """Extract the YAML frontmatter block. Returns {} if missing or invalid."""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _scan() -> tuple[List[dict], List[dict]]:
    """One-pass scan separating valid stories from priority-rejected ones."""
    d = _backlog_dir()
    if not d.exists():
        return [], []
    valid: List[dict] = []
    rejected: List[dict] = []
    for f in sorted(d.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm = _parse_frontmatter(content)
        # Treat missing + null/empty story_id as "no story" (YAML "null" parses as None)
        if not fm.get("story_id"):
            continue
        fm["_path"] = str(f)
        prio = fm.get("priority", _DEFAULT_PRIORITY)
        if prio not in _PRIORITY_ORDER:
            rejected.append(fm)
            continue
        valid.append(fm)

    valid.sort(key=lambda e: _PRIORITY_ORDER[e.get("priority", _DEFAULT_PRIORITY)])
    return valid, rejected


def list_backlog() -> List[dict]:
    """Return backlog stories with frontmatter metadata, priority-sorted.

    Strict rules (v2.1.2+):
    - Missing or empty _backlog/ → []
    - Files without story_id are skipped
    - Files with malformed YAML are skipped
    - Files with a priority NOT in {critical, high, medium, low} are REJECTED
      (use list_rejected() to inspect; render_backlog() surfaces them as
      warnings so typos like 'urgent' are caught early).
    - Missing priority defaults to 'medium'.
    """
    valid, _ = _scan()
    return valid


def list_rejected() -> List[dict]:
    """Return stories rejected for having an invalid priority."""
    _, rejected = _scan()
    return rejected


def render_backlog() -> str:
    """Human-readable priority-sorted backlog for /mb:backlog.

    Includes a ⚠️ warning block for any story rejected for an invalid priority
    so the author notices typos immediately.
    """
    valid, rejected = _scan()
    lines: List[str]

    from scripts.v2_1._emoji import tag
    bk_tag = tag("backlog")
    warn_tag = tag("warning")

    if not valid and not rejected:
        return (
            f"{bk_tag} No stories in _backlog/.\n"
            "Create one with the template at .claude/mb/templates/backlog-story.md"
        )

    lines = [f"{bk_tag} {len(valid)} story(ies) in backlog", ""]
    if valid:
        pri_w = max(len(i.get("priority", _DEFAULT_PRIORITY)) for i in valid)
        id_w = max(len(i["story_id"]) for i in valid)
        for i in valid:
            prio = i.get("priority", _DEFAULT_PRIORITY)
            lines.append(
                f"  [{prio:<{pri_w}}] {i['story_id']:<{id_w}}  {i.get('title', '')}"
            )

    if rejected:
        lines.append("")
        lines.append(
            f"{warn_tag} {len(rejected)} story(ies) REJECTED — priority must be "
            f"one of: {', '.join(sorted(_PRIORITY_ORDER))}"
        )
        for i in rejected:
            lines.append(
                f"  {i['story_id']} has priority={i.get('priority')!r}  "
                f"({i['_path']})"
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
    return p.read_text()


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "backlog"
    if cmd == "roadmap":
        print(read_roadmap())
    else:
        print(render_backlog())
