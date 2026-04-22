"""Layered memory accessors for mb v2.2.

Layers:
    memory/project/              — long-term project state (mission, codebase-index)
    memory/agents/{agent}/       — per-agent state (instructions, runs.jsonl)
    memory/stories/{story_id}/   — per-story state (handoff, context)
    memory/session/              — ephemeral current-turn state

Features I (/mb:inbox) and J (/mb:board) and the run-summary writer all
consume these paths. Centralizing here avoids every feature re-inventing
"what's the right spot for this file".
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from scripts.v2_2 import _paths


VALID_LAYERS = {"project", "agents", "stories", "session"}


def project_path(filename: str) -> Path:
    return _paths.memory_root() / "project" / filename


def agent_path(agent: str, filename: str) -> Path:
    return _paths.memory_root() / "agents" / agent / filename


def story_path(story: str, filename: str) -> Path:
    return _paths.memory_root() / "stories" / story / filename


def session_path(filename: str) -> Path:
    return _paths.memory_root() / "session" / filename


def _resolve(
    layer: str,
    filename: str,
    agent: Optional[str] = None,
    story: Optional[str] = None,
) -> Path:
    if layer == "project":
        return project_path(filename)
    if layer == "agents":
        if not agent:
            raise ValueError("layer=agents requires agent=...")
        return agent_path(agent, filename)
    if layer == "stories":
        if not story:
            raise ValueError("layer=stories requires story=...")
        return story_path(story, filename)
    if layer == "session":
        return session_path(filename)
    raise ValueError(
        f"Invalid layer {layer!r}. Must be one of {sorted(VALID_LAYERS)}"
    )


def write(
    layer: str,
    filename: str,
    content: str,
    agent: Optional[str] = None,
    story: Optional[str] = None,
) -> Path:
    """Write content to the given layer file, creating parents as needed."""
    target = _resolve(layer, filename, agent=agent, story=story)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def read(
    layer: str,
    filename: str,
    agent: Optional[str] = None,
    story: Optional[str] = None,
) -> Optional[str]:
    """Return file content, or None if the target does not exist."""
    target = _resolve(layer, filename, agent=agent, story=story)
    if not target.exists():
        return None
    return target.read_text(encoding="utf-8")


def append(
    layer: str,
    filename: str,
    content: str,
    agent: Optional[str] = None,
    story: Optional[str] = None,
) -> Path:
    """Append content to a layer file. Useful for logs and notes."""
    target = _resolve(layer, filename, agent=agent, story=story)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(content)
    return target
