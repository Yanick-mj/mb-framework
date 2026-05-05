---
story_id: STU-P2S1.4
title: Story deletion and archival
priority: medium
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint1
parent_story: STU-P2S1.1
---

# Story deletion and archival

## Why

Backlog accumulates stale tickets. The builder needs to clean up without losing history — archive by default, hard delete as an option.

## Scope

**In:**
- "Archive" button on story modal (primary action)
- "Delete permanently" option (behind confirmation)
- Archive: moves to `_backlog/_archive/`, removes from board
- Delete: removes file entirely
- Confirmation dialog for both actions
- Undo for archive (toast with "Undo" link for 5s)

**Out:**
- Bulk archive/delete (Sprint 6)
- Archive page/view (nice-to-have, not blocking)

## Acceptance criteria

- [ ] "Archive" button visible on story modal (secondary style)
- [ ] Click "Archive" shows confirmation: "Archive {title}?"
- [ ] Confirm → story disappears from kanban + toast "Archived. Undo?"
- [ ] "Undo" within 5s → story restored to original position
- [ ] "Delete permanently" behind "..." menu or smaller link
- [ ] Delete confirmation is stronger: "This cannot be undone. Delete?"
- [ ] After archive, file exists in `_backlog/_archive/`
- [ ] After delete, file is gone

## Tech requirements

- **Archive endpoint:** `POST /api/stories/{id}/archive` (not DELETE — semantic)
- **Undo:** `POST /api/stories/{id}/unarchive` (moves back from _archive/)
- **Hard delete:** `DELETE /api/stories/{id}?permanent=true`
- **Toast:** HTMX OOB swap or lightweight JS toast (no library)
- **Undo window:** 5s client-side timer, after which toast disappears

## Designer requirements

- Archive button: muted/secondary style (not destructive-looking)
- Delete: red text, small, behind overflow menu "..."
- Confirmation dialog: centered modal, blur background
- Toast: bottom-right, dark background, white text, "Undo" as underlined link
- Toast animation: slide up + fade out after 5s

## TDD

```python
# tests/dashboard/test_delete_archive.py (Playwright)

def test_archive_button_on_story_modal():
    """Story modal shows 'Archive' button"""

def test_archive_moves_file():
    """Archive → file in _backlog/_archive/, not in _backlog/"""

def test_archive_shows_undo_toast():
    """After archive → toast visible with 'Undo' link"""

def test_undo_restores_story():
    """Click 'Undo' within 5s → story back on board"""

def test_permanent_delete_removes_file():
    """Delete permanently → file gone from filesystem"""

def test_delete_requires_confirmation():
    """Click delete → confirmation dialog appears first"""
```
