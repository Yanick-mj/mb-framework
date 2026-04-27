"""Compose core skill SKILL.md files into a subagent preamble.

The orchestrator injects this preamble into every Task subagent prompt so
that subagents produce ``runs.jsonl`` entries, ``handoff.md`` blocks, and
follow evidence rules — without needing the full agent composition pipeline.

Skills included:
- ``evidence-rules/SKILL.md``
- ``run-summary/SKILL.md``
- ``handoff-contract/SKILL.md``

Orchestrator-only skills (``preflight-tool-rbac``, ``stage-adaptation``)
are NOT included.
"""
from __future__ import annotations

from pathlib import Path

from scripts.v2_2.agent_loader import _mb_root
from scripts.v2_2.memory import session_path

PREAMBLE_FILENAME = "subagent-preamble.md"

CORE_SKILLS = [
    "evidence-rules",
    "run-summary",
    "handoff-contract",
]


def compose() -> str:
    """Read and concatenate core skill SKILL.md files into a single string.

    Returns
    -------
    str
        The concatenated preamble content.

    Raises
    ------
    FileNotFoundError
        If any required skill SKILL.md is missing.
    """
    mb_root = _mb_root()
    parts = [
        "<!-- subagent-preamble: injected by orchestrator (v2.2) -->",
        "<!-- These protocols are MANDATORY for all subagents -->",
        "",
    ]

    for skill_name in CORE_SKILLS:
        skill_path = mb_root / "skills" / "core" / skill_name / "SKILL.md"
        if not skill_path.exists():
            raise FileNotFoundError(
                f"Core skill {skill_name}/SKILL.md not found at {skill_path}"
            )
        parts.append(f"\n---\n")
        parts.append(f"<!-- skill: core/{skill_name} -->")
        parts.append(skill_path.read_text(encoding="utf-8"))

    return "\n".join(parts)


def compose_and_write() -> Path:
    """Compose the preamble and write it to ``memory/session/subagent-preamble.md``.

    Returns
    -------
    Path
        The path to the written file.
    """
    content = compose()
    target = session_path(PREAMBLE_FILENAME)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
