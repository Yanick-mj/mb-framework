"""Integration: after migration, every agent composes correctly at every stage.

Uses the REAL repo's agents/ and skills/ directories (not a tmp fixture) because
the whole point is to verify that the 13 migrated AGENT.md files + the 5 core
skills compose cleanly for Claude Code loading.

Stage is controlled by writing an mb-stage.yaml to a tmp cwd while keeping the
agents/ + skills/ lookup pointing at the real repo root (via a symlink inside
the tmp cwd's .claude/mb).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.v2_2 import agent_loader


V1_AGENTS = [
    "architect", "be-dev", "devops", "fe-dev", "lead-dev", "orchestrator",
    "pm", "quick-flow", "sm", "tea", "tech-writer", "ux-designer", "verifier",
]

EARLY_AGENTS = [
    "idea-validator", "stage-advisor", "user-interviewer", "wedge-builder",
]

STAGES = ["discovery", "mvp", "pmf", "scale"]


def _repo_root() -> Path:
    # tests file is at scripts/v2_2/tests/test_*.py → 3 levels up
    return Path(__file__).resolve().parents[3]


@pytest.fixture
def tmp_project_symlinked_mb(tmp_path, monkeypatch):
    """tmp cwd with .claude/mb → symlink to the real repo root.

    agent_loader._mb_root() will find .claude/mb/agents/ and use those real
    agent files, while mb-stage.yaml and any memory/ paths resolve in the
    tmp cwd. This lets us exercise real agents under different stages without
    touching the repo working tree.
    """
    project = tmp_path / "demo-project"
    project.mkdir()
    (project / "memory").mkdir()
    (project / "_mb-output").mkdir()

    claude_dir = project / ".claude"
    claude_dir.mkdir()
    (claude_dir / "mb").symlink_to(_repo_root(), target_is_directory=True)

    monkeypatch.chdir(project)
    return project


@pytest.mark.parametrize("name", V1_AGENTS)
@pytest.mark.parametrize("stage", STAGES)
def test_every_v1_agent_composes_at_every_stage(
    tmp_project_symlinked_mb, name, stage
):
    """Every v1 agent must compose successfully at all 4 stages."""
    (tmp_project_symlinked_mb / "mb-stage.yaml").write_text(
        f"stage: {stage}\nsince: 2026-04-22\n"
    )
    composed = agent_loader.compose_agent(name)
    assert len(composed) > 100, (
        f"{name} at stage={stage} produced suspiciously short output "
        f"({len(composed)} chars)"
    )
    # Each composed agent should mention its own name (in persona, frontmatter, etc.)
    lc = composed.lower()
    assert name in lc or name.replace("-", "") in lc, (
        f"{name} at stage={stage} — composed output doesn't mention agent name"
    )


@pytest.mark.parametrize("name", EARLY_AGENTS)
def test_early_agents_compose(tmp_project_symlinked_mb, name):
    """agents-early/ also composes (legacy SKILL.md fallback for these)."""
    composed = agent_loader.compose_agent(name)
    assert len(composed) > 50, (
        f"early agent {name} produced suspiciously short output "
        f"({len(composed)} chars)"
    )


def test_core_skills_are_present_in_repo(tmp_project_symlinked_mb):
    """Sanity: the 5 core skills extracted in G4 must exist."""
    skills_dir = _repo_root() / "skills" / "core"
    for name in [
        "evidence-rules", "stage-adaptation", "run-summary",
        "preflight-tool-rbac", "handoff-contract",
    ]:
        assert (skills_dir / name / "SKILL.md").exists(), (
            f"core skill {name} missing from skills/core/"
        )


def test_7_tool_touching_agents_import_preflight_skill(tmp_project_symlinked_mb):
    """F4 contract: 7 tool-touching agents must declare preflight-tool-rbac."""
    import yaml
    tool_agents = [
        "be-dev", "fe-dev", "devops", "tea",
        "verifier", "lead-dev", "tech-writer",
    ]
    for name in tool_agents:
        uses_skills_path = _repo_root() / "agents" / name / "uses-skills.yaml"
        assert uses_skills_path.exists(), f"{name}/uses-skills.yaml missing"
        data = yaml.safe_load(uses_skills_path.read_text())
        core = data.get("uses", {}).get("core", [])
        assert "preflight-tool-rbac" in core, (
            f"{name} does NOT declare core/preflight-tool-rbac "
            f"(actual core: {core})"
        )
