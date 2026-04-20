"""Story tree parser + ASCII renderer.

Stories live at: {cwd}/_bmad-output/implementation-artifacts/stories/*.md
Frontmatter must include story_id. Optional: parent_story, children, title.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml


def _stories_root() -> Path:
    return Path.cwd() / "_bmad-output" / "implementation-artifacts" / "stories"


def _parse_frontmatter(text: str) -> dict:
    """Extract the YAML frontmatter block from a story md file."""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    # Normalize children: accept "[a, b]" or "- a\n- b"
    children = data.get("children")
    if isinstance(children, str):
        data["children"] = [c.strip() for c in children.strip("[]").split(",") if c.strip()]
    return data


def scan_stories() -> List[dict]:
    """Return all stories with their frontmatter. Empty list if no stories dir."""
    root = _stories_root()
    if not root.exists():
        return []
    stories = []
    for path in sorted(root.glob("*.md")):
        fm = _parse_frontmatter(path.read_text())
        if "story_id" in fm:
            fm["_path"] = path
            stories.append(fm)
    return stories


def _build_tree(stories: List[dict]) -> Dict[Optional[str], List[str]]:
    """Return {parent_id: [child_ids]}. Root entries have parent_id=None."""
    children_by_parent: Dict[Optional[str], List[str]] = {}
    for s in stories:
        parent = s.get("parent_story")
        children_by_parent.setdefault(parent, []).append(s["story_id"])
    return children_by_parent


def _story_by_id(stories: List[dict]) -> Dict[str, dict]:
    return {s["story_id"]: s for s in stories}


def render(focus: Optional[str] = None) -> str:
    """ASCII render the tree. If focus is set, mark that story with <- me."""
    stories = scan_stories()
    if not stories:
        return "No stories found."
    by_parent = _build_tree(stories)
    by_id = _story_by_id(stories)

    lines: List[str] = []

    def walk(story_id: str, indent: str = "", is_last: bool = True):
        s = by_id.get(story_id)
        if not s:
            return
        connector = "└── " if is_last else "├── "
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
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    focus = sys.argv[1] if len(sys.argv) > 1 else None
    print(render(focus=focus))
