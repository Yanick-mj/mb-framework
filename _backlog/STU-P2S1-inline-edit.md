---
story_id: STU-P2S1.3
title: Inline story editing from modal
priority: high
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint1
parent_story: STU-P2S1.1
---

# Inline story editing from modal

## Why

The story modal (STU-D6) currently shows read-only content. The builder needs to edit title, description, priority, and status without navigating away.

## Scope

**In:**
- "Edit" button on story modal → switches to edit mode
- Editable fields: title, description, priority, status, labels
- Save button → PUT /api/stories/{id}
- Cancel → revert to read-only view
- Optimistic UI: show changes immediately, rollback on error

**Out:**
- Editing frontmatter fields not in the form (created, assignee — admin only)
- Markdown preview for description (v2.3)
- Inline editing directly on kanban cards (just the modal)

## Acceptance criteria

- [ ] "Edit" button visible on story modal header
- [ ] Click "Edit" transforms display fields into form inputs
- [ ] Title becomes editable text input (pre-filled)
- [ ] Description becomes textarea (pre-filled, auto-height)
- [ ] Priority and status become dropdowns (pre-selected)
- [ ] "Save" calls PUT /api/stories/{id} with changed fields only
- [ ] "Cancel" reverts to read-only without API call
- [ ] Successful save shows brief success indicator (checkmark)
- [ ] Kanban card updates after modal save (HX-Trigger)
- [ ] Cannot save if title is empty

## Tech requirements

- **HTMX:** `hx-put="/api/stories/{id}"` with JSON body
- **Partial update:** only send modified fields (diff against original)
- **Optimistic UI:** swap display immediately, revert if 4xx/5xx
- **HX-Trigger:** `storiesChanged` on success to refresh kanban behind modal
- **Auto-resize textarea:** CSS `field-sizing: content` or JS fallback

## Designer requirements

- Edit mode: subtle background change on the modal (light gray → white)
- Inputs: borderless style (text looks the same, just becomes editable)
- Save/Cancel: floating action bar at bottom of modal
- Transition: smooth 150ms crossfade between read/edit mode
- Success indicator: green checkmark that fades after 1.5s

## TDD

```python
# tests/dashboard/test_inline_edit.py (Playwright)

def test_edit_button_visible_on_story_modal():
    """Story modal has an 'Edit' button"""

def test_click_edit_shows_input_fields():
    """Click Edit → title becomes input, description becomes textarea"""

def test_save_sends_put_request():
    """Change title + Save → PUT /api/stories/{id} called"""

def test_cancel_reverts_without_api_call():
    """Edit → change title → Cancel → original title shown, no network request"""

def test_save_updates_kanban_card():
    """Edit title + Save → close modal → kanban card shows new title"""

def test_empty_title_prevents_save():
    """Clear title → Save button disabled"""
```
