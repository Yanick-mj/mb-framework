"""Shared fixtures for dashboard tests."""
import json
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


@pytest.fixture
def tmp_home(monkeypatch):
    """Redirect ~ to tmpdir so tests never touch real $HOME."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("HOME", tmpdir)
        yield Path(tmpdir)


@pytest.fixture
def tmp_project(tmp_path, monkeypatch):
    """Minimal mb project layout, cd'd into it."""
    project = tmp_path / "demo-project"
    project.mkdir()
    (project / "mb-stage.yaml").write_text("stage: mvp\nsince: 2026-04-19\n")
    (project / "memory").mkdir()
    (project / "_bmad-output").mkdir()
    monkeypatch.chdir(project)
    return project


def write_story(root: Path, story_id: str, status: str,
                title: str = "", priority: str = "medium",
                labels: list[str] | None = None) -> None:
    """Helper: write a story .md with frontmatter to stories dir."""
    d = root / "_bmad-output" / "implementation-artifacts" / "stories"
    d.mkdir(parents=True, exist_ok=True)
    fm = {
        "story_id": story_id,
        "title": title or story_id,
        "status": status,
        "priority": priority,
    }
    if labels:
        fm["labels"] = labels
    content = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---\n\n## Why\nBecause.\n\n## Scope\nDo the thing.\n\n## Acceptance criteria\n- [ ] First item\n- [x] Done item\n"
    (d / f"{story_id}.md").write_text(content)


def write_backlog_story(root: Path, story_id: str, status: str,
                        title: str = "", priority: str = "medium") -> None:
    """Helper: write a story to _backlog/ dir."""
    d = root / "_backlog"
    d.mkdir(parents=True, exist_ok=True)
    fm = {
        "story_id": story_id,
        "title": title or story_id,
        "status": status,
        "priority": priority,
    }
    content = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---\n\n## Why\nReason.\n"
    (d / f"{story_id}.md").write_text(content)


def write_runs(root: Path, count: int = 3) -> None:
    """Helper: write N run entries to runs.jsonl."""
    log = root / "memory" / "runs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        entry = {
            "run_id": f"run{i:03d}",
            "ts": f"2026-05-04T10:{i:02d}:00.000000+00:00",
            "agent": f"agent-{i}",
            "story": f"STU-{i}",
            "action": f"action_{i}",
            "tokens_in": 100,
            "tokens_out": 50,
            "summary": f"Did thing {i}",
        }
        with log.open("a") as f:
            f.write(json.dumps(entry) + "\n")


def register_projects(tmp_home: Path, projects: list[dict]) -> None:
    """Helper: write projects to ~/.mb/projects.yaml."""
    mb_dir = tmp_home / ".mb"
    mb_dir.mkdir(parents=True, exist_ok=True)
    (mb_dir / "projects.yaml").write_text(
        yaml.safe_dump({"version": 1, "projects": projects}, sort_keys=False)
    )


def write_roadmap(root: Path, mission: str = "", phases: list[dict] | None = None) -> None:
    """Helper: write a _roadmap.md file."""
    lines = ["# Roadmap — Test Project", ""]
    if mission:
        lines += ["## Mission", "", mission, ""]
    if phases:
        lines += ["---", "", "## Phases", ""]
        for p in phases:
            lines.append(f"### Phase {p.get('num', '?')} — {p.get('name', 'Unnamed')} ({p.get('timeframe', 'TBD')})")
            lines.append("")
            if p.get("goal"):
                lines.append(f"**Goal:** {p['goal']}")
                lines.append("")
            if p.get("tracks"):
                lines.append("| Track | Work | Owner |")
                lines.append("|---|---|---|")
                for t in p["tracks"]:
                    lines.append(f"| {t[0]} | {t[1]} | {t[2]} |")
                lines.append("")
            if p.get("exit"):
                lines.append(f"**Exit criteria:** {p['exit']}")
                lines.append("")
    (root / "_roadmap.md").write_text("\n".join(lines))
