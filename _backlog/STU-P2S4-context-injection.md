---
story_id: STU-P2S4.3
title: Project context injection for chat
priority: high
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint4
parent_story: STU-P2S4.2
---

# Project context injection for chat

## Why

The chat must know about the project's current state to give useful answers. Without context, it's just a generic Claude — with context, it's a project-aware assistant.

## Scope

**In:**
- `scripts/dashboard/services/context_builder.py` — builds system prompt context
- Injected context: active sprint + stories summary + metrics + recent activity
- Context refreshed per chat request (not cached — data changes fast)
- Token budget: context fits in ~2000 tokens (summarized, not raw files)

**Out:**
- Full file content injection (too expensive)
- Codebase awareness (that's the agent's job, not the chat's)
- Memory/history beyond current session

## Acceptance criteria

- [ ] System prompt includes: project name, stage, active sprint summary
- [ ] System prompt includes: story counts by status (X backlog, Y in progress, Z done)
- [ ] System prompt includes: top 3 blockers (if any)
- [ ] System prompt includes: sprint % completion
- [ ] Context is under 2000 tokens (measured)
- [ ] Chat can answer "what's the sprint status?" correctly from context
- [ ] Chat can answer "what's blocked?" correctly from context

## Tech requirements

- **Context builder:** function returning string, called per request
- **Data sources:** `load_sprints()`, `get_board_data()`, `get_inbox_data()`
- **Format:** structured text (not JSON) for better LLM comprehension
- **Token counting:** `len(context.split()) * 1.3` as rough estimate
- **System prompt template:**
  ```
  You are a project assistant for {project_name} (stage: {stage}).
  
  Active sprint: {sprint_name} ({X}/{Y} stories done, {pct}% complete)
  Stories: {backlog} backlog, {todo} todo, {in_progress} in progress, {in_review} in review, {done} done
  Blockers: {blocker_list or "None"}
  
  Answer concisely about project status, priorities, and progress.
  ```

## Designer requirements

- N/A (backend only)

## TDD

```python
# tests/dashboard/test_context_builder.py

def test_context_includes_project_name():
    """Built context mentions project name"""

def test_context_includes_sprint_status():
    """Active sprint name and completion in context"""

def test_context_includes_story_counts():
    """Counts per status present in context"""

def test_context_includes_blockers():
    """Blocked stories listed in context"""

def test_context_under_token_budget():
    """Context string is under 2000 tokens estimate"""

def test_context_handles_no_active_sprint():
    """No active sprint → 'No active sprint' in context"""
```
