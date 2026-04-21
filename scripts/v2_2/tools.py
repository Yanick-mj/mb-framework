"""External tool catalog for mb v2.2.

Reads ``{cwd}/tools/_catalog.yaml`` which lists tools the project integrates
with (github, supabase, vercel, stripe, etc.) and the actions each tool
supports.

The catalog is consulted by ``rbac.py`` to validate whether an agent is
allowed to invoke a specific ``(tool, action)`` at the current project stage.

Design: strict — entries missing a ``name`` are silently dropped (v2.1.2 M10
pattern). Malformed YAML returns an empty list rather than crashing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover — only hit when pyyaml missing
    import sys
    print(
        "⚠️  mb-framework needs PyYAML but it's not installed.\n"
        "\n"
        "Fix: pip install pyyaml\n",
        file=sys.stderr,
    )
    sys.exit(2)

from scripts.v2_2 import _paths


def load() -> List[Dict[str, Any]]:
    """Load the tool catalog.

    Returns an empty list if the file is missing, cannot parse as YAML, has
    an unexpected top-level structure, or 'tools' is not a list.
    """
    path = _paths.tools_catalog()
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict):
        return []
    items = data.get("tools", [])
    if not isinstance(items, list):
        return []
    # Strict: drop entries that aren't dicts OR lack a non-empty name
    valid: List[Dict[str, Any]] = []
    for t in items:
        if not isinstance(t, dict):
            continue
        name = t.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        valid.append(t)
    return valid


def get_tool(name: str) -> Optional[Dict[str, Any]]:
    """Lookup a single tool entry by name. None if not found."""
    for t in load():
        if t.get("name") == name:
            return t
    return None


def render() -> str:
    """Human-readable catalog listing for ``/mb:tool list``."""
    # Prefer v2.1 emoji tag if available; fall back to a literal emoji
    try:
        from scripts.v2_1._emoji import tag
        t = tag("tools") if hasattr(tag, "__call__") else "🔧"
        # _emoji.tag doesn't currently know "tools" — ensure we always get 🔧
        if t in ("", "[TOOLS]"):
            pass  # honor MB_NO_EMOJI=1 convention if tag returns ASCII form
        elif not t:
            t = "🔧"
    except Exception:
        t = "🔧"

    items = load()
    if not items:
        return (
            f"🔧 No tools registered.\n"
            f"Add entries to tools/_catalog.yaml "
            f"(see templates/tool-definition.md)."
        )
    lines = [f"🔧 {len(items)} tool(s) registered", ""]
    for entry in items:
        actions = entry.get("actions") or []
        if not actions:
            actions_str = "(no actions)"
        else:
            actions_str = ", ".join(str(a) for a in actions)
        lines.append(f"  {entry['name']:<15} {actions_str}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
