"""Compose AGENT.md + declared skills into a Claude Code-compatible SKILL.md.

Resolves the agent's `uses-skills.yaml`, loads each skill SKILL.md from its
tier directory, and concatenates them with AGENT.md to produce a single
SKILL.md file that Claude Code loads via its Skill tool.

Stage-aware: if `uses-skills.at_stage.{current_stage}` is defined, only
those skills are composed. Fallback = all skills in `uses.{tier}`.

Backward compat: if the agent directory has SKILL.md but NO AGENT.md,
the legacy file is returned as-is (no composition).
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import yaml

from scripts.v2_2 import _paths


MB_ROOT_CANDIDATES = [".claude/mb", "."]


def _mb_root() -> Path:
    """Resolve the mb-framework installation root for this project."""
    for candidate in MB_ROOT_CANDIDATES:
        p = _paths.project_root() / candidate
        if (p / "agents").exists() or (p / "skills").exists():
            return p
    raise FileNotFoundError(
        f"mb-framework not found at any of {MB_ROOT_CANDIDATES}"
    )


def _agent_dir(name: str) -> Path:
    return _mb_root() / "agents" / name


def _skill_dir(tier: str, name: str) -> Path:
    return _mb_root() / "skills" / tier / name


def _current_stage() -> str:
    stage_file = _paths.project_root() / "mb-stage.yaml"
    if not stage_file.exists():
        return "scale"
    try:
        data = yaml.safe_load(stage_file.read_text()) or {}
    except yaml.YAMLError:
        return "scale"
    return str(data.get("stage", "scale"))


def _resolve_skills_for_stage(uses_skills: dict, stage: str) -> List[Tuple[str, str]]:
    """Return list of (tier, name) skills to include for the given stage."""
    skills_by_tier = uses_skills.get("uses", {}) or {}
    at_stage = uses_skills.get("at_stage", {}) or {}
    if stage in at_stage:
        allowed = set(at_stage[stage])
        out: List[Tuple[str, str]] = []
        for tier, names in skills_by_tier.items():
            for name in names:
                if name in allowed:
                    out.append((tier, name))
        return out
    # No stage filter → include everything in uses
    out = []
    for tier, names in skills_by_tier.items():
        for name in names:
            out.append((tier, name))
    return out


def compose_agent(name: str) -> str:
    """Return the composed SKILL.md content for agent `name`.

    If agents/{name}/AGENT.md exists → compose with uses-skills.
    Else if agents/{name}/SKILL.md exists → return legacy content (back-compat).
    Else → raise FileNotFoundError.
    """
    agent_dir = _agent_dir(name)
    agent_md = agent_dir / "AGENT.md"
    legacy_md = agent_dir / "SKILL.md"

    if agent_md.exists():
        # v2.2+ 3-layer composition
        body = agent_md.read_text(encoding="utf-8")
        uses_yaml = agent_dir / "uses-skills.yaml"
        if not uses_yaml.exists():
            # AGENT.md without uses.yaml → no skills composed
            return body
        uses_skills = yaml.safe_load(uses_yaml.read_text()) or {}
        stage = _current_stage()
        skills_to_include = _resolve_skills_for_stage(uses_skills, stage)

        composed = [body, ""]
        for tier, skill_name in skills_to_include:
            skill_md = _skill_dir(tier, skill_name) / "SKILL.md"
            if not skill_md.exists():
                raise FileNotFoundError(
                    f"Skill {tier}/{skill_name} required by agent {name} "
                    f"not found at {skill_md}"
                )
            composed.append(f"\n---\n")
            composed.append(f"<!-- skill: {tier}/{skill_name} -->")
            composed.append(skill_md.read_text(encoding="utf-8"))
        return "\n".join(composed)

    if legacy_md.exists():
        # Backward compat: old-style all-in-one SKILL.md
        return legacy_md.read_text(encoding="utf-8")

    raise FileNotFoundError(
        f"Agent {name} has neither AGENT.md nor SKILL.md at {agent_dir}"
    )


def compose_and_write(name: str) -> Path:
    """Write the composed SKILL.md to .claude/skills/mb-{name}/SKILL.md.

    This is the file Claude Code actually loads when you invoke Skill(mb-{name}).
    """
    content = compose_agent(name)
    target = (
        _paths.project_root() / ".claude" / "skills" / f"mb-{name}" / "SKILL.md"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def compose_all() -> List[Path]:
    """Compose SKILL.md for every agent in agents/ and agents-early/."""
    mb_root = _mb_root()
    written = []
    for base in ["agents", "agents-early"]:
        base_dir = mb_root / base
        if not base_dir.exists():
            continue
        for agent_path in sorted(base_dir.iterdir()):
            if agent_path.is_dir():
                written.append(compose_and_write(agent_path.name))
    return written


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Compose a specific agent
        print(compose_agent(sys.argv[1]))
    else:
        # Compose all, for install-time use
        written = compose_all()
        print(f"Composed {len(written)} agents:")
        for p in written:
            print(f"  + {p}")
