"""Emoji + ASCII fallback for render outputs.

When MB_NO_EMOJI=1 is set (e.g. legacy Windows cmd, pipe to grep, CI logs),
the render functions use ASCII tag prefixes instead of emoji.
"""
from __future__ import annotations

import os


EMOJI_MAP = {
    "projects": ("📁", "[PROJECTS]"),
    "backlog":  ("📋", "[BACKLOG]"),
    "deliverables": ("📦", "[DELIVERABLES]"),
    "runs":     ("🏃", "[RUNS]"),
    "tree":     ("🌲", "[TREE]"),
    "warning":  ("⚠️ ", "[WARN]"),
}


def tag(name: str) -> str:
    """Return the emoji or ASCII tag for a render category.

    Usage:
        from scripts.v2_1 import _emoji
        lines = [f"{_emoji.tag('projects')} 3 mb project(s)"]
    """
    emoji, ascii_ = EMOJI_MAP.get(name, ("", ""))
    if os.environ.get("MB_NO_EMOJI", "").strip() in ("1", "true", "yes"):
        return ascii_
    return emoji
