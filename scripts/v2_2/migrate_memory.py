"""Migrate v2.1 flat memory/ layout to v2.2 layered layout.

Safe: dry_run by default. Idempotent: re-running after first migration is a no-op.

Migration map (v2.1 → v2.2):
    memory/runs.jsonl        → memory/agents/_common/runs.jsonl
    memory/cost-log.md       → memory/project/cost-log.md
    memory/codebase-index.md → memory/project/codebase-index.md
    memory/wedge-log.md      → memory/project/wedge-log.md
    memory/stage-history.md  → memory/project/stage-history.md
    memory/_session/*        → memory/session/*
    (anything else: left in place — flagged in the report for user review)
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from scripts.v2_2 import _paths


MIGRATION_MAP: List[Tuple[str, str]] = [
    ("runs.jsonl", "agents/_common/runs.jsonl"),
    ("cost-log.md", "project/cost-log.md"),
    ("codebase-index.md", "project/codebase-index.md"),
    ("wedge-log.md", "project/wedge-log.md"),
    ("stage-history.md", "project/stage-history.md"),
]

# memory/_session/* → memory/session/*  (entire directory rename)
SESSION_DIR_MAP = ("_session", "session")


@dataclass
class Report:
    migrated_files: int = 0
    skipped_existing: int = 0
    not_found: int = 0
    unknown_files: List[str] = field(default_factory=list)


def run(dry_run: bool = True) -> Report:
    report = Report()
    root = _paths.memory_root()
    if not root.exists():
        return report

    for src_name, dst_rel in MIGRATION_MAP:
        src = root / src_name
        dst = root / dst_rel
        if not src.exists():
            report.not_found += 1
            continue
        if dst.exists():
            report.skipped_existing += 1
            continue
        report.migrated_files += 1
        if dry_run:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    # Directory-level move for _session/
    src_session = root / SESSION_DIR_MAP[0]
    dst_session = root / SESSION_DIR_MAP[1]
    if src_session.exists() and not dst_session.exists():
        report.migrated_files += 1
        if not dry_run:
            shutil.move(str(src_session), str(dst_session))

    # Flag unknown top-level memory/ files (not in migration map, not a layer dir)
    known = {s for s, _ in MIGRATION_MAP} | {
        SESSION_DIR_MAP[0],
        SESSION_DIR_MAP[1],
    }
    reserved_dirs = {"project", "agents", "stories", "session"}
    if root.exists():
        for item in sorted(root.iterdir()):
            if item.name in known or item.name in reserved_dirs:
                continue
            report.unknown_files.append(item.name)

    return report


def render(report: Report) -> str:
    lines = ["🧠 Memory migration report", ""]
    lines.append(f"  Migrated:         {report.migrated_files}")
    lines.append(f"  Skipped (exist):  {report.skipped_existing}")
    lines.append(f"  Not found:        {report.not_found}")
    if report.unknown_files:
        lines.append("")
        lines.append(
            f"  ⚠️  {len(report.unknown_files)} file(s) not in migration map "
            "(left in place):"
        )
        for f in report.unknown_files:
            lines.append(f"    - {f}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    dry = "--apply" not in sys.argv
    r = run(dry_run=dry)
    print(render(r))
    if dry:
        print("\n(dry run — pass --apply to actually move files)")
