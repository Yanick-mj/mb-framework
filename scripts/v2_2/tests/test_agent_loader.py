"""Tests for agent_loader.py — compose AGENT.md + skills into SKILL.md."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.v2_2 import agent_loader


def _scaffold_agent(project: Path, name: str, agent_body: str,
                    uses_skills: dict | None = None) -> None:
    agent_dir = project / ".claude" / "mb" / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "AGENT.md").write_text(agent_body)
    if uses_skills is not None:
        (agent_dir / "uses-skills.yaml").write_text(yaml.safe_dump(uses_skills))


def _scaffold_skill(project: Path, tier: str, name: str, body: str) -> None:
    skill_dir = project / ".claude" / "mb" / "skills" / tier / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(body)


def test_compose_agent_with_no_skills(tmp_project):
    """Agent with empty uses-skills.yaml → SKILL.md = just AGENT.md content."""
    _scaffold_agent(tmp_project, "fe-dev", "# fe-dev\nI am frontend.",
                    uses_skills={"uses": {}})
    generated = agent_loader.compose_agent("fe-dev")
    assert "I am frontend" in generated


def test_compose_agent_concatenates_core_skills(tmp_project):
    _scaffold_skill(tmp_project, "core", "evidence-rules",
                    "## Rules\n1. Cite file paths\n")
    _scaffold_skill(tmp_project, "core", "run-summary",
                    "## Run Summary\nFormat: AGENT_NAME on STORY\n")
    _scaffold_agent(tmp_project, "fe-dev", "# fe-dev\nPersona.",
                    uses_skills={
                        "version": 1,
                        "agent": "fe-dev",
                        "uses": {"core": ["evidence-rules", "run-summary"]},
                    })
    generated = agent_loader.compose_agent("fe-dev")
    assert "I am" not in generated or "Persona" in generated
    assert "Cite file paths" in generated
    assert "Run Summary" in generated


def test_compose_respects_stage_filter(tmp_project):
    """uses-skills at_stage.mvp filters to only subset of skills."""
    _scaffold_skill(tmp_project, "core", "evidence-rules", "## Evidence rules\n")
    _scaffold_skill(tmp_project, "core", "tdd-discipline", "## TDD rules\n")
    _scaffold_agent(tmp_project, "fe-dev", "# fe-dev\n", uses_skills={
        "version": 1, "agent": "fe-dev",
        "uses": {"core": ["evidence-rules", "tdd-discipline"]},
        "at_stage": {
            "mvp": ["evidence-rules"],          # TDD off at mvp
            "pmf": ["evidence-rules", "tdd-discipline"],
            "scale": ["evidence-rules", "tdd-discipline"],
        },
    })
    (tmp_project / "mb-stage.yaml").write_text("stage: mvp\n")
    generated = agent_loader.compose_agent("fe-dev")
    assert "Evidence rules" in generated
    assert "TDD rules" not in generated  # filtered out at mvp


def test_compose_fails_loud_if_skill_not_registered(tmp_project):
    """Skill declared in uses-skills.yaml but not registered → raise."""
    _scaffold_agent(tmp_project, "fe-dev", "# fe-dev\n", uses_skills={
        "version": 1, "agent": "fe-dev",
        "uses": {"core": ["nonexistent"]},
    })
    with pytest.raises(FileNotFoundError, match="nonexistent"):
        agent_loader.compose_agent("fe-dev")


def test_compose_legacy_SKILL_md_used_if_no_AGENT_md(tmp_project):
    """Backward compat: if agents/fe-dev/ has SKILL.md but no AGENT.md,
    use the legacy file as-is."""
    legacy_dir = tmp_project / ".claude" / "mb" / "agents" / "legacy-agent"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "SKILL.md").write_text("# Legacy full agent\n## Rules\n...")
    generated = agent_loader.compose_agent("legacy-agent")
    assert "Legacy full agent" in generated


def test_write_generated_skill_md(tmp_project):
    """compose_and_write produces .claude/skills/mb-{name}/SKILL.md."""
    _scaffold_agent(tmp_project, "fe-dev", "# fe-dev\n", uses_skills={"uses": {}})
    output_path = agent_loader.compose_and_write("fe-dev")
    assert output_path.exists()
    assert output_path == tmp_project / ".claude" / "skills" / "mb-fe-dev" / "SKILL.md"
