"""Idempotent merge of the mb-framework hooks into .claude/settings.json.

Called by install.sh. Safe to re-run: if the mb-orchestrator-autoinvoke
hook is already present, nothing changes. If the user added their own
UserPromptSubmit hooks, they are preserved.

Marker used to identify our hook: the command string contains
"orchestrator-autoinvoke.sh".
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


HOOK_MARKER = "orchestrator-autoinvoke.sh"


def _desired_entry(mb_dir_abs: str) -> dict:
    return {
        "hooks": [
            {
                "type": "command",
                "command": f"bash {mb_dir_abs}/hooks/orchestrator-autoinvoke.sh",
            }
        ]
    }


def _entry_matches_marker(entry: dict) -> bool:
    for h in entry.get("hooks", []):
        if isinstance(h, dict) and HOOK_MARKER in str(h.get("command", "")):
            return True
    return False


def merge(settings_path: Path, mb_dir_abs: str) -> str:
    """Merge the hook into settings.json. Returns 'added' | 'updated' | 'noop'."""
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text() or "{}")
        except json.JSONDecodeError:
            print(
                f"  ⚠️  {settings_path} has invalid JSON — not touching it.",
                file=sys.stderr,
            )
            return "noop"
    else:
        data = {}

    if not isinstance(data, dict):
        print(f"  ⚠️  {settings_path} is not a JSON object — not touching it.", file=sys.stderr)
        return "noop"

    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        print(f"  ⚠️  settings.json 'hooks' field is not an object — not touching.", file=sys.stderr)
        return "noop"

    ups_list = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(ups_list, list):
        print(f"  ⚠️  'UserPromptSubmit' is not a list — not touching.", file=sys.stderr)
        return "noop"

    desired = _desired_entry(mb_dir_abs)
    desired_cmd = desired["hooks"][0]["command"]

    # If an mb-orchestrator entry already exists, check whether the command
    # path matches the current mb_dir (user may have relocated the submodule).
    for i, entry in enumerate(ups_list):
        if isinstance(entry, dict) and _entry_matches_marker(entry):
            existing_cmd = entry["hooks"][0].get("command", "")
            if existing_cmd == desired_cmd:
                return "noop"
            ups_list[i] = desired
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(json.dumps(data, indent=2) + "\n")
            return "updated"

    ups_list.append(desired)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(data, indent=2) + "\n")
    return "added"


def remove(settings_path: Path) -> str:
    """Remove the mb-orchestrator-autoinvoke entry. Returns 'removed' | 'noop'."""
    if not settings_path.exists():
        return "noop"
    try:
        data = json.loads(settings_path.read_text() or "{}")
    except json.JSONDecodeError:
        return "noop"

    hooks = data.get("hooks", {})
    ups_list = hooks.get("UserPromptSubmit", [])
    if not isinstance(ups_list, list):
        return "noop"

    new_list = [
        e for e in ups_list if not (isinstance(e, dict) and _entry_matches_marker(e))
    ]
    if len(new_list) == len(ups_list):
        return "noop"

    if new_list:
        hooks["UserPromptSubmit"] = new_list
    else:
        hooks.pop("UserPromptSubmit", None)

    if not hooks:
        data.pop("hooks", None)

    if data:
        settings_path.write_text(json.dumps(data, indent=2) + "\n")
    else:
        settings_path.unlink()
    return "removed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mb_dir_abs", help="Absolute path to .claude/mb")
    parser.add_argument(
        "--settings",
        default=".claude/settings.json",
        help="Path to settings.json (default: .claude/settings.json)",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove the hook instead of installing it",
    )
    args = parser.parse_args()

    path = Path(args.settings)
    if args.remove:
        print(remove(path))
    else:
        print(merge(path, args.mb_dir_abs))
