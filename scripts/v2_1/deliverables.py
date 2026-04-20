"""Typed, versioned deliverables for mb stories.

Layout:
  {cwd}/_bmad-output/deliverables/{story_id}/{TYPE}-rev{n}.md

Example: _bmad-output/deliverables/STU-46/PLAN-rev2.md
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


VALID_TYPES = {"PLAN", "IMPL", "REVIEW", "DOC", "SPEC", "TEST", "NOTE"}


def _deliverables_root() -> Path:
    return Path.cwd() / "_bmad-output" / "deliverables"


def path(story_id: str, type: str, rev: int) -> Path:
    """Canonical path for a deliverable. Does not check existence."""
    if type not in VALID_TYPES:
        raise ValueError(f"Invalid type {type!r}. Must be one of {sorted(VALID_TYPES)}")
    return _deliverables_root() / story_id / f"{type}-rev{rev}.md"


def next_rev(story_id: str, type: str) -> int:
    """Return the next revision number for a given story_id + type."""
    if type not in VALID_TYPES:
        raise ValueError(f"Invalid type {type!r}. Must be one of {sorted(VALID_TYPES)}")
    story_dir = _deliverables_root() / story_id
    if not story_dir.exists():
        return 1
    pattern = re.compile(rf"^{re.escape(type)}-rev(\d+)\.md$")
    existing_revs = []
    for f in story_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            existing_revs.append(int(m.group(1)))
    return (max(existing_revs) + 1) if existing_revs else 1


def write(story_id: str, type: str, body: str, author: str, rev: int | None = None) -> Path:
    """Write a deliverable, auto-incrementing rev if not supplied. Returns the path.

    Race-safe: uses exclusive create (O_CREAT | O_EXCL via mode='x'). If the
    target rev already exists (because next_rev() was stale, or an explicit rev
    clashes), retries with rev+1 up to 10 times.
    """
    if rev is None:
        rev = next_rev(story_id, type)
    # Validate the starting rev's type (raises ValueError for invalid type)
    path(story_id, type, rev)
    now = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    for _ in range(10):
        target = path(story_id, type, rev)
        target.parent.mkdir(parents=True, exist_ok=True)
        frontmatter = (
            "---\n"
            f"story_id: {story_id}\n"
            f"type: {type}\n"
            f"rev: {rev}\n"
            f"author: {author}\n"
            f"created: {now}\n"
            "---\n\n"
        )
        try:
            with open(target, "x", encoding="utf-8") as f:
                f.write(frontmatter + body)
            return target
        except FileExistsError:
            rev += 1
    raise RuntimeError(
        f"Could not reserve a rev slot for {story_id}/{type} after 10 tries"
    )


def list_for_story(story_id: str) -> Dict[str, List[Path]]:
    """Return {type: [sorted paths by rev asc]} for a story. Empty dict if none."""
    story_dir = _deliverables_root() / story_id
    if not story_dir.exists():
        return {}
    by_type: Dict[str, List[Path]] = {}
    pattern = re.compile(r"^(\w+)-rev(\d+)\.md$")
    for f in sorted(story_dir.iterdir()):
        m = pattern.match(f.name)
        if not m:
            continue
        t = m.group(1)
        if t not in VALID_TYPES:
            continue
        by_type.setdefault(t, []).append(f)
    for t in by_type:
        by_type[t].sort(key=lambda p: int(pattern.match(p.name).group(2)))
    return by_type


def render_list(story_id: str) -> str:
    """Human-readable listing for /mb:deliverables STU-N."""
    by_type = list_for_story(story_id)
    if not by_type:
        return f"No deliverables for {story_id}."
    lines = [f"Deliverables for {story_id}", ""]
    for t, files in by_type.items():
        lines.append(f"  {t}")
        for f in files:
            lines.append(f"    - {f.name}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python deliverables.py <story-id>", file=sys.stderr)
        sys.exit(1)
    print(render_list(sys.argv[1]))
