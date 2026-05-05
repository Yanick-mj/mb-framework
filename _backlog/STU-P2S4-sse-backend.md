---
story_id: STU-P2S4.2
title: SSE streaming backend for chat
priority: critical
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint4
---

# SSE streaming backend for chat

## Why

Chat responses must stream token-by-token for a responsive UX. Server-Sent Events (SSE) is simpler than WebSocket for unidirectional streaming.

## Scope

**In:**
- `POST /api/chat` — accepts message, returns SSE stream
- `scripts/dashboard/services/chat_service.py` — orchestrates LLM call
- Claude API integration with streaming (`stream=True`)
- Request body: `{"message": "...", "history": [...]}` (last 10 messages for context)
- SSE format: `data: {"token": "..."}\n\n` per chunk, `data: {"done": true}\n\n` at end

**Out:**
- Tool use / function calling (Sprint 5)
- Persistent conversation storage
- Rate limiting (nice-to-have, add if cost is an issue)

## Acceptance criteria

- [ ] `POST /api/chat` with message returns SSE stream
- [ ] Each token arrives as separate SSE event
- [ ] Final event signals completion (`done: true`)
- [ ] History from request body included in Claude prompt
- [ ] Timeout after 60s if no response (returns error event)
- [ ] Invalid/empty message → 422 (not streamed)
- [ ] Connection drop handled gracefully (no server crash)

## Tech requirements

- **FastAPI streaming:** `StreamingResponse(media_type="text/event-stream")`
- **Claude SDK:** `anthropic.messages.stream()` with `model="claude-sonnet-4-20250514"`
- **System prompt:** inject project context (stories summary, sprint status, metrics)
- **History:** max 10 messages (user/assistant pairs) to limit token usage
- **Env var:** `ANTHROPIC_API_KEY` required, error message if missing
- **Timeout:** `asyncio.wait_for()` with 60s limit

## Designer requirements

- N/A (backend only)

## TDD

```python
# tests/dashboard/test_chat_sse.py

def test_chat_returns_sse_content_type():
    """POST /api/chat → content-type: text/event-stream"""

def test_chat_streams_tokens():
    """Response contains multiple 'data:' lines"""

def test_chat_final_event_is_done():
    """Last SSE event has done=true"""

def test_chat_empty_message_returns_422():
    """POST with empty message → 422"""

def test_chat_includes_history_in_prompt():
    """History messages passed to Claude API (mock verify)"""

def test_chat_timeout_returns_error():
    """Mock slow response → error event after timeout"""
```
