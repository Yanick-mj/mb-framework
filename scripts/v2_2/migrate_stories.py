"""Add `status:` frontmatter to existing stories that don't have one.

Heuristic:
  - Story file lives in the mb output dir (``_mb-output/`` or legacy
    ``_bmad-output/``) under ``implementation-artifacts/stories/`` → default `todo`
  - Story file lives in _backlog/ → default `backlog`
  - If frontmatter already has status, leave alone

⚠️  Heuristic limitation: stories in stories/ that are actually DONE will be
marked `todo` by this migration. The report surfaces these files so you can
manually edit them to `status: done` after running with --apply. There's no
automated way to know which legacy stories are complete (no git-based signal
we trust).

Dry-run by default. --apply to actually modify files.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import yaml

from scripts.v2_2 import _paths


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)


@dataclass
class Report:
    updated: List[str] = field(default_factory=list)
    already_has_status: int = 0
    no_frontmatter: List[str] = field(default_factory=list)
    skipped_invalid: List[str] = field(default_factory=list)


def _files_needing_status() -> List[Tuple[Path, str]]:
    """Return (path, default_status) tuples for stories without status."""
    targets: List[Tuple[Path, str]] = []
    stories = _paths.stories_root()
    backlog = _paths.backlog_dir()
    if stories.exists():
        for p in stories.glob("*.md"):
            targets.append((p, "todo"))
    if backlog.exists():
        for p in backlog.glob("*.md"):
            targets.append((p, "backlog"))
    return targets


def run(dry_run: bool = True) -> Report:
    report = Report()
    for path, default in _files_needing_status():
        text = path.read_text()
        m = FRONTMATTER_RE.match(text)
        if not m:
            report.no_frontmatter.append(str(path))
            continue
        try:
            data = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            report.skipped_invalid.append(str(path))
            continue
        if not isinstance(data, dict):
            report.skipped_invalid.append(str(path))
            continue
        if "status" in data:
            report.already_has_status += 1
            continue

        report.updated.append(str(path))
        if dry_run:
            continue

        # Inject status before the first frontmatter close marker
        new_fm = yaml.safe_dump({**data, "status": default}, sort_keys=False).rstrip()
        new_text = f"---\n{new_fm}\n---\n" + text[m.end():].lstrip("\n")
        # Preserve trailing newline intent
        if text.endswith("\n") and not new_text.endswith("\n"):
            new_text += "\n"
        path.write_text(new_text)
    return report


def render(report: Report) -> str:
    lines = ["📖 Story status migration", ""]
    lines.append(f"  Updated:              {len(report.updated)}")
    lines.append(f"  Already had status:   {report.already_has_status}")
    lines.append(f"  No frontmatter:       {len(report.no_frontmatter)}")
    lines.append(f"  Skipped (invalid):    {len(report.skipped_invalid)}")
    if report.updated:
        lines.append("")
        lines.append("  Files updated (default applied):")
        for f in report.updated:
            lines.append(f"    - {f}")
        lines.append("")
        lines.append(
            "  ⚠️  MANUAL REVIEW REQUIRED: the default is `todo` for files in "
            "stories/ and `backlog` for _backlog/. If a story is actually "
            "`in_progress`, `in_review`, or `done`, edit its frontmatter manually."
        )
    if report.no_frontmatter:
        lines.append("")
        lines.append("  ⚠️  Files without frontmatter (not modified):")
        for f in report.no_frontmatter:
            lines.append(f"    - {f}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    dry = "--apply" not in sys.argv
    r = run(dry_run=dry)
    print(render(r))
    if dry:
        print("\n(dry run — pass --apply to actually modify files)")
