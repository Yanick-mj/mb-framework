---
story_id: STU-P2S5.2
title: Action confirmation before mutation
priority: high
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint5
parent_story: STU-P2S5.1
---

# Action confirmation before mutation

## Why

The chat must never mutate data silently. The builder needs to see what will happen and confirm before any create/update/delete executes.

## Scope

**In:**
- After intent detection, chat shows a confirmation card:
  "I'll create: **fix le header** (priority: medium). Confirm?"
- Confirm/Cancel buttons inline in chat
- Confirm → executes CRUD → shows success message
- Cancel → "OK, cancelled." + no mutation
- Edit before confirm: "Change priority to high" → updates preview

**Out:**
- Auto-confirm for "safe" queries (list, status check)
- Undo after confirmation (rely on archive/revert)

## Acceptance criteria

- [ ] Mutation intent → confirmation card in chat (not immediate execution)
- [ ] Card shows: action summary + extracted parameters
- [ ] "Confirm" button → action executed → success message
- [ ] "Cancel" button → no mutation → cancellation acknowledged
- [ ] User can modify parameters before confirming ("change priority to high")
- [ ] Non-mutation intents (list, status) execute immediately (no confirm)
- [ ] Confirm button disabled while action executes (prevent double-click)

## Tech requirements

- **Confirmation card:** special SSE event type `{"type": "confirmation", "action": {...}}`
- **Frontend:** renders confirmation as a styled card with buttons
- **Confirm endpoint:** `POST /api/chat/confirm` with action payload
- **State:** pending action stored in session (or passed back in confirm call)
- **HTMX:** buttons use `hx-post` to confirm/cancel endpoints

## Designer requirements

- Confirmation card: distinct from regular messages (bordered, slightly indented)
- Background: light yellow/amber (attention-drawing but not alarming)
- Action summary: bold title, parameters as key:value list
- Buttons: "Confirm" (green, primary) + "Cancel" (gray, text-only)
- After confirm: card collapses to single "✅ Created: fix le header" line
- After cancel: card collapses to "❌ Cancelled" line

## TDD

```python
# tests/dashboard/test_confirmation.py (Playwright)

def test_mutation_shows_confirmation():
    """'Crée un ticket X' → confirmation card appears, not immediate creation"""

def test_confirm_executes_action():
    """Click Confirm → story file created"""

def test_cancel_prevents_mutation():
    """Click Cancel → no file created"""

def test_non_mutation_skips_confirmation():
    """'Qu est-ce qui est en cours' → immediate response, no confirm card"""

def test_modify_before_confirm():
    """'Change priority to high' → updated confirmation card"""
```
