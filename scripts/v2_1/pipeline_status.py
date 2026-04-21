"""/mb:pipeline diagnostic helper.

Inspects the current project state and answers: where are you in the
mb-framework pipeline? What's the next agent? What artifacts exist?

Reads:
- mb-stage.yaml (current stage)
- memory/runs.jsonl (recent agent invocations, if any)
- _discovery/*/  (Discovery artifacts per feature)
- _bmad-output/deliverables/*/  (per-story typed artifacts)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    import sys
    print(
        "⚠️  mb-framework needs PyYAML.\nFix: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)


# Pipeline sequences (mirror agents/orchestrator/SKILL.md Routing Table)
PIPELINES: Dict[str, List[str]] = {
    "trivial-fix": ["quick-flow", "verifier"],
    "backend-feature": ["architect", "lead-dev", "be-dev", "lead-dev", "tea", "verifier"],
    "frontend-feature": ["architect", "lead-dev", "ux-designer", "fe-dev", "lead-dev", "tea", "verifier"],
    "full-stack-feature": ["architect", "lead-dev", "be-dev", "ux-designer", "fe-dev", "lead-dev", "tea", "verifier"],
    "redesign": ["pm", "ux-designer", "architect", "lead-dev", "ux-designer", "fe-dev", "lead-dev", "tea", "verifier"],
    "infra-change": ["architect", "devops", "verifier"],
    "test-only": ["tea", "verifier"],
    "doc-only": ["tech-writer"],
    "sprint-story": ["pm", "architect", "lead-dev", "fe-dev", "lead-dev", "tea", "verifier"],
    "sprint-planning": ["sm"],
    "product-discovery": ["pm", "ux-designer", "architect"],
    "architecture-review": ["architect"],
}


def _load_stage() -> str:
    stage_file = Path.cwd() / "mb-stage.yaml"
    if not stage_file.exists():
        return "scale"
    try:
        data = yaml.safe_load(stage_file.read_text()) or {}
    except yaml.YAMLError:
        return "scale"
    return str(data.get("stage", "scale"))


def _load_recent_runs(limit: int = 20) -> List[dict]:
    log = Path.cwd() / "memory" / "runs.jsonl"
    if not log.exists():
        return []
    lines = log.read_text().strip().splitlines()
    entries = []
    for l in lines[-limit * 2:]:  # grab more than limit in case of corrupted
        if not l.strip():
            continue
        try:
            entries.append(json.loads(l))
        except json.JSONDecodeError:
            continue
    entries.reverse()
    return entries[:limit]


def _discovery_features() -> List[dict]:
    """List features in _discovery/ with artifact presence info."""
    discovery_dir = Path.cwd() / "_discovery"
    if not discovery_dir.exists():
        return []
    out = []
    for feature_dir in sorted(discovery_dir.iterdir()):
        if not feature_dir.is_dir():
            continue
        artifacts = {
            "brief": (feature_dir / "brief.md").exists(),
            "ui_spec": (feature_dir / "ui-spec.md").exists(),
            "wireframes": any(feature_dir.glob("wireframes/*.excalidraw")),
            "user_flows": (feature_dir / "user-flows.md").exists(),
            "accessibility": (feature_dir / "accessibility-check.md").exists(),
            "architecture": (feature_dir / "architecture.md").exists(),
        }
        out.append({"name": feature_dir.name, "artifacts": artifacts})
    return out


def _ux_gate_status(feature: dict, stage: str) -> tuple[bool, List[str]]:
    """Returns (passed, missing_artifacts) for the UX GATE check."""
    a = feature["artifacts"]
    missing = []
    if stage in {"discovery", "mvp"}:
        required = ["brief", "ui_spec"]
    else:  # pmf, scale
        required = ["brief", "ui_spec", "wireframes", "user_flows"]
    for key in required:
        if not a[key]:
            label = {
                "brief": "brief.md",
                "ui_spec": "ui-spec.md",
                "wireframes": "wireframes/ (≥ 1 .excalidraw)",
                "user_flows": "user-flows.md",
                "accessibility": "accessibility-check.md",
            }[key]
            missing.append(label)
    return (len(missing) == 0, missing)


def render() -> str:
    from scripts.v2_1._emoji import tag
    t = tag("projects")

    stage = _load_stage()
    runs = _load_recent_runs(limit=5)
    features = _discovery_features()

    lines = [f"{t} mb pipeline status", ""]
    lines.append(f"  Stage:      {stage}")
    lines.append(f"  Runs log:   {len(runs)} recent entries")
    lines.append(f"  Features:   {len(features)} in _discovery/")
    lines.append("")

    if runs:
        lines.append("🏃 Recent agent activity (last 5):")
        for r in runs:
            lines.append(
                f"  {r['ts'][:19]}  {r['agent']:<12}  {r.get('story', '?'):<10}  {r.get('action', '?')}"
            )
        lines.append("")

    if features:
        lines.append("📋 UX GATE status per feature:")
        for f in features:
            passed, missing = _ux_gate_status(f, stage)
            icon = "✅" if passed else "🚧"
            lines.append(f"  {icon} {f['name']}")
            if not passed:
                lines.append(f"     Missing: {', '.join(missing)}")
                lines.append(
                    f"     → Run ux-designer (Discovery) or override via /mb:gate skip ux"
                )
        lines.append("")

    lines.append("📜 Available pipelines (see orchestrator/SKILL.md Routing Table):")
    for name, agents in PIPELINES.items():
        lines.append(f"  {name:<22}  {' → '.join(agents)}")

    lines.append("")
    lines.append("🔒 Anti-drift rule: use /mb:feature to let orchestrator classify.")
    lines.append("   Never invoke superpowers:* for tasks that have mb equivalents.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
