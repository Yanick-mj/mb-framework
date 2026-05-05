---
story_id: STU-P2S5.3
title: Launch agent pipeline from chat
priority: high
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint5
---

# Launch agent pipeline from chat

## Why

The builder says "lance ce ticket" and expects the AI agent to start working on it. This bridges chat → agent execution → streamed feedback.

## Scope

**In:**
- "Lance {story_id}" intent → spawns agent subprocess
- Agent runs in background (non-blocking for chat)
- Subprocess: `claude --project-dir {path} --story {id}` (or equivalent)
- Process tracked: PID stored, status queryable
- Kill/cancel support: "annule le run" → SIGTERM

**Out:**
- Full agent orchestration (existing mb pipeline handles this)
- Agent selection logic (use default be-dev for now)
- Multi-agent coordination (Sprint 6)

## Acceptance criteria

- [ ] "Lance STU-P2S1.1" → subprocess spawned
- [ ] Chat confirms: "Agent started on STU-P2S1.1..."
- [ ] Process PID tracked in memory (queryable)
- [ ] "Status du run ?" → "Running for 45s" or "Completed"
- [ ] "Annule" → SIGTERM sent, process killed, confirmed
- [ ] Subprocess failure → error message in chat
- [ ] Max 3 concurrent agent runs (queue beyond that)

## Tech requirements

- **Subprocess:** `asyncio.create_subprocess_exec()` with stdout/stderr pipes
- **Tracking:** dict `{story_id: {"pid": int, "started": datetime, "status": str}}`
- **Endpoint:** `POST /api/agent/launch` body: `{"story_id": "STU-P2S1.1"}`
- **Cancel:** `POST /api/agent/{story_id}/cancel` → sends SIGTERM
- **Status:** `GET /api/agent/{story_id}/status`
- **Limit:** max 3 concurrent processes, 4th returns 429

## Designer requirements

- N/A (backend — UI feedback handled in S5.4)

## TDD

```python
# tests/dashboard/test_agent_launch.py

def test_launch_spawns_subprocess():
    """POST /api/agent/launch → subprocess started (mock)"""

def test_launch_returns_tracking_info():
    """Response includes story_id, pid, started timestamp"""

def test_cancel_sends_sigterm():
    """POST cancel → process receives SIGTERM"""

def test_max_concurrent_limit():
    """4th launch attempt → 429 Too Many Requests"""

def test_status_returns_running_state():
    """GET status while running → {"status": "running", "elapsed": ...}"""

def test_completed_process_status():
    """After subprocess exits → status becomes "completed" """
```
