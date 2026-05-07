"""Tests for init_scaffold.py — /mb:init deterministic scaffolder."""
import json
from pathlib import Path

import pytest

from scripts.v2_1 import init_scaffold


def _write_package_json(root: Path, deps: dict, dev_deps: dict = None) -> None:
    """Helper: write a minimal package.json with given deps."""
    data = {
        "name": root.name,
        "version": "0.1.0",
        "dependencies": deps or {},
        "devDependencies": dev_deps or {},
    }
    (root / "package.json").write_text(json.dumps(data))


# =================================================================
# detect_stack
# =================================================================

def test_detect_stack_unknown_when_no_manifest(tmp_project):
    info = init_scaffold.detect_stack()
    assert info["stack"] == "unknown"
    assert info["framework"] is None
    assert info["tools"] == []


def test_detect_stack_node_react_vite(tmp_project):
    _write_package_json(tmp_project,
        deps={"react": "^18.0.0", "vite": "^5.0.0"},
        dev_deps={"vitest": "^1.0.0", "typescript": "^5.0.0"})
    info = init_scaffold.detect_stack()
    assert info["stack"] == "node"
    assert info["framework"] == "react+vite"
    assert "vitest" in info["tools"]
    assert "typescript" in info["tools"]


def test_detect_stack_nextjs(tmp_project):
    _write_package_json(tmp_project, deps={"next": "^14.0.0", "react": "^18.0.0"})
    info = init_scaffold.detect_stack()
    assert info["framework"] == "next.js"


def test_detect_stack_expo(tmp_project):
    _write_package_json(tmp_project,
        deps={"expo": "~50.0.0", "react-native": "0.73.0"})
    info = init_scaffold.detect_stack()
    assert info["framework"] == "expo"


def test_detect_stack_tailwind_detected(tmp_project):
    _write_package_json(tmp_project, deps={"react": "^18"},
                        dev_deps={"tailwindcss": "^3"})
    info = init_scaffold.detect_stack()
    assert "tailwind" in info["tools"]


def test_detect_stack_rust(tmp_project):
    (tmp_project / "Cargo.toml").write_text('[package]\nname = "x"\n')
    info = init_scaffold.detect_stack()
    assert info["stack"] == "rust"


def test_detect_stack_python(tmp_project):
    (tmp_project / "pyproject.toml").write_text('[project]\nname = "x"\n')
    info = init_scaffold.detect_stack()
    assert info["stack"] == "python"


def test_detect_stack_supabase_dir_alone(tmp_project):
    """supabase/ directory counts as a supabase tool even without npm dep."""
    (tmp_project / "supabase").mkdir()
    info = init_scaffold.detect_stack()
    assert "supabase" in info["tools"]


def test_detect_stack_monorepo_turbo(tmp_project):
    _write_package_json(tmp_project, deps={"next": "^14"})
    (tmp_project / "turbo.json").write_text('{"$schema": "..."}')
    info = init_scaffold.detect_stack()
    assert info.get("monorepo") == "turbo"


def test_detect_stack_monorepo_pnpm(tmp_project):
    (tmp_project / "pnpm-workspace.yaml").write_text("packages:\n  - 'apps/*'\n")
    _write_package_json(tmp_project, deps={"react": "^18"})
    info = init_scaffold.detect_stack()
    assert info.get("monorepo") == "pnpm-workspaces"


def test_detect_stack_monorepo_yarn_workspaces_in_package_json(tmp_project):
    data = {"name": "x", "workspaces": ["apps/*", "packages/*"]}
    (tmp_project / "package.json").write_text(json.dumps(data))
    info = init_scaffold.detect_stack()
    assert info.get("monorepo") == "yarn-workspaces"


def test_detect_stack_no_monorepo_for_single_package(tmp_project):
    _write_package_json(tmp_project, deps={"react": "^18"})
    info = init_scaffold.detect_stack()
    assert info.get("monorepo") is None


def test_detect_stack_handles_broken_package_json(tmp_project):
    """A malformed package.json must not crash detection."""
    (tmp_project / "package.json").write_text("not json {{{")
    info = init_scaffold.detect_stack()
    # Should detect 'node' (file exists) but no framework/tools
    assert info["stack"] == "node"
    assert info["framework"] is None


# =================================================================
# scaffold_dirs
# =================================================================

def test_scaffold_dirs_creates_all_expected(tmp_project):
    created = init_scaffold.scaffold_dirs()
    assert (tmp_project / "_backlog").is_dir()
    assert (tmp_project / "_mb-output" / "deliverables").is_dir()
    assert (tmp_project / "_mb-output" / "implementation-artifacts" / "stories").is_dir()
    assert (tmp_project / "memory" / "_session").is_dir()
    # .gitkeep in each
    assert (tmp_project / "_backlog" / ".gitkeep").exists()


def test_scaffold_dirs_idempotent(tmp_project):
    init_scaffold.scaffold_dirs()
    # Run again — should not error
    created_again = init_scaffold.scaffold_dirs()
    # Already-existing dirs not reported as newly created
    assert created_again == []


# =================================================================
# scaffold_roadmap
# =================================================================

def test_scaffold_roadmap_creates_when_absent(tmp_project, monkeypatch):
    # Set MB_FRAMEWORK_PATH to the real framework so templates are reachable
    monkeypatch.setenv("MB_FRAMEWORK_PATH", str(_framework_root()))
    result = init_scaffold.scaffold_roadmap()
    assert result is not None
    assert (tmp_project / "_roadmap.md").exists()
    assert "Roadmap" in (tmp_project / "_roadmap.md").read_text()


def test_scaffold_roadmap_preserves_existing(tmp_project, monkeypatch):
    monkeypatch.setenv("MB_FRAMEWORK_PATH", str(_framework_root()))
    (tmp_project / "_roadmap.md").write_text("# My custom roadmap")
    result = init_scaffold.scaffold_roadmap()
    assert result is None
    assert (tmp_project / "_roadmap.md").read_text() == "# My custom roadmap"


# =================================================================
# scaffold_claude_md
# =================================================================

def test_scaffold_claude_md_creates_with_stack_placeholders(tmp_project, monkeypatch):
    monkeypatch.setenv("MB_FRAMEWORK_PATH", str(_framework_root()))
    _write_package_json(tmp_project, deps={"react": "^18", "vite": "^5"},
                        dev_deps={"typescript": "^5"})
    stack = init_scaffold.detect_stack()
    result = init_scaffold.scaffold_claude_md(stack)
    assert result is not None
    content = (tmp_project / "CLAUDE.md").read_text()
    assert "react+vite" in content
    assert "typescript" in content
    assert tmp_project.name in content


def test_scaffold_claude_md_preserves_existing(tmp_project, monkeypatch):
    monkeypatch.setenv("MB_FRAMEWORK_PATH", str(_framework_root()))
    (tmp_project / "CLAUDE.md").write_text("# Custom instructions")
    stack = {"stack": "node", "framework": "react", "tools": []}
    result = init_scaffold.scaffold_claude_md(stack)
    assert result is None
    assert (tmp_project / "CLAUDE.md").read_text() == "# Custom instructions"


def test_scaffold_claude_md_handles_unknown_stack(tmp_project, monkeypatch):
    monkeypatch.setenv("MB_FRAMEWORK_PATH", str(_framework_root()))
    stack = {"stack": "unknown", "framework": None, "tools": []}
    result = init_scaffold.scaffold_claude_md(stack)
    content = (tmp_project / "CLAUDE.md").read_text()
    # Should have fallback text, no exception
    assert "unknown" in content or "none detected" in content.lower()


# =================================================================
# seed_first_backlog_story
# =================================================================

def test_seed_first_backlog_story_creates_stu_1(tmp_project):
    init_scaffold.scaffold_dirs()
    stack = {"stack": "node", "framework": "react+vite", "tools": ["typescript", "vitest"]}
    result = init_scaffold.seed_first_backlog_story(stack)
    assert result is not None
    path = tmp_project / "_backlog" / "STU-1-initial-setup.md"
    assert path.exists()
    content = path.read_text()
    assert "story_id: STU-1" in content
    assert "priority: high" in content
    assert "node" in content  # stack recorded in notes


def test_seed_first_backlog_story_skips_if_backlog_nonempty(tmp_project):
    init_scaffold.scaffold_dirs()
    (tmp_project / "_backlog" / "STU-99-existing.md").write_text(
        "---\nstory_id: STU-99\n---\n"
    )
    stack = {"stack": "node", "framework": None, "tools": []}
    result = init_scaffold.seed_first_backlog_story(stack)
    # Since backlog already has content, don't seed
    assert result is None
    # Must not have created STU-1
    assert not (tmp_project / "_backlog" / "STU-1-initial-setup.md").exists()


def test_seeded_story_is_picked_up_by_backlog(tmp_project, monkeypatch):
    """Full integration: seed → /mb:backlog shows it."""
    monkeypatch.setenv("MB_FRAMEWORK_PATH", str(_framework_root()))
    init_scaffold.scaffold_dirs()
    stack = {"stack": "node", "framework": "react", "tools": []}
    init_scaffold.seed_first_backlog_story(stack)
    # Import backlog module and render
    from scripts.v2_1 import backlog
    out = backlog.render_backlog()
    assert "STU-1" in out


# =================================================================
# run_all
# =================================================================

def test_run_all_creates_everything_on_fresh_project(tmp_project, monkeypatch):
    monkeypatch.setenv("MB_FRAMEWORK_PATH", str(_framework_root()))
    _write_package_json(tmp_project, deps={"react": "^18"})
    report = init_scaffold.run_all()
    # Verify ALL artifacts present
    assert (tmp_project / "_backlog").is_dir()
    assert (tmp_project / "_roadmap.md").exists()
    assert (tmp_project / "CLAUDE.md").exists()
    assert (tmp_project / "_backlog" / "STU-1-initial-setup.md").exists()
    # Report structure
    assert report["stack"]["stack"] == "node"
    assert len(report["created"]) > 0


def test_run_all_idempotent(tmp_project, monkeypatch):
    monkeypatch.setenv("MB_FRAMEWORK_PATH", str(_framework_root()))
    init_scaffold.run_all()
    report2 = init_scaffold.run_all()
    # Second run creates nothing new
    assert report2["created"] == []


# =================================================================
# helpers
# =================================================================

def _framework_root() -> Path:
    """Return the real mb-framework repo root (for template resolution in tests)."""
    # We're at scripts/v2_1/tests/test_init_scaffold.py — parents[3] is the repo root
    return Path(__file__).resolve().parents[3]
