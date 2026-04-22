"""Append-only run log stored at {cwd}/memory/runs.jsonl (v2.1) or
{cwd}/memory/agents/_common/runs.jsonl (v2.2+).

Each line is a JSON object:
  {"run_id": "...", "ts": "...", "agent": "...", "story": "...",
   "action": "...", "tokens_in": N, "tokens_out": N, "summary": "..."}
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List


def _log_path() -> Path:
    """Return path to runs.jsonl.

    v2.2-aware: prefers memory/agents/_common/runs.jsonl if the v2.2
    layered layout exists (either the directory or an existing file).
    Falls back to memory/runs.jsonl (v2.1 layout) otherwise.
    """
    v2_2 = Path.cwd() / "memory" / "agents" / "_common" / "runs.jsonl"
    v2_1 = Path.cwd() / "memory" / "runs.jsonl"
    if v2_2.parent.exists() or v2_2.exists():
        return v2_2
    return v2_1


def append(
    *,
    agent: str,
    story: str,
    action: str,
    tokens_in: int,
    tokens_out: int,
    summary: str,
) -> str:
    """Append a run entry. Returns the run_id."""
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex[:12]
    entry = {
        "run_id": run_id,
        "ts": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "agent": agent,
        "story": story,
        "action": action,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "summary": summary,
    }
    with path.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return run_id


def load_recent(limit: int = 10) -> List[dict]:
    """Return up to `limit` most recent entries (newest first).

    Uses line order as tiebreaker (last line = most recent).
    """
    path = _log_path()
    if not path.exists():
        return []
    lines = path.read_text().strip().splitlines()
    entries = []
    for l in lines:
        if not l.strip():
            continue
        try:
            entries.append(json.loads(l))
        except json.JSONDecodeError:
            continue  # skip corrupted lines
    # Reverse since file is append-only (last entry = most recent)
    entries.reverse()
    return entries[:limit]


def render_recent(limit: int = 10) -> str:
    """Human-readable recent runs listing."""
    from scripts.v2_1._emoji import tag
    t = tag("runs")
    entries = load_recent(limit)
    if not entries:
        return f"{t} No runs logged yet."
    lines = [f"{t} Last {len(entries)} run(s)", ""]
    for e in entries:
        lines.append(
            f"  {e['ts'][:19]}  {e['agent']:<12}  {e['story']:<10}  {e['action']}"
        )
        lines.append(f"    └─ {e['summary']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(render_recent(limit))
