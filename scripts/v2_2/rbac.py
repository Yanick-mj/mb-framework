"""Stage-aware RBAC checker — agent × tool × action.

Reads ``{cwd}/memory/permissions.yaml``:

    permissions:
      fe-dev:
        - tool: vercel
          actions: [deploy-preview]         # flat list = applies at every stage
      be-dev:
        - tool: supabase
          actions:
            discovery: []
            mvp: [read, write]
            pmf: [read]
            scale: [read]

Stage-aware defaults when the file is ABSENT:
  - discovery, mvp → ALLOW (permissive, move fast)
  - pmf, scale     → DENY (strict, safety first)

Once the file EXISTS, it is strictly enforced at every stage. Missing
(agent, tool) pairs = DENIED, even at mvp.

Every call to check() writes an audit entry to
``memory/tool-audit.jsonl`` unless ``audit=False`` is passed.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

try:
    import yaml
except ImportError:  # pragma: no cover
    import sys
    print(
        "⚠️  mb-framework needs PyYAML but it's not installed.\n"
        "\n"
        "Fix: pip install pyyaml\n",
        file=sys.stderr,
    )
    sys.exit(2)

from scripts.v2_2 import _paths


PERMISSIVE_STAGES = {"discovery", "mvp"}


@dataclass
class Decision:
    allowed: bool
    reason: str


def _current_stage() -> str:
    """Read mb-stage.yaml's `stage` field. Default 'scale' (safest)."""
    stage_file = _paths.project_root() / "mb-stage.yaml"
    if not stage_file.exists():
        return "scale"
    try:
        data = yaml.safe_load(stage_file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return "scale"
    if not isinstance(data, dict):
        return "scale"
    return str(data.get("stage", "scale"))


def load() -> Dict[str, Any]:
    """Load permissions config. Returns {} on missing, malformed, or
    unexpected structure."""
    path = _paths.permissions_file()
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}
    perms = data.get("permissions", {})
    if not isinstance(perms, dict):
        return {}
    return perms


def _extract_actions(spec_actions: Any, stage: str) -> List[str]:
    """Normalize the 'actions' value for a given stage.

    Accepts either:
      - flat list: [a, b, c] → applies to all stages
      - stage-keyed dict: {mvp: [...], pmf: [...]}
    """
    if isinstance(spec_actions, list):
        return [a for a in spec_actions if isinstance(a, str)]
    if isinstance(spec_actions, dict):
        stage_actions = spec_actions.get(stage, [])
        if isinstance(stage_actions, list):
            return [a for a in stage_actions if isinstance(a, str)]
    return []


def check(
    agent: str,
    tool: str,
    action: str,
    *,
    audit: bool = True,
) -> Decision:
    """Check whether `agent` may perform `action` on `tool`.

    Stage-aware default when permissions.yaml is absent:
      - discovery / mvp: PERMISSIVE (allow)
      - pmf / scale:     STRICT (deny)

    Once permissions.yaml exists, it's enforced at every stage (opt-in to
    strict enforcement — useful in discovery/mvp too).

    Writes an audit entry unless audit=False.
    """
    perms = load()
    stage = _current_stage()

    if not perms:
        if stage in PERMISSIVE_STAGES:
            decision = Decision(
                allowed=True,
                reason=(
                    f"{agent} → {tool}:{action} ALLOWED (permissive default at "
                    f"stage={stage}, no permissions.yaml configured)"
                ),
            )
        else:
            decision = Decision(
                allowed=False,
                reason=(
                    f"{agent} → {tool}:{action} DENIED at stage={stage}: "
                    f"no permissions configured (memory/permissions.yaml "
                    f"missing or empty). At stage ≥ pmf, explicit permissions "
                    f"are required."
                ),
            )
    else:
        agent_perms = perms.get(agent, [])
        if not isinstance(agent_perms, list):
            agent_perms = []
        tool_entries = [
            e for e in agent_perms
            if isinstance(e, dict) and e.get("tool") == tool
        ]
        if not tool_entries:
            decision = Decision(
                allowed=False,
                reason=(
                    f"{agent} → {tool}:{action} DENIED: agent has no "
                    f"permissions on tool {tool!r}"
                ),
            )
        else:
            allowed_actions: List[str] = []
            for entry in tool_entries:
                allowed_actions.extend(_extract_actions(entry.get("actions"), stage))
            if action in allowed_actions:
                decision = Decision(
                    allowed=True,
                    reason=(
                        f"{agent} → {tool}:{action} ALLOWED at stage={stage}"
                    ),
                )
            else:
                decision = Decision(
                    allowed=False,
                    reason=(
                        f"{agent} → {tool}:{action} DENIED at stage={stage}: "
                        f"action not allowed "
                        f"(allowed: {allowed_actions or 'none'})"
                    ),
                )

    if audit:
        _append_audit(
            agent=agent, tool=tool, action=action,
            allowed=decision.allowed, reason=decision.reason,
        )
    return decision


def audit(
    *,
    agent: str,
    tool: str,
    action: str,
    allowed: bool,
    reason: str,
) -> str:
    """Public helper to append an audit entry (useful for override flows).

    Returns the audit_id (12 hex chars).
    """
    return _append_audit(
        agent=agent, tool=tool, action=action,
        allowed=allowed, reason=reason,
    )


def _append_audit(
    *,
    agent: str,
    tool: str,
    action: str,
    allowed: bool,
    reason: str,
) -> str:
    log = _paths.tool_audit_log()
    log.parent.mkdir(parents=True, exist_ok=True)
    audit_id = uuid.uuid4().hex[:12]
    entry = {
        "audit_id": audit_id,
        "ts": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "agent": agent,
        "tool": tool,
        "action": action,
        "allowed": allowed,
        "reason": reason,
    }
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return audit_id


def render_audit(limit: int = 10) -> str:
    """Human-readable recent audit entries (newest first)."""
    log = _paths.tool_audit_log()
    if not log.exists():
        return "🔒 No tool audit entries yet."
    raw_lines = log.read_text(encoding="utf-8").strip().splitlines()
    entries: List[dict] = []
    for l in raw_lines[-limit * 2:]:  # buffer for corrupted lines
        if not l.strip():
            continue
        try:
            entries.append(json.loads(l))
        except json.JSONDecodeError:
            continue
    entries.reverse()
    entries = entries[:limit]

    if not entries:
        return "🔒 No tool audit entries yet."

    out = [f"🔒 Last {len(entries)} audit entry(ies)", ""]
    for e in entries:
        icon = "✅" if e.get("allowed") else "🔴"
        ts = str(e.get("ts", ""))[:19]
        out.append(
            f"  {icon}  {ts}  "
            f"{e.get('agent', '?'):<12} "
            f"{e.get('tool', '?'):<12} "
            f"{e.get('action', '?')}"
        )
        out.append(f"    └─ {e.get('reason', '')}")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 5 and sys.argv[1] == "check":
        d = check(sys.argv[2], sys.argv[3], sys.argv[4])
        print(d.reason)
        sys.exit(0 if d.allowed else 1)
    # Default: print the audit log
    print(render_audit())
