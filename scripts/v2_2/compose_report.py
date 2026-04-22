"""Monitor composed SKILL.md health (size + Claude Code rejections).

AT INSTALL: warn if a composed SKILL.md is unreasonably large.
  - 500+ lines or 50KB+ → warning
  - 1000+ lines or 100KB+ → critical
  (thresholds conservative — Claude Code has no documented hard limit.
  Adjust after dogfood if rejection log reveals the real cliff.)

AT RUNTIME: agents that detect a Claude Code skill-load failure append a
JSONL entry via log_rejection(). Next compose_report render surfaces them
for investigation.

Task 0 scaffolding — full implementation lands in G6 per the v2.2 plan.
The scaffold is present early so tests can reference the module.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from scripts.v2_2 import _paths


LINE_WARN = 500
LINE_CRIT = 1000
BYTE_WARN = 50_000
BYTE_CRIT = 100_000


def scan_sizes() -> List[Dict]:
    """Return per-skill size info with warning/critical flags.

    Scans .claude/skills/ in the current project. Returns empty list if the
    directory doesn't exist (no install yet).
    """
    out: List[Dict] = []
    d = _paths.claude_skills_dir()
    if not d.exists():
        return out
    for skill_dir in sorted(d.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        text = skill_md.read_text(encoding="utf-8")
        lines = text.count("\n") + 1 if text else 0
        size = skill_md.stat().st_size
        flag = "ok"
        if lines >= LINE_CRIT or size >= BYTE_CRIT:
            flag = "critical"
        elif lines >= LINE_WARN or size >= BYTE_WARN:
            flag = "warning"
        out.append({
            "name": skill_dir.name,
            "path": str(skill_md),
            "lines": lines,
            "bytes": size,
            "flag": flag,
        })
    return out


def load_rejections(limit: int = 20) -> List[dict]:
    """Return up to `limit` most recent rejection entries (newest first).

    Entry schema:
        {"ts":"...","skill":"mb-fe-dev","reason":"too_large"|"load_error"|...,
         "context":"optional","bytes":...}
    """
    log = _paths.claude_skill_rejections_log()
    if not log.exists():
        return []
    raw_lines = log.read_text(encoding="utf-8").strip().splitlines()
    entries: List[dict] = []
    # Take trailing slice wide enough to account for any corrupted lines
    for l in raw_lines[-limit * 2:]:
        if not l.strip():
            continue
        try:
            entries.append(json.loads(l))
        except json.JSONDecodeError:
            continue  # skip corrupted lines
    entries.reverse()
    return entries[:limit]


def log_rejection(
    *, skill: str, reason: str, context: str = "", bytes_size: int = 0
) -> None:
    """Append a rejection entry.

    Called by agents when Claude Code refuses to load or execute a skill.
    """
    log = _paths.claude_skill_rejections_log()
    log.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "skill": skill,
        "reason": reason,
        "context": context,
        "bytes": bytes_size,
    }
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def render() -> str:
    """Human-readable composed-skill health report."""
    # Reuse v2.1 emoji tag if available (install.sh may not have composed yet)
    try:
        from scripts.v2_1._emoji import tag
        t = tag("projects")
    except Exception:
        t = "📁"

    sizes = scan_sizes()
    rejections = load_rejections(limit=10)

    lines = [f"{t} Composed SKILL.md health check", ""]

    if not sizes:
        lines.append("  (no .claude/skills/ composed yet — run install.sh first)")
    else:
        warnings = [s for s in sizes if s["flag"] == "warning"]
        crits = [s for s in sizes if s["flag"] == "critical"]
        oks = [s for s in sizes if s["flag"] == "ok"]
        lines.append(
            f"  Scanned {len(sizes)} composed skill(s): "
            f"✅ {len(oks)} ok, ⚠️ {len(warnings)} warn, 🔴 {len(crits)} crit"
        )
        for s in crits + warnings:
            icon = "🔴" if s["flag"] == "critical" else "⚠️ "
            lines.append(
                f"  {icon} {s['name']:<30} "
                f"{s['lines']:>5} lines, {s['bytes']:>7} bytes"
            )

    if rejections:
        lines.append("")
        lines.append(f"🚫 {len(rejections)} recent skill-load rejection(s):")
        for r in rejections:
            lines.append(
                f"  {r['ts'][:19]}  {r['skill']:<25}  {r['reason']}  "
                f"({r.get('bytes', '?')} bytes)"
            )

    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
