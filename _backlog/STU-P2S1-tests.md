---
story_id: STU-P2S1.5
title: Sprint 1 integration tests
priority: high
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint1
parent_story: STU-P2S1.1
---

# Sprint 1 integration tests

## Why

CRUD on files is risky — concurrent access, malformed YAML, partial writes. Integration tests catch issues that unit tests miss.

## Scope

**In:**
- Full API integration tests (TestClient, real filesystem via tmp_path)
- Playwright E2E: create → edit → archive flow
- Edge cases: special characters in title, very long descriptions, unicode
- Concurrency test: 2 simultaneous PUT requests
- Regression: existing read endpoints still work after write endpoints added

**Out:**
- Performance/load testing
- Cross-browser testing (Chromium only for Playwright)

## Acceptance criteria

- [ ] 10+ pytest API tests passing (covers all CRUD endpoints)
- [ ] 4+ Playwright tests passing (full user flow)
- [ ] Concurrency test proves file locking works
- [ ] No regression on existing dashboard routes (GET /board, /overview, etc.)
- [ ] Tests run in CI-compatible way (no real ~/.mb dependency)
- [ ] All tests use tmp_path fixtures (no side effects)

## Tech requirements

- **pytest fixtures:** `tmp_project` that creates a temp `_backlog/` with sample stories
- **TestClient:** FastAPI `TestClient` for API tests (no real server needed)
- **Playwright:** `@pytest.mark.playwright` with browser fixture
- **Concurrency:** `threading.Thread` or `asyncio.gather` for lock tests
- **Isolation:** each test gets fresh tmp directory (no cross-test contamination)

## Designer requirements

- N/A (tests only)

## TDD

This IS the TDD ticket — tests written first, then implementation fills them:

```python
# tests/dashboard/test_crud_integration.py

def test_full_lifecycle_create_edit_archive():
    """Create story → edit title → archive → verify in _archive/"""

def test_create_with_special_characters():
    """Title with accents, emoji, quotes → file created correctly"""

def test_edit_preserves_body_content():
    """PUT with title change only → body markdown unchanged"""

def test_concurrent_edits_one_wins():
    """Two threads PUT same story → one 200, one 409"""

def test_archived_story_not_in_board():
    """Archive story → GET /board → story absent"""

def test_existing_read_routes_unchanged():
    """GET /overview, /board, /inbox → same responses as before"""
```
