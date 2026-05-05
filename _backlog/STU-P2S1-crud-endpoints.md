---
story_id: STU-P2S1.1
title: Backend CRUD endpoints for stories
priority: critical
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint1
---

# Backend CRUD endpoints for stories

## Why

The dashboard is read-only. Product builders cannot create, edit, or delete stories from the UI. This endpoint layer is the foundation for all write operations.

## Scope

**In:**
- `scripts/dashboard/api/stories.py` — FastAPI router with CRUD endpoints
- `POST /api/stories` — create a new story .md file in `_backlog/`
- `PUT /api/stories/{story_id}` — update frontmatter + body
- `DELETE /api/stories/{story_id}` — archive (move to `_backlog/_archive/`) or hard delete
- `scripts/dashboard/services/file_lock.py` — fcntl advisory locking
- `scripts/dashboard/services/story_writer.py` — atomic write (write to .tmp, rename)
- Request/response Pydantic models with validation

**Out:**
- Frontend forms (S1.2)
- Drag-drop status changes (Sprint 2)
- Batch operations (Sprint 6)

## Acceptance criteria

- [ ] `POST /api/stories` creates a valid .md file with YAML frontmatter + body
- [ ] `PUT /api/stories/{id}` updates only specified fields, preserves others
- [ ] `DELETE /api/stories/{id}` moves file to `_backlog/_archive/{id}.md`
- [ ] Concurrent writes to same story return 409 Conflict (file lock)
- [ ] Invalid story_id format returns 422
- [ ] Missing required fields (title) returns 422
- [ ] Created file is parseable by existing `parsers.py`
- [ ] Response includes full story object after mutation

## Tech requirements

- **File locking:** `fcntl.flock(LOCK_EX | LOCK_NB)` with 3s retry + timeout
- **Atomic writes:** write to `{filename}.tmp` then `os.rename()` (POSIX atomic)
- **Frontmatter format:** must match existing stories (yaml between `---` delimiters)
- **ID generation:** `STU-{next_int}` based on max existing ID + 1
- **Validation:** Pydantic models for StoryCreate, StoryUpdate (partial)
- **Router prefix:** `/api` mounted on main FastAPI app

## Designer requirements

- N/A (backend only — no UI in this ticket)

## TDD

Write tests BEFORE implementation:

```python
# tests/dashboard/test_api_stories.py

def test_create_story_returns_201_with_valid_payload():
    """POST /api/stories with title+priority → 201 + story object"""

def test_create_story_generates_sequential_id():
    """New story gets STU-{max+1} as story_id"""

def test_create_story_writes_valid_markdown_file():
    """Created file has --- frontmatter --- and body"""

def test_update_story_preserves_unmodified_fields():
    """PUT with only title change keeps priority, status, etc."""

def test_update_story_returns_404_for_missing_id():
    """PUT /api/stories/STU-999 → 404"""

def test_delete_story_moves_to_archive():
    """DELETE moves file to _archive/ dir"""

def test_concurrent_write_returns_409():
    """Two simultaneous PUTs → one succeeds, one gets 409"""

def test_create_story_validates_required_fields():
    """POST without title → 422"""
```
