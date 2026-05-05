---
story_id: STU-P2S2.3
title: Validation flow (Approve / Request changes)
priority: high
status: in_review
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint2
parent_story: STU-P2S2.2
---

# Validation flow (Approve / Request changes)

## Why

When a story is "in_review", the builder needs to approve (→ done) or request changes (→ in_progress) with a single click. This is the core PM validation gesture.

## Scope

**In:**
- Story modal shows "Approve" and "Request Changes" buttons when status = in_review
- "Approve" → PATCH status to "done" + optional comment
- "Request Changes" → PATCH status to "in_progress" + required comment
- Comment stored in story body (appended as `## Review — {date}`)
- Visual feedback: green flash for approve, orange for request changes

**Out:**
- Multi-reviewer approval (single user for now)
- Approval chains or gates
- Email/Slack notification on approval

## Acceptance criteria

- [ ] Buttons visible ONLY when story status = in_review
- [ ] "Approve" moves to done + closes modal + success feedback
- [ ] "Request Changes" requires a comment (textarea appears)
- [ ] Comment appended to story .md body under `## Review — YYYY-MM-DD`
- [ ] Both actions update the kanban immediately
- [ ] Keyboard shortcut: Cmd+Enter to approve (for speed)
- [ ] After approve, card moves to "done" column without page refresh

## Tech requirements

- **Approve:** `PATCH /api/stories/{id}/status` + optional `POST /api/stories/{id}/comment`
- **Request changes:** same PATCH (to in_progress) + required comment
- **Comment endpoint:** `POST /api/stories/{id}/comment` body: `{"text": "..."}`
- **Comment storage:** append to .md body (not frontmatter)
- **HTMX:** buttons use `hx-patch` with `hx-swap="none"` + `HX-Trigger`

## Designer requirements

- Approve button: green, prominent, left position
- Request Changes: orange/amber, secondary style, right position
- Comment textarea: appears with slide-down animation (150ms)
- Placeholder text: "What needs to change?"
- Flash feedback: card briefly glows green (approve) or orange (changes)
- Buttons disappear when status ≠ in_review (conditional render)

## TDD

```python
# tests/dashboard/test_validation_flow.py (Playwright)

def test_approve_button_shown_for_in_review():
    """Story in_review → modal shows Approve button"""

def test_approve_button_hidden_for_other_statuses():
    """Story in todo → no Approve/Request Changes buttons"""

def test_approve_moves_to_done():
    """Click Approve → story status becomes done"""

def test_request_changes_requires_comment():
    """Click Request Changes without comment → validation error"""

def test_request_changes_appends_review_section():
    """Submit with comment → .md file has ## Review section"""

def test_approve_updates_kanban():
    """Approve → card moves to done column without refresh"""
```
