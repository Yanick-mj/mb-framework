---
story_id: STU-P2S3.5
title: Create and close sprints from UI
priority: high
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint3
parent_story: STU-P2S3.1
---

# Create and close sprints from UI

## Why

The builder needs to plan and close sprints without editing YAML files manually.

## Scope

**In:**
- "New Sprint" button on sprints page
- Modal form: name, goal, start_date, end_date, phase (dropdown)
- `POST /api/sprints` → creates sprint YAML
- "Add to Sprint" action on story modal → assigns story to active sprint
- "Close Sprint" on sprint detail (already in S3.3, wiring here)

**Out:**
- Sprint templates (predefined sprint structures)
- Auto-populate stories based on priority

## Acceptance criteria

- [ ] "New Sprint" button on /sprints page
- [ ] Form fields: name, goal, start_date, end_date, phase
- [ ] Submit creates sprint YAML file in `_sprints/`
- [ ] New sprint appears in list immediately
- [ ] Story modal has "Add to Sprint" dropdown (lists planned/active sprints)
- [ ] Adding story updates both sprint YAML and story frontmatter
- [ ] "Remove from Sprint" action also available

## Tech requirements

- **Endpoints:**
  - `POST /api/sprints` (create)
  - `POST /api/sprints/{id}/stories` body: `{"story_id": "STU-P2S1.1"}` (add)
  - `DELETE /api/sprints/{id}/stories/{story_id}` (remove)
  - `POST /api/sprints/{id}/close` (close)
- **Validation:** start_date < end_date, name required
- **Auto-ID:** `sprint-{max+1}`

## Designer requirements

- New Sprint button: primary, top-right of sprints page
- Form: same modal style as story creation (consistent)
- Date pickers: native HTML date inputs (no library)
- Phase dropdown: lists phases from _roadmap.md
- "Add to Sprint" in story modal: dropdown below status field
- Remove: small "x" next to sprint tag on story

## TDD

```python
# tests/dashboard/test_sprint_crud.py

def test_create_sprint_form_opens():
    """Click 'New Sprint' → modal with form fields"""

def test_create_sprint_writes_file():
    """Submit form → YAML file created in _sprints/"""

def test_add_story_to_sprint():
    """POST story to sprint → both files updated"""

def test_remove_story_from_sprint():
    """DELETE → story removed from sprint, frontmatter cleared"""

def test_close_sprint_via_api():
    """POST /api/sprints/{id}/close → status=closed"""
```
