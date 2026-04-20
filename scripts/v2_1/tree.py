"""Story tree parser + ASCII renderer.

Stories live at: {cwd}/_bmad-output/implementation-artifacts/stories/*.md
Frontmatter must include story_id. Optional: parent_story, children, title.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    import yaml
except ImportError:  # pragma: no cover
    import sys
    print(
        "⚠️  mb-framework needs PyYAML.\nFix: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)


# Story IDs must match this pattern — prevents path traversal / shell meta
# when story_id comes from CLI arg (sys.argv) in the focus= parameter.
_STORY_ID_RE = re.compile(r"^[A-Z]+-[A-Za-z0-9_-]+$")


def _validate_story_id(story_id: str) -> None:
    """Reject story_id with path separators, shell meta, or null bytes."""
    if not isinstance(story_id, str) or not _STORY_ID_RE.match(story_id):
        raise ValueError(
            f"Invalid story_id {story_id!r}. "
            f"Expected pattern: [A-Z]+-[A-Za-z0-9_-]+  (e.g. STU-46)"
        )


def _stories_root() -> Path:
    return Path.cwd() / "_bmad-output" / "implementation-artifacts" / "stories"


def _parse_frontmatter(text: str) -> dict:
    """Extract the YAML frontmatter block from a story md file."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    # Normalize children: list form is ideal. When YAML parses the value as a
    # string (because the frontmatter quoted the whole list), strip brackets
    # AND any surrounding quotes on each id so we never end up with '"STU-2"'.
    children = data.get("children")
    if isinstance(children, str):
        parts = children.strip().strip("[]").split(",")
        cleaned: List[str] = []
        for p in parts:
            p = p.strip().strip('"').strip("'")
            if p:
                cleaned.append(p)
        data["children"] = cleaned
    elif children is not None and not isinstance(children, list):
        # Defensive: unknown type → treat as no children
        data["children"] = []
    return data


def scan_stories() -> List[dict]:
    """Return all stories with their frontmatter. Empty list if no stories dir."""
    root = _stories_root()
    if not root.exists():
        return []
    stories = []
    for path in sorted(root.glob("*.md")):
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # binary garbage or unreadable — skip silently
        fm = _parse_frontmatter(raw)
        # Reject missing / null / empty story_id (YAML "null" parses as None)
        if not fm.get("story_id"):
            continue
        fm["_path"] = path
        stories.append(fm)
    return stories


def _build_tree(stories: List[dict]) -> Dict[Optional[str], List[str]]:
    """Return {parent_id: [child_ids]}. Root entries have parent_id=None.

    Stories referencing a non-existent parent are promoted to root level.
    """
    known_ids = {s["story_id"] for s in stories}
    children_by_parent: Dict[Optional[str], List[str]] = {}
    for s in stories:
        parent = s.get("parent_story")
        if parent and parent not in known_ids:
            parent = None  # promote to root if parent doesn't exist
        children_by_parent.setdefault(parent, []).append(s["story_id"])
    return children_by_parent


def _story_by_id(stories: List[dict]) -> Dict[str, dict]:
    return {s["story_id"]: s for s in stories}


def render(focus: Optional[str] = None) -> str:
    """ASCII render the tree. If focus is set, mark that story with <- me."""
    if focus is not None:
        _validate_story_id(focus)
    stories = scan_stories()
    if not stories:
        from scripts.v2_1._emoji import tag
        return f"{tag('tree')} No stories found."
    by_parent = _build_tree(stories)
    by_id = _story_by_id(stories)

    from scripts.v2_1._emoji import tag
    lines: List[str] = [f"{tag('tree')} Story tree ({len(stories)} stories)", ""]
    visited: Set[str] = set()

    def walk(story_id: str, indent: str = "", is_last: bool = True):
        s = by_id.get(story_id)
        if not s:
            return
        connector = "└── " if is_last else "├── "
        if story_id in visited:
            lines.append(f"{indent}{connector}{story_id} [CYCLE]")
            return
        visited.add(story_id)
        marker = "  ← me" if focus == story_id else ""
        title = s.get("title", "")
        lines.append(f"{indent}{connector}{story_id} {title}{marker}")
        children = by_parent.get(story_id, [])
        new_indent = indent + ("    " if is_last else "│   ")
        for i, c in enumerate(children):
            walk(c, new_indent, i == len(children) - 1)

    roots = by_parent.get(None, [])
    for i, r in enumerate(roots):
        walk(r, "", i == len(roots) - 1)

    # Render any stories not reachable from roots (cycles)
    unreachable = [sid for sid in by_id if sid not in visited]
    if unreachable:
        for i, sid in enumerate(unreachable):
            walk(sid, "", i == len(unreachable) - 1)

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    focus = sys.argv[1] if len(sys.argv) > 1 else None
    print(render(focus=focus))
