"""Namespaced skill registry (Paperclip-style runtime discovery).

Skills live in {cwd}/skills/{tier}/{key}/SKILL.md where tier ∈ {core, project, community}.

Only skills listed in memory/skills-registry.yaml are considered discoverable
by agents. This prevents stray .md files from polluting the skill surface.

Registry schema:
    version: 1
    registered:
      - key: core/evidence-rules
        source: bundled        # bundled | local | git:<url>
        added: 2026-04-19T...
        used_by: [orchestrator, verifier]
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import yaml

from scripts.v2_2 import _paths


VALID_TIERS = {"core", "project", "community"}


def _registry_load() -> Dict[str, Any]:
    path = _paths.skills_registry()
    if not path.exists():
        return {"version": 1, "registered": []}
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return {"version": 1, "registered": []}
    data.setdefault("version", 1)
    if not isinstance(data.get("registered"), list):
        data["registered"] = []
    return data


def _registry_save(data: Dict[str, Any]) -> None:
    path = _paths.skills_registry()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def _skill_dir(tier: str, key: str) -> Path:
    return _paths.skills_dir(tier) / key


def list_registered() -> List[Dict[str, Any]]:
    return _registry_load()["registered"]


def register(*, tier: str, key: str, source: str) -> None:
    """Register a skill. Skill must already exist on disk at skills/{tier}/{key}/SKILL.md."""
    if tier not in VALID_TIERS:
        raise ValueError(f"Invalid tier {tier!r}. Must be one of {sorted(VALID_TIERS)}")
    skill_md = _skill_dir(tier, key) / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"Expected {skill_md} to exist before registration")

    data = _registry_load()
    full_key = f"{tier}/{key}"
    data["registered"] = [s for s in data["registered"] if s.get("key") != full_key]
    data["registered"].append({
        "key": full_key,
        "source": source,
        "added": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "used_by": [],
    })
    _registry_save(data)


def unregister(full_key: str) -> None:
    """Remove a skill entry. Does NOT delete the files on disk."""
    data = _registry_load()
    data["registered"] = [s for s in data["registered"] if s.get("key") != full_key]
    _registry_save(data)


def render() -> str:
    items = list_registered()
    if not items:
        return "📦 No skills registered.\nUse /mb:skill add <path-or-github-url>."
    lines = [f"📦 {len(items)} skill(s) registered", ""]
    for s in items:
        lines.append(
            f"  {s['key']:<30} source={s.get('source', '?')}  "
            f"added={s.get('added', '')[:10]}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
