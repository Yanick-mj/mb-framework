---
story_id: STU-P2S1.2
title: Story creation form
priority: critical
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint1
parent_story: STU-P2S1.1
---

# Story creation form

## Why

The builder needs a way to create tickets without leaving the dashboard. A form accessible from any page lets them capture ideas instantly.

## Scope

**In:**
- "New Story" button in header/sidebar (always visible)
- Modal form with: title (required), description (textarea), priority (dropdown), status (dropdown, default: backlog)
- HTMX POST to `/api/stories` on submit
- Success: close modal + refresh current view
- Error: inline validation messages

**Out:**
- Rich text editor for description (plain textarea is fine)
- File attachments
- Template selection

## Acceptance criteria

- [ ] "New Story" button visible on all pages
- [ ] Click opens a modal form (not a new page)
- [ ] Title field is required — submit disabled if empty
- [ ] Priority dropdown: critical, high, medium, low (default: medium)
- [ ] Status dropdown: backlog, todo, in_progress, in_review, done (default: backlog)
- [ ] Submit calls POST /api/stories and closes modal on success
- [ ] Error from API shown inline (red text below field)
- [ ] After creation, the kanban/list refreshes to show new story
- [ ] Escape key or click-outside closes the modal
- [ ] Form resets after successful creation

## Tech requirements

- **HTMX:** `hx-post="/api/stories"` with `hx-target` for error swap
- **Modal:** reuse existing modal pattern from STU-D6 (story detail modal)
- **Form validation:** HTML5 `required` + server-side Pydantic
- **Refresh:** `HX-Trigger: storiesChanged` response header → listeners refresh views
- **No JS framework:** pure HTMX + minimal vanilla JS for modal open/close

## Designer requirements

- Modal width: 560px (consistent with story detail modal)
- Form layout: stacked fields, labels above inputs
- Priority dropdown: show colored dot next to each option (same colors as kanban cards)
- Submit button: primary color, full-width at bottom
- Cancel: text link next to submit, not a button
- Aesthetic: match existing Notion + Apple style (clean, minimal, generous spacing)
- Animation: modal slides in from right or fades in (200ms)

## TDD

Write tests BEFORE implementation:

```python
# tests/dashboard/test_create_form.py (Playwright)

def test_new_story_button_visible_on_board_page():
    """Button with text 'New Story' exists in header"""

def test_click_new_story_opens_modal():
    """Click → modal appears with form fields"""

def test_submit_empty_title_shows_error():
    """Submit with empty title → validation message"""

def test_submit_valid_form_creates_story():
    """Fill title + submit → API called → modal closes → story appears in kanban"""

def test_escape_closes_modal():
    """Press Escape → modal disappears, no API call"""

def test_form_resets_after_success():
    """Create story → reopen form → fields are empty"""
```
