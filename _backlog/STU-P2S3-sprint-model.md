---
story_id: STU-P2S3.1
title: Sprint data model (YAML)
priority: critical
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint3
---

# Sprint data model

## Why

There's no concept of "sprint" in the current data model. Stories exist in a flat backlog. To show sprint views and track velocity, we need a sprint entity.

## Scope

**In:**
- `_sprints/` directory at project root
- Sprint file format: `sprint-{N}.yaml` with metadata + story list
- Fields: id, name, goal, start_date, end_date, status (active/closed/planned), stories[]
- `scripts/dashboard/parsers.py`: `load_sprints()`, `get_sprint(id)`
- `scripts/dashboard/services/sprint_service.py`: create, close, add/remove stories
- Stories get optional `sprint` field in frontmatter (backref)

**Out:**
- Sprint velocity calculation (Sprint 3.3 handles display)
- Auto-assignment of stories to sprints
- Sprint capacity planning

## Acceptance criteria

- [ ] `_sprints/sprint-1.yaml` is a valid sprint file with all fields
- [ ] `load_sprints()` returns list of sprint objects sorted by start_date
- [ ] `get_sprint(id)` returns single sprint with resolved story objects
- [ ] Creating a sprint creates the YAML file
- [ ] Adding a story to a sprint updates both sprint YAML and story frontmatter
- [ ] Closing a sprint sets status=closed and end_date
- [ ] Only one sprint can be status=active at a time

## Tech requirements

- **Format:** YAML (consistent with projects.yaml pattern)
- **Schema:**
  ```yaml
  id: sprint-4
  name: "Phase 2 - CRUD"
  goal: "Product builder can create/edit/delete stories"
  start_date: 2026-05-06
  end_date: 2026-05-08
  status: active  # planned | active | closed
  phase: "Phase 2"
  stories:
    - STU-P2S1.1
    - STU-P2S1.2
  ```
- **Bidirectional link:** story frontmatter gets `sprint: sprint-4`
- **Atomic:** use same file_lock + atomic write pattern from Sprint 1

## Designer requirements

- N/A (data model only)

## TDD

```python
# tests/dashboard/test_sprint_model.py

def test_load_sprints_returns_sorted_list():
    """Multiple sprint files → sorted by start_date"""

def test_get_sprint_resolves_stories():
    """get_sprint('sprint-1') → includes full story objects"""

def test_create_sprint_writes_yaml():
    """create_sprint() → file exists with correct schema"""

def test_close_sprint_sets_status_and_date():
    """close_sprint() → status=closed, end_date=today"""

def test_only_one_active_sprint():
    """Activating sprint-2 when sprint-1 active → error or auto-close"""

def test_add_story_updates_both_files():
    """add_story_to_sprint() → sprint YAML + story frontmatter updated"""
```
