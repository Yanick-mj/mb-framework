"""Semi-automated migration: legacy agents/*/SKILL.md → AGENT.md + uses-skills.yaml.

Strategy:
1. Read the legacy SKILL.md
2. Detect the 5 common sections (evidence-rules, stage-adaptation,
   run-summary, preflight, handoff) → remove them from the content
3. Write what's left to AGENT.md (persona + agent-specific rules)
4. Write a uses-skills.yaml listing the 3 core skills as default — user
   edits to add preflight-tool-rbac / handoff-contract per agent role.

Dry-run by default. --apply to actually write the 2 new files.
Preserves the original SKILL.md (agent_loader prefers AGENT.md when present).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict, Any

import yaml

from scripts.v2_2 import _paths


# Headers whose section (until next `## `) should be dropped from AGENT.md
# (now live in skills/core/*/SKILL.md).
COMMON_SECTION_HEADERS = [
    r"^## Stage Adaptation\b",
    r"^## Run Summary\b",
    r"^## Pre-flight: Tool RBAC\b",
    r"^## Handoff contract\b",
]


DEFAULT_CORE_SKILLS: Dict[str, Any] = {
    "version": 1,
    "uses": {
        "core": [
            "evidence-rules",
            "stage-adaptation",
            "run-summary",
        ],
    },
    # preflight-tool-rbac and handoff-contract added per-agent by hand.
}


def _strip_common_sections(content: str) -> str:
    """Remove every COMMON_SECTION from `## Header` through end-of-section."""
    out_lines: List[str] = []
    in_common = False
    for line in content.splitlines():
        if any(re.match(pat, line) for pat in COMMON_SECTION_HEADERS):
            in_common = True
            continue
        if in_common and line.startswith("## ") and not any(
            re.match(pat, line) for pat in COMMON_SECTION_HEADERS
        ):
            in_common = False
        if not in_common:
            out_lines.append(line)
    return "\n".join(out_lines)


def migrate_agent(agent_dir: Path, dry_run: bool = True) -> Dict[str, Any]:
    """Migrate a single agent dir. Returns a report dict."""
    skill_md = agent_dir / "SKILL.md"
    if not skill_md.exists():
        return {"status": "no-legacy-skill-md", "agent": agent_dir.name}
    if (agent_dir / "AGENT.md").exists():
        return {"status": "already-migrated", "agent": agent_dir.name}

    content = skill_md.read_text(encoding="utf-8")
    agent_content = _strip_common_sections(content)

    uses_skills: Dict[str, Any] = dict(DEFAULT_CORE_SKILLS)
    uses_skills["agent"] = agent_dir.name

    if dry_run:
        return {
            "status": "would-migrate",
            "agent": agent_dir.name,
            "legacy_lines": len(content.splitlines()),
            "new_agent_md_lines": len(agent_content.splitlines()),
            "skills_to_add": uses_skills["uses"],
        }

    (agent_dir / "AGENT.md").write_text(agent_content, encoding="utf-8")
    (agent_dir / "uses-skills.yaml").write_text(
        yaml.safe_dump(uses_skills, sort_keys=False)
    )
    return {"status": "migrated", "agent": agent_dir.name}


def migrate_all(dry_run: bool = True, only: List[str] | None = None) -> List[Dict[str, Any]]:
    """Iterate through agents/ and agents-early/.

    If `only` is set, migrate only those agent names (batch mode).
    """
    reports: List[Dict[str, Any]] = []
    mb_root = _paths.project_root() / ".claude" / "mb"
    if not (mb_root / "agents").exists():
        mb_root = _paths.project_root()
    for base in ["agents", "agents-early"]:
        base_dir = mb_root / base
        if not base_dir.exists():
            continue
        for agent_path in sorted(base_dir.iterdir()):
            if not agent_path.is_dir():
                continue
            if only is not None and agent_path.name not in only:
                continue
            reports.append(migrate_agent(agent_path, dry_run=dry_run))
    return reports


if __name__ == "__main__":
    import sys

    dry = "--apply" not in sys.argv
    # --only a,b,c restricts to a subset (batch migration)
    only = None
    for arg in sys.argv[1:]:
        if arg.startswith("--only="):
            only = arg.split("=", 1)[1].split(",")

    results = migrate_all(dry_run=dry, only=only)
    for r in results:
        print(f"  {r.get('status'):<20} {r.get('agent')}")
    if dry:
        print("\n(dry run — pass --apply to actually migrate)")
