---
story_id: STU-P2S2.2
title: PATCH status endpoint
priority: critical
status: in_review
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint2
---

# PATCH status endpoint

## Why

Drag-drop and validation buttons need a lightweight endpoint to change just the status field without rewriting the entire story.

## Scope

**In:**
- `PATCH /api/stories/{story_id}/status` — updates only `status` in frontmatter
- Validates status against allowed values: backlog, todo, in_progress, in_review, done
- Returns updated story object
- Respects file locking (reuse from S1.1)
- Logs status transition in `memory/agents/_common/runs.jsonl`

**Out:**
- Workflow rules (e.g. "can't go from backlog to done directly") — keep flexible
- Notifications on status change (Sprint 4 chat could pick this up)

## Acceptance criteria

- [ ] `PATCH /api/stories/STU-1/status` with `{"status": "done"}` → 200
- [ ] Only `status` field changes in the .md file, everything else preserved
- [ ] Invalid status value → 422 with allowed values listed
- [ ] Non-existent story_id → 404
- [ ] Concurrent status changes → file lock prevents corruption
- [ ] Transition logged: `{story_id, from_status, to_status, timestamp}`

## Tech requirements

- **Endpoint:** `PATCH /api/stories/{story_id}/status`
- **Body:** `{"status": "in_progress"}` (Pydantic enum validation)
- **Allowed values:** Literal["backlog", "todo", "in_progress", "in_review", "done"]
- **Logging:** append to `runs.jsonl` with action type "status_change"
- **Reuse:** `file_lock.py` and `story_writer.py` from Sprint 1

## Designer requirements

- N/A (backend only)

## TDD

```python
# tests/dashboard/test_status_endpoint.py

def test_patch_status_updates_frontmatter():
    """PATCH with valid status → file frontmatter updated"""

def test_patch_status_invalid_value():
    """PATCH with status='invalid' → 422"""

def test_patch_status_not_found():
    """PATCH non-existent story → 404"""

def test_patch_status_logs_transition():
    """After PATCH → runs.jsonl has status_change entry"""

def test_patch_preserves_other_fields():
    """PATCH status → title, priority, description unchanged"""
```
