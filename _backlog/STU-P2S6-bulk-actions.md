---
story_id: STU-P2S6.2
title: Bulk status change
priority: high
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint6
parent_story: STU-P2S6.1
---

# Bulk status change

## Why

Validating 5 stories one by one is tedious. The builder selects all "in_review" stories and approves them in one click.

## Scope

**In:**
- Action bar button: "Move to..." dropdown (status options)
- `POST /api/stories/bulk/status` body: `{"story_ids": [...], "status": "done"}`
- Backend iterates and updates each file (with locking per file)
- Response: list of results (success/failure per story)
- UI: progress indicator during bulk operation

**Out:**
- Bulk edit other fields (title, priority) — keep simple
- Undo bulk (too complex for now)

## Acceptance criteria

- [ ] "Move to" dropdown in action bar with all status options
- [ ] Select 3 stories + "Move to done" → all 3 updated
- [ ] Each file updated atomically (locking per story)
- [ ] Partial failure: if 1/3 fails, other 2 still succeed
- [ ] Response shows per-story result (✅ or ❌ + reason)
- [ ] Kanban refreshes after bulk action completes
- [ ] Button disabled during execution (prevent double-submit)

## Tech requirements

- **Endpoint:** `POST /api/stories/bulk/status`
- **Body:** `{"story_ids": ["STU-1", "STU-2"], "status": "done"}`
- **Implementation:** loop with individual file locks (not one big lock)
- **Response:** `{"results": [{"id": "STU-1", "ok": true}, {"id": "STU-2", "ok": false, "error": "..."}]}`
- **Frontend:** disable action bar + show spinner during request

## Designer requirements

- "Move to" dropdown: appears above action bar (dropdown-up)
- Status options: same colored dots as kanban headers
- Processing state: spinner replaces button text
- Results: brief toast "3/3 moved to done ✅" or "2/3 moved, 1 failed"

## TDD

```python
# tests/dashboard/test_bulk_actions.py

def test_bulk_status_change():
    """POST bulk with 3 IDs → all 3 files updated"""

def test_bulk_partial_failure():
    """1 locked file → 2 succeed, 1 fails, correct response"""

def test_bulk_invalid_status():
    """POST with invalid status → 422"""

def test_bulk_empty_list():
    """POST with empty story_ids → 422"""

def test_bulk_updates_kanban(page):
    """Bulk move → cards appear in new column"""
```
