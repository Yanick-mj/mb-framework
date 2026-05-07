"""Shared path helpers for v2.2 modules.

Centralizes ``Path.cwd() / ...`` calls so a single cwd change in tests
propagates everywhere, and refactoring the layout later is a one-edit job.

Paths are computed relative to the current working directory (the project
root where `/mb:*` commands run from).
"""
from __future__ import annotations

from pathlib import Path


# v2.4 — independence cut from BMAD naming.
# All mb output (stories, deliverables, sprint status) lives under OUTPUT_DIRNAME.
# Projects created before v2.4 used LEGACY_OUTPUT_DIRNAME; we read from it
# transparently so they keep working. Fallback dropped at v2.5.
OUTPUT_DIRNAME = "_mb-output"
LEGACY_OUTPUT_DIRNAME = "_bmad-output"


def project_root() -> Path:
    """The project root is always the current working directory for mb commands."""
    return Path.cwd()


def output_root_for(project: Path) -> Path:
    """Output directory for a specific project root.

    Used by the dashboard which inspects multiple projects, each with its
    own root path. ``output_root()`` is the single-project shorthand.
    """
    new = project / OUTPUT_DIRNAME
    legacy = project / LEGACY_OUTPUT_DIRNAME
    if new.exists():
        return new
    if legacy.exists():
        return legacy
    return new


def output_root() -> Path:
    """Project's mb output directory (current project = ``Path.cwd()``).

    Default: ``_mb-output/``. Falls back to ``_bmad-output/`` for projects that
    haven't migrated yet (read-compat). New artifacts are always written under
    ``_mb-output/``. The fallback is removed at v2.5.
    """
    return output_root_for(project_root())


def deliverables_root_for(project: Path) -> Path:
    return output_root_for(project) / "deliverables"


def deliverables_root() -> Path:
    return deliverables_root_for(project_root())


def sprint_status_file_for(project: Path) -> Path:
    return output_root_for(project) / "implementation-artifacts" / "sprint-status.yaml"


def sprint_status_file() -> Path:
    return sprint_status_file_for(project_root())


def stories_root_for(project: Path) -> Path:
    return output_root_for(project) / "implementation-artifacts" / "stories"


def memory_root() -> Path:
    return project_root() / "memory"


def tools_catalog() -> Path:
    return project_root() / "tools" / "_catalog.yaml"


def tools_dir() -> Path:
    return project_root() / "tools"


def permissions_file() -> Path:
    return memory_root() / "permissions.yaml"


def tool_audit_log() -> Path:
    return memory_root() / "tool-audit.jsonl"


def skills_registry() -> Path:
    return memory_root() / "skills-registry.yaml"


def skills_dir(tier: str = "") -> Path:
    base = project_root() / "skills"
    if tier:
        return base / tier
    return base


def stories_root() -> Path:
    return stories_root_for(project_root())


def backlog_dir() -> Path:
    return project_root() / "_backlog"


def claude_skills_dir() -> Path:
    """Where Claude Code loads composed SKILL.md files from."""
    return project_root() / ".claude" / "skills"


def claude_skill_rejections_log() -> Path:
    """Runtime append log for skills Claude Code refused to load."""
    return memory_root() / "claude-skill-rejections.jsonl"
