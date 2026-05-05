---
story_id: STU-P2S2.5
title: Sprint 2 integration tests (drag-drop + validation)
priority: high
status: in_review
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint2
---

# Sprint 2 integration tests

## Why

Drag-drop and validation involve UI + backend coordination. E2E tests ensure the full flow works.

## Scope

**In:**
- Playwright E2E: drag story → new column → verify file changed
- Playwright E2E: open in_review story → approve → verify done
- Playwright E2E: request changes with comment → verify appended
- API tests for PATCH status + comment endpoints
- Regression: Sprint 1 CRUD still works

**Out:**
- Cross-browser (Chromium only)
- Visual regression testing

## Acceptance criteria

- [ ] 8+ tests passing covering drag-drop + validation + deliverables
- [ ] Full flow test: create story → move to in_review → approve → done
- [ ] Regression suite from Sprint 1 still green
- [ ] Tests run in < 30s total

## Tech requirements

- **Playwright drag:** `page.drag_and_drop(source, target)` or Sortable.js event simulation
- **Fixtures:** stories in various statuses + sample deliverable files
- **Isolation:** fresh tmp_path per test

## Designer requirements

- N/A (tests only)

## TDD

```python
# tests/dashboard/test_sprint2_e2e.py (Playwright)

def test_full_flow_create_to_done():
    """Create → move to in_review → approve → in done column"""

def test_drag_and_file_sync():
    """Drag card → file on disk reflects new status"""

def test_approve_with_deliverable_visible():
    """Open in_review → see deliverable → approve"""

def test_request_changes_comment_persisted():
    """Request changes with comment → reopen → comment visible"""
```
