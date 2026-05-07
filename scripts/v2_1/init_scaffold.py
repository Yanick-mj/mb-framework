"""Deterministic scaffolder for /mb:init.

Detects the stack from common manifest files, creates the mb directory
skeleton (_backlog/, _mb-output/, memory/_session/), and generates
_roadmap.md + CLAUDE.md from templates on first run. Idempotent: re-running
never overwrites existing user content.

Pre-v2.4 projects with _bmad-output/ keep working — the read fallback in
scripts.v2_2._paths.output_root() routes reads there. Only NEW projects
get the new _mb-output/ name.

Used by the `/mb:init` command — Claude Code invokes this script then does
higher-level pattern detection (hooks, API, DB) with its own tools.
"""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import List, Optional

from scripts.v2_2._paths import OUTPUT_DIRNAME

try:
    import yaml  # noqa: F401 — imported for template consistency w/ other modules
except ImportError:  # pragma: no cover
    import sys
    print(
        "⚠️  mb-framework needs PyYAML.\nFix: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)


# Tool aliases detected in package.json deps (one string → one label)
_NODE_TOOL_MATCHERS = [
    ("vitest", "vitest"),
    ("jest", "jest"),
    ("@playwright/test", "playwright"),
    ("playwright", "playwright"),
    ("tailwindcss", "tailwind"),
    ("typescript", "typescript"),
    ("@supabase/supabase-js", "supabase"),
    ("prisma", "prisma"),
    ("drizzle-orm", "drizzle"),
]


def detect_stack() -> dict:
    """Inspect project root manifests, return a dict describing the stack.

    Returns:
        {
            "stack": "node" | "rust" | "go" | "python" | "unknown",
            "framework": "next.js" | "react+vite" | "react" | "expo" | ...,
            "tools": ["typescript", "vitest", "tailwind", "supabase", ...],
            "monorepo": None | "turbo" | "lerna" | "pnpm-workspaces" | "yarn-workspaces",
        }

    Gracefully handles malformed manifests (returns partial info, never raises).
    """
    root = Path.cwd()
    info: dict = {"stack": "unknown", "framework": None, "tools": [], "monorepo": None}

    # Supabase-as-filesystem detection (in addition to deps-based detection below)
    if (root / "supabase").is_dir():
        if "supabase" not in info["tools"]:
            info["tools"].append("supabase")

    pkg_json = root / "package.json"
    if pkg_json.exists():
        info["stack"] = "node"
        try:
            pkg = json.loads(pkg_json.read_text())
        except (json.JSONDecodeError, OSError):
            return info  # stack=node, no framework/tools

        # Monorepo detection (top of info so downstream can skip framework detect)
        if (root / "turbo.json").exists():
            info["monorepo"] = "turbo"
        elif (root / "lerna.json").exists():
            info["monorepo"] = "lerna"
        elif pkg.get("workspaces"):
            # pnpm uses pnpm-workspace.yaml; yarn/npm use workspaces in package.json
            if (root / "pnpm-workspace.yaml").exists():
                info["monorepo"] = "pnpm-workspaces"
            else:
                info["monorepo"] = "yarn-workspaces"
        elif (root / "pnpm-workspace.yaml").exists():
            info["monorepo"] = "pnpm-workspaces"

        deps = {**(pkg.get("dependencies") or {}),
                **(pkg.get("devDependencies") or {})}

        # Framework detection (priority order matters)
        if "next" in deps:
            info["framework"] = "next.js"
        elif "expo" in deps or "react-native" in deps:
            info["framework"] = "expo" if "expo" in deps else "react-native"
        elif "react" in deps and "vite" in deps:
            info["framework"] = "react+vite"
        elif "react" in deps:
            info["framework"] = "react"
        elif "express" in deps or "fastify" in deps:
            info["framework"] = "express" if "express" in deps else "fastify"
        elif "vue" in deps:
            info["framework"] = "vue"

        for dep_key, label in _NODE_TOOL_MATCHERS:
            if dep_key in deps and label not in info["tools"]:
                info["tools"].append(label)
        return info

    if (root / "Cargo.toml").exists():
        info["stack"] = "rust"
        return info

    if (root / "go.mod").exists():
        info["stack"] = "go"
        return info

    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        info["stack"] = "python"
        return info

    return info


# =================================================================
# Directory scaffold
# =================================================================

_REQUIRED_DIRS = [
    "_backlog",
    f"{OUTPUT_DIRNAME}/deliverables",
    f"{OUTPUT_DIRNAME}/implementation-artifacts/stories",
    "memory/_session",
]


def scaffold_dirs() -> List[str]:
    """Create all mb-expected directories with .gitkeep placeholders.

    Returns the list of directories NEWLY created (empty list on 2nd run).
    """
    created: List[str] = []
    root = Path.cwd()
    for rel in _REQUIRED_DIRS:
        target = root / rel
        was_new = not target.exists()
        target.mkdir(parents=True, exist_ok=True)
        gitkeep = target / ".gitkeep"
        if was_new and not gitkeep.exists():
            gitkeep.write_text("")
            created.append(str(target))
    return created


# =================================================================
# Roadmap scaffold
# =================================================================

def _find_framework_path() -> Path:
    """Resolve the mb-framework install root. Prefer MB_FRAMEWORK_PATH env,
    fallback to .claude/mb in cwd."""
    env = os.environ.get("MB_FRAMEWORK_PATH")
    if env and Path(env).exists():
        return Path(env)
    local = Path.cwd() / ".claude" / "mb"
    if local.exists():
        return local
    raise FileNotFoundError(
        "mb-framework not found. Set MB_FRAMEWORK_PATH or install at .claude/mb."
    )


def scaffold_roadmap(force: bool = False) -> Optional[Path]:
    """Copy templates/roadmap.md to ./_roadmap.md if absent.

    Returns the target path if created, None if preserved existing.
    """
    target = Path.cwd() / "_roadmap.md"
    if target.exists() and not force:
        return None
    framework = _find_framework_path()
    template = framework / "templates" / "roadmap.md"
    target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    return target


# =================================================================
# CLAUDE.md scaffold
# =================================================================

def scaffold_claude_md(stack_info: dict, force: bool = False) -> Optional[Path]:
    """Generate CLAUDE.md from templates/CLAUDE.md.template with placeholders
    filled from stack_info.

    Returns the target path if created, None if preserved existing.
    """
    target = Path.cwd() / "CLAUDE.md"
    if target.exists() and not force:
        return None
    framework = _find_framework_path()
    template_file = framework / "templates" / "CLAUDE.md.template"
    content = template_file.read_text(encoding="utf-8")

    replacements = {
        "{PROJECT_NAME}": Path.cwd().name,
        "{STACK}": stack_info.get("stack", "unknown"),
        "{FRAMEWORK}": stack_info.get("framework") or "<none detected>",
        "{TOOLS}": ", ".join(stack_info.get("tools", [])) or "none detected",
        "{MONOREPO}": stack_info.get("monorepo") or "single-package",
        "{DATE}": date.today().isoformat(),
    }
    for key, value in replacements.items():
        content = content.replace(key, value)
    target.write_text(content, encoding="utf-8")
    return target


# =================================================================
# First backlog story
# =================================================================

def seed_first_backlog_story(stack_info: dict) -> Optional[Path]:
    """Create _backlog/STU-1-initial-setup.md, only if _backlog/ is empty of .md files.

    Returns the target path if created, None if backlog non-empty.
    """
    backlog_dir = Path.cwd() / "_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    existing_md = [f for f in backlog_dir.glob("*.md")]
    if existing_md:
        return None

    target = backlog_dir / "STU-1-initial-setup.md"

    ac_lines = [
        "- [ ] Read `_roadmap.md` and fill in Mission + Current Stage + Next Milestone",
        "- [ ] Read `CLAUDE.md` and add project-specific conventions (naming, commits)",
    ]
    tools = stack_info.get("tools", [])
    if "typescript" in tools:
        ac_lines.append("- [ ] Verify `tsc --noEmit` runs clean")
    if "vitest" in tools or "jest" in tools:
        test_cmd = "vitest" if "vitest" in tools else "jest"
        ac_lines.append(f"- [ ] Verify `npx {test_cmd}` runs (or `pnpm test`)")
    if "playwright" in tools:
        ac_lines.append("- [ ] Run `npx playwright test` to confirm e2e baseline")
    ac_lines.append("- [ ] Mark this story as done (`status: done`) after verification")

    framework = stack_info.get("framework") or "none"
    tools_str = ", ".join(tools) or "none"

    content = f"""---
story_id: STU-1
title: Initial mb setup + project baseline
priority: high
status: todo
created: {date.today().isoformat()}
---

# Initial mb setup + project baseline

## Why

First story in any mb-framework project. Confirms the setup works and
establishes the baseline for future work.

## Acceptance criteria

{chr(10).join(ac_lines)}

## Notes

Generated by `/mb:init` on {date.today().isoformat()}.

Detected environment:
- Stack: {stack_info.get("stack")}
- Framework: {framework}
- Tools: {tools_str}

Once this story is `status: done`, delete the file or move it out of `_backlog/`.
"""
    target.write_text(content, encoding="utf-8")
    return target


# =================================================================
# Top-level orchestrator
# =================================================================

def run_all() -> dict:
    """Orchestrate stack detection + directory + templates + seed story.

    Idempotent: already-existing files are preserved. Second run creates nothing.

    Returns a report dict:
        {
            "stack": {...},
            "created": [<list of str paths>],
            "preserved": [<list of str paths that were already there>],
        }
    """
    stack_info = detect_stack()
    created: List[str] = []
    preserved: List[str] = []

    created.extend(scaffold_dirs())

    r = scaffold_roadmap()
    if r is not None:
        created.append(str(r))
    else:
        preserved.append(str(Path.cwd() / "_roadmap.md"))

    c = scaffold_claude_md(stack_info)
    if c is not None:
        created.append(str(c))
    else:
        preserved.append(str(Path.cwd() / "CLAUDE.md"))

    s = seed_first_backlog_story(stack_info)
    if s is not None:
        created.append(str(s))

    return {
        "stack": stack_info,
        "created": created,
        "preserved": preserved,
    }


def render(report: dict) -> str:
    """Human-readable rendering of the run_all() report."""
    from scripts.v2_1._emoji import tag
    t = tag("projects")
    stack = report["stack"]
    lines = [f"{t} mb init scaffold report", ""]
    lines.append(f"  Stack:     {stack.get('stack')}")
    lines.append(f"  Framework: {stack.get('framework') or '<none detected>'}")
    lines.append(f"  Tools:     {', '.join(stack.get('tools', [])) or 'none detected'}")
    lines.append("")
    if report["created"]:
        lines.append(f"  Created {len(report['created'])} artifact(s):")
        for p in report["created"]:
            lines.append(f"    + {p}")
    if report["preserved"]:
        lines.append("")
        lines.append(f"  Preserved {len(report['preserved'])} existing artifact(s):")
        for p in report["preserved"]:
            lines.append(f"    = {p}")
    if not report["created"] and not report["preserved"]:
        lines.append("  (nothing to do — project already scaffolded)")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render(run_all()))
