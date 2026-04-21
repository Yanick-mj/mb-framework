"""Guards: ensure v2.1.6 pipeline-enforcement sections are present in the
key artifacts. These tests catch regressions if a future refactor drops the
required guardrails.
"""
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


# =================================================================
# orchestrator/SKILL.md guards
# =================================================================

def _orchestrator_content() -> str:
    p = REPO_ROOT / "agents" / "orchestrator" / "SKILL.md"
    assert p.exists(), f"missing {p}"
    return p.read_text()


def test_orchestrator_has_redesign_classification():
    text = _orchestrator_content()
    assert "redesign" in text.lower(), "orchestrator missing redesign class"
    # Specifically in routing table
    assert "pm → ux-designer (discovery, MANDATORY)" in text


def test_orchestrator_lists_redesign_keywords():
    text = _orchestrator_content()
    for kw in ["refonte", "refaire", "rework", "revamp"]:
        assert kw in text.lower(), f"missing redesign keyword '{kw}'"


def test_orchestrator_has_ux_gate_section():
    text = _orchestrator_content()
    assert "### UX GATE" in text
    assert "HALT" in text  # enforcement verb
    assert "override" in text.lower()


def test_orchestrator_has_handoff_artifact_validation():
    text = _orchestrator_content()
    assert "### Handoff Artifact Validation" in text
    assert "contract" in text.lower()


def test_orchestrator_has_anti_drift_routing():
    text = _orchestrator_content()
    assert "### Anti-drift routing" in text
    assert "NEVER invoke" in text or "NEVER use" in text
    # must mention superpowers explicitly
    assert "superpowers" in text


# =================================================================
# ux-designer/SKILL.md guards
# =================================================================

def _ux_designer_content() -> str:
    p = REPO_ROOT / "agents" / "ux-designer" / "SKILL.md"
    assert p.exists(), f"missing {p}"
    return p.read_text()


def test_ux_designer_has_anti_skip_rules():
    text = _ux_designer_content()
    assert "Anti-skip rules" in text
    # Required artifact enforcement
    assert "status: blocked" in text
    # Explicit user-approval requirement
    assert "inline message" in text.lower() or "user approval" in text.lower()


def test_ux_designer_enforces_discovery_artifacts():
    text = _ux_designer_content()
    for artifact in ["ui-spec.md", "wireframes/", "user-flows.md", "accessibility-check.md"]:
        assert artifact in text, f"ux-designer doesn't require {artifact}"


def test_ux_designer_refuses_delivery_without_discovery():
    text = _ux_designer_content()
    assert "Delivery mode" in text
    assert "ui-spec.md does NOT exist" in text or "Discovery required first" in text


# =================================================================
# templates/CLAUDE.md.template guards
# =================================================================

def _claude_template_content() -> str:
    p = REPO_ROOT / "templates" / "CLAUDE.md.template"
    assert p.exists(), f"missing {p}"
    return p.read_text()


def test_claude_template_has_pipeline_enforcement():
    text = _claude_template_content()
    assert "Pipeline enforcement" in text
    assert "RÈGLES STRICTES" in text or "STRICT RULES" in text


def test_claude_template_has_superpowers_mapping_table():
    text = _claude_template_content()
    # Must map mb agents vs superpowers explicitly
    assert "superpowers" in text
    assert "/mb:feature" in text
    assert "/mb:fix" in text
    assert "/mb:review" in text


def test_claude_template_has_anti_drift_rules():
    text = _claude_template_content()
    assert "Anti-drift rules" in text or "anti-drift" in text.lower()
    assert "NEVER" in text  # enforcement verb


def test_claude_template_has_ux_gate_section():
    text = _claude_template_content()
    assert "UX GATE" in text


def test_claude_template_has_legitimate_lightening_examples():
    text = _claude_template_content()
    assert "lightening" in text.lower() or "alléger" in text.lower() \
        or "lighten" in text.lower()


# =================================================================
# commands/pipeline.md exists
# =================================================================

def test_pipeline_command_exists():
    p = REPO_ROOT / "commands" / "pipeline.md"
    assert p.exists(), f"missing {p}"
    text = p.read_text()
    assert "pipeline_status" in text  # references the helper
    assert "/mb:pipeline" in text
