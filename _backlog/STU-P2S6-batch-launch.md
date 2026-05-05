---
story_id: STU-P2S6.3
title: Batch agent launch
priority: high
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint6
parent_story: STU-P2S5.3
---

# Batch agent launch

## Why

The builder selects 3 tickets and says "lance-les". Three agents run in parallel and the builder comes back later to validate results.

## Scope

**In:**
- Action bar button: "Launch agents" (when stories selected)
- `POST /api/agent/batch` body: `{"story_ids": [...]}`
- Spawns up to 3 subprocesses in parallel (respects max concurrency)
- Queue stories beyond limit (FIFO)
- Batch status view: shows progress per story

**Out:**
- Agent coordination (each runs independently)
- Dependency resolution between stories
- Cost estimation before launch

## Acceptance criteria

- [ ] "Launch agents" button in action bar when ≥1 selected
- [ ] Click → confirmation: "Launch agents for 3 stories?"
- [ ] Confirm → subprocesses spawned (up to 3 parallel)
- [ ] 4+ stories → first 3 launch, rest queued
- [ ] Queued stories auto-launch when slot frees up
- [ ] Batch status: per-story progress (pending/running/done/failed)
- [ ] All done → notification in chat: "3/3 agents completed"

## Tech requirements

- **Endpoint:** `POST /api/agent/batch` body: `{"story_ids": [...]}`
- **Queue:** `asyncio.Queue` with max 3 workers
- **Worker:** coroutine that pulls from queue, spawns subprocess, reports completion
- **Status:** `GET /api/agent/batch/{batch_id}/status`
- **Notification:** push SSE event to chat when batch completes
- **Isolation:** each subprocess gets its own working directory context

## Designer requirements

- Launch button: rocket icon 🚀 + "Launch" text
- Confirmation: same pattern as chat confirmations (amber card)
- Batch progress: mini cards per story with status icon (⏳🔄✅❌)
- Queue indicator: "2 queued, 1 running" in action bar
- Completion: green banner "All agents completed" with link to results

## TDD

```python
# tests/dashboard/test_batch_launch.py

def test_batch_launch_spawns_processes():
    """POST batch with 3 IDs → 3 subprocesses started"""

def test_batch_respects_concurrency_limit():
    """POST batch with 5 IDs → 3 running, 2 queued"""

def test_queued_auto_launches():
    """After 1 completes → next queued story launches"""

def test_batch_status_shows_per_story():
    """GET status → per-story running/pending/done"""

def test_batch_completion_notification():
    """All done → SSE event pushed to chat"""

def test_batch_confirmation_required(page):
    """Click Launch → confirmation before execution"""
```
