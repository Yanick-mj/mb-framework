"""Pipeline checkpoint: init, step tracking, pause/resume, archive.

Manages ``memory/session/pipeline-state.yaml`` — a machine-readable YAML
file that tracks pipeline progress across sessions. Enables chunked
execution (pause after N agents) and crash recovery (detect ``in_progress``
steps on restart).

Single-pipeline enforcement: only one pipeline may be active at a time.
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    import sys

    print(
        "\u26a0\ufe0f  mb-framework needs PyYAML.\nFix: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)

from scripts.v2_2 import _paths
from scripts.v2_2.memory import session_path
from scripts.v2_2.subagent_preamble import PREAMBLE_FILENAME

STATE_FILENAME = "pipeline-state.yaml"
VERSION = 1


class PipelineAlreadyActiveError(Exception):
    """Raised when ``init()`` is called while a pipeline is already active."""

    def __init__(self, pipeline_id: str, task: str):
        self.pipeline_id = pipeline_id
        self.task = task
        super().__init__(
            f"Active pipeline already exists (id: {pipeline_id}, task: {task}). "
            f"Resume it with /mb:resume or abandon it with /mb:pipeline abandon."
        )


def _state_path() -> Path:
    return session_path(STATE_FILENAME)


def _read_state() -> Optional[Dict[str, Any]]:
    path = _state_path()
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(
            f"\u26a0\ufe0f  Pipeline state corrupted: {path}\n"
            f"   Error: {exc}\n"
            f"   The file will be ignored. Run /mb:pipeline abandon to clean up,\n"
            f"   or delete {path} manually.",
            file=sys.stderr,
        )
        return None
    if not isinstance(data, dict):
        return None
    return data


def _write_state(state: Dict[str, Any]) -> Path:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(state, default_flow_style=False, sort_keys=False), encoding="utf-8")
    return path


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_current_step(state: Dict[str, Any]) -> int:
    """Return ``current_step`` index, raising if out of bounds."""
    idx = state["current_step"]
    pipeline = state["pipeline"]
    if idx < 0 or idx >= len(pipeline):
        raise IndexError(
            f"Pipeline step {idx} out of range (pipeline has {len(pipeline)} agents). "
            f"All agents may already be complete."
        )
    return idx


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init(
    task_original: str,
    classified_as: str,
    story_id: str,
    stage: str,
    agents: Sequence[Tuple[str, str]],
    chunk_size: int = 4,
) -> Dict[str, Any]:
    """Initialize a new pipeline state file.

    Parameters
    ----------
    task_original : str
        The original task description from the user.
    classified_as : str
        The task classification (e.g. ``full-stack-feature``).
    story_id : str
        Story ID (e.g. ``STU-058``), or empty string if none.
    stage : str
        Current project stage (``discovery``, ``mvp``, ``pmf``, ``scale``).
    agents : sequence of (agent_name, role) tuples
        Ordered pipeline agents.
    chunk_size : int
        How many agents to run before pausing for context preservation.

    Returns
    -------
    dict
        The newly created pipeline state.

    Raises
    ------
    PipelineAlreadyActiveError
        If a non-completed/non-failed pipeline already exists.
    ValueError
        If ``agents`` is empty or ``chunk_size`` < 1.
    """
    if not agents:
        raise ValueError("agents must not be empty")
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")

    existing = _read_state()
    if existing and existing.get("status") not in ("completed", "failed"):
        raise PipelineAlreadyActiveError(
            pipeline_id=existing.get("pipeline_id", "?"),
            task=existing.get("task", {}).get("original", "?"),
        )

    pipeline_id = _short_id()
    pipeline_steps = [
        {"agent": agent, "role": role, "status": "pending", "run_id": None}
        for agent, role in agents
    ]

    state: Dict[str, Any] = {
        "version": VERSION,
        "pipeline_id": pipeline_id,
        "status": "active",
        "created_at": _now_iso(),
        "task": {
            "original": task_original,
            "classified_as": classified_as,
            "story_id": story_id or "",
        },
        "stage": stage,
        "pipeline": pipeline_steps,
        "current_step": 0,
        "completed_count": 0,
        "total_count": len(pipeline_steps),
        "chunk_size": chunk_size,
        "paused": None,
        "resume_context": {
            "key_artifacts": [],
            "decisions_so_far": [],
            "open_unknowns": [],
        },
    }

    _write_state(state)
    return state


def mark_in_progress() -> Dict[str, Any]:
    """Mark the current step as ``in_progress`` before spawning the agent.

    Returns the updated state.
    """
    state = _read_state()
    if state is None:
        raise FileNotFoundError("No pipeline state found")

    idx = _get_current_step(state)
    state["pipeline"][idx]["status"] = "in_progress"
    _write_state(state)
    return state


def complete_step(run_id: Optional[str] = None) -> Dict[str, Any]:
    """Mark the current step as ``done`` and advance ``current_step``.

    Parameters
    ----------
    run_id : str, optional
        The run ID from runs.jsonl for traceability.
    """
    state = _read_state()
    if state is None:
        raise FileNotFoundError("No pipeline state found")

    idx = _get_current_step(state)
    state["pipeline"][idx]["status"] = "done"
    state["pipeline"][idx]["run_id"] = run_id
    state["completed_count"] += 1
    state["current_step"] = idx + 1
    _write_state(state)
    return state


def fail_step(error: str = "") -> Dict[str, Any]:
    """Mark the current step as ``failed`` and pause the pipeline."""
    state = _read_state()
    if state is None:
        raise FileNotFoundError("No pipeline state found")

    idx = _get_current_step(state)
    state["pipeline"][idx]["status"] = "failed"
    state["paused"] = {
        "reason": "agent_failure",
        "at_step": idx,
        "message": error or f"Agent {state['pipeline'][idx]['agent']} failed",
        "paused_at": _now_iso(),
    }
    _write_state(state)
    return state


def reset_current_step() -> Dict[str, Any]:
    """Reset the current step to ``pending`` for retry after crash/failure.

    Also clears any ``paused`` state so the pipeline can continue.
    """
    state = _read_state()
    if state is None:
        raise FileNotFoundError("No pipeline state found")

    idx = _get_current_step(state)
    state["pipeline"][idx]["status"] = "pending"
    state["pipeline"][idx]["run_id"] = None
    state["paused"] = None
    _write_state(state)
    return state


def skip_step() -> Dict[str, Any]:
    """Mark the current step as ``skipped`` and advance ``current_step``.

    Does NOT increment ``completed_count`` — skipped is not completed.
    Also clears any ``paused`` state.
    """
    state = _read_state()
    if state is None:
        raise FileNotFoundError("No pipeline state found")

    idx = _get_current_step(state)
    state["pipeline"][idx]["status"] = "skipped"
    state["current_step"] = idx + 1
    state["paused"] = None
    _write_state(state)
    return state


def pause(reason: str = "chunk_budget", message: str = "") -> Dict[str, Any]:
    """Pause the pipeline at the current step."""
    state = _read_state()
    if state is None:
        raise FileNotFoundError("No pipeline state found")

    state["paused"] = {
        "reason": reason,
        "at_step": state["current_step"],
        "message": message
        or f"Completed {state['completed_count']} agents, pausing for context preservation",
        "paused_at": _now_iso(),
    }
    _write_state(state)
    return state


def unpause() -> Dict[str, Any]:
    """Clear the paused state so the pipeline can continue."""
    state = _read_state()
    if state is None:
        raise FileNotFoundError("No pipeline state found")

    state["paused"] = None
    _write_state(state)
    return state


def should_pause() -> bool:
    """Return True if the pipeline should pause before the next agent.

    Heuristic: pause when ``completed_count > 0 AND completed_count %
    chunk_size == 0 AND remaining > 0``.
    """
    state = _read_state()
    if state is None:
        return False

    completed = state.get("completed_count", 0)
    total = state.get("total_count", 0)
    chunk_size = state.get("chunk_size", 4)
    remaining = total - completed

    if completed > 0 and completed % chunk_size == 0 and remaining > 0:
        return True
    return False


def update_resume_context(
    key_artifacts: Optional[List[str]] = None,
    decisions: Optional[List[str]] = None,
    open_unknowns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Append entries to ``resume_context`` for cross-session continuity.

    Called by the orchestrator after each agent completes, so that
    ``/mb:resume`` can reconstruct context without re-reading all files.
    """
    state = _read_state()
    if state is None:
        raise FileNotFoundError("No pipeline state found")

    ctx = state.get("resume_context", {})
    if key_artifacts:
        ctx.setdefault("key_artifacts", []).extend(key_artifacts)
    if decisions:
        ctx.setdefault("decisions_so_far", []).extend(decisions)
    if open_unknowns:
        ctx.setdefault("open_unknowns", []).extend(open_unknowns)

    state["resume_context"] = ctx
    _write_state(state)
    return state


def _finalize(end_status: str, timestamp_key: str) -> Optional[Path]:
    """Shared logic for archive and abandon: set status, rename file, clean preamble."""
    state = _read_state()
    if state is None:
        return None

    state["status"] = end_status
    state[timestamp_key] = _now_iso()
    _write_state(state)

    src = _state_path()
    pid = state.get("pipeline_id", "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    dest = src.parent / f"pipeline-state-{pid}-{ts}.yaml"
    src.rename(dest)

    preamble = session_path(PREAMBLE_FILENAME)
    if preamble.exists():
        preamble.unlink()

    return dest


def archive() -> Optional[Path]:
    """Archive the pipeline state file as completed and clean up session artifacts."""
    return _finalize("completed", "completed_at")


def abandon() -> Optional[Path]:
    """Mark the pipeline as failed/abandoned and archive it."""
    return _finalize("failed", "abandoned_at")


def render_status() -> str:
    """Render a human-readable status of the current pipeline."""
    state = _read_state()
    if state is None:
        return "No active pipeline."

    lines = []
    pid = state.get("pipeline_id", "?")
    task = state.get("task", {}).get("original", "?")
    classified = state.get("task", {}).get("classified_as", "?")
    completed = state.get("completed_count", 0)
    total = state.get("total_count", 0)
    paused = state.get("paused")

    lines.append(f"Pipeline {pid}: {task}")
    lines.append(f"  Class: {classified}")
    lines.append(f"  Progress: {completed}/{total} agents")
    lines.append(f"  Status: {'PAUSED' if paused else state.get('status', '?')}")

    if paused:
        lines.append(f"  Pause reason: {paused.get('reason', '?')}")
        lines.append(f"  Message: {paused.get('message', '')}")

    lines.append("")
    lines.append("  Pipeline steps:")
    for i, step in enumerate(state.get("pipeline", [])):
        marker = ">" if i == state.get("current_step", -1) else " "
        status_icon = {
            "pending": "  ",
            "in_progress": ">>",
            "done": "OK",
            "failed": "XX",
            "skipped": "--",
        }.get(step["status"], "??")
        lines.append(
            f"  {marker} [{status_icon}] {i + 1}. {step['agent']} ({step['role']})"
        )

    return "\n".join(lines)


def get_state() -> Optional[Dict[str, Any]]:
    """Return the current pipeline state, or None."""
    return _read_state()
