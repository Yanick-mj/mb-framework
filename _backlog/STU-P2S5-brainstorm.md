---
story_id: STU-P2S5.5
title: Brainstorm mode with ticket creation
priority: medium
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint5
parent_story: STU-P2S5.1
---

# Brainstorm mode with ticket creation

## Why

The builder says "propose 3 quick wins pour l'onboarding" and wants to turn the best ideas into tickets directly — no copy-paste.

## Scope

**In:**
- Brainstorm intent → Claude responds with numbered suggestions
- Each suggestion has a "→ Create ticket" button
- Click → pre-fills create form (title from suggestion, description from context)
- "Create all" option to batch-create all suggestions
- Suggestions styled differently from regular responses

**Out:**
- Voting/ranking of suggestions
- AI self-ranking (just list them, builder decides)

## Acceptance criteria

- [ ] "Propose 3 quick wins" → numbered list with action buttons
- [ ] Each suggestion has "Create ticket →" button
- [ ] Click creates story with title = suggestion text
- [ ] "Create all" button creates all suggestions as separate stories
- [ ] Created stories appear in kanban immediately
- [ ] Suggestions styled as cards (not plain text)
- [ ] Works in French and English

## Tech requirements

- **Response format:** Claude returns structured suggestions via tool_use
- **Tool:** `suggest_items` with `items: [{title, description, priority}]`
- **Frontend:** special render for suggestion-type responses
- **Create action:** reuses POST /api/stories endpoint
- **Batch:** multiple POST calls (or batch endpoint)

## Designer requirements

- Suggestion cards: numbered, subtle border, compact
- "Create ticket →" button: small, right-aligned on each card
- "Create all" button: below the list, secondary style
- Created indicator: card gets green check after creation
- Card content: title bold, 1-line description muted below

## TDD

```python
# tests/dashboard/test_brainstorm.py

def test_brainstorm_returns_suggestions():
    """'Propose 3 quick wins' → response with 3 items"""

def test_create_from_suggestion(page):
    """Click 'Create ticket' on suggestion → story file created"""

def test_create_all_suggestions(page):
    """Click 'Create all' → all suggestions become stories"""

def test_suggestion_cards_rendered(page):
    """Suggestions appear as styled cards, not plain text"""
```
