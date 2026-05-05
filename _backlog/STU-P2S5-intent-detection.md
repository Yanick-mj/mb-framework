---
story_id: STU-P2S5.1
title: Chat intent detection for CRUD actions
priority: critical
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint5
parent_story: STU-P2S4.2
---

# Chat intent detection for CRUD actions

## Why

The builder wants to say "crée un ticket pour fix le header" and have it happen. The chat needs to detect actionable intents and route them to CRUD endpoints.

## Scope

**In:**
- Intent detection via Claude tool_use (structured output)
- Supported intents: create_story, update_status, list_stories, get_status, brainstorm
- Tool definitions passed to Claude API for reliable extraction
- Response includes: intent + extracted parameters (title, priority, etc.)

**Out:**
- Custom NLP model (use Claude's native tool_use)
- Intents beyond CRUD (deploy, git operations)
- Multi-step reasoning chains

## Acceptance criteria

- [ ] "Crée un ticket: fix le header" → intent: create_story, title: "fix le header"
- [ ] "Passe STU-5 en done" → intent: update_status, story_id: STU-5, status: done
- [ ] "Qu'est-ce qui est en cours ?" → intent: list_stories, filter: in_progress
- [ ] "Propose 3 quick wins" → intent: brainstorm, topic: quick wins
- [ ] Ambiguous input → intent: chat (fallback to normal response)
- [ ] Parameters extracted correctly (title, priority, status, story_id)

## Tech requirements

- **Claude tool_use:** define tools matching CRUD actions
- **Tools schema:**
  ```python
  tools = [
      {"name": "create_story", "parameters": {"title": str, "priority": str, "description": str}},
      {"name": "update_status", "parameters": {"story_id": str, "status": str}},
      {"name": "list_stories", "parameters": {"filter_status": str}},
      {"name": "brainstorm", "parameters": {"topic": str, "count": int}},
  ]
  ```
- **Fallback:** if no tool_use in response → treat as regular chat message
- **Language:** system prompt handles French + English input

## Designer requirements

- N/A (backend logic only — UI impact in S5.2)

## TDD

```python
# tests/dashboard/test_intent_detection.py

def test_create_intent_detected():
    """'Crée un ticket: fix header' → create_story intent with title"""

def test_status_change_intent():
    """'Passe STU-5 en done' → update_status intent"""

def test_list_intent():
    """'Qu est-ce qui est en cours' → list_stories with filter"""

def test_brainstorm_intent():
    """'Propose 3 quick wins' → brainstorm intent, count=3"""

def test_ambiguous_falls_back_to_chat():
    """'Bonjour comment ça va' → no tool_use, regular response"""
```
