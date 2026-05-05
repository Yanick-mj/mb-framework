---
story_id: STU-P2S4.1
title: Chat panel UI
priority: critical
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint4
---

# Chat panel UI

## Why

The builder wants to ask questions about the project state without reading dashboards. A chat panel gives instant natural language access.

## Scope

**In:**
- Chat panel: slide-in from right side (or dedicated /chat page)
- Message list: user messages + assistant responses
- Input field: textarea + send button (Enter to send, Shift+Enter for newline)
- Streaming display: tokens appear progressively
- Chat toggle button in header (always accessible)
- Message history persisted in session (lost on page refresh — stateless)

**Out:**
- Persistent chat history across sessions (v2.3)
- Multi-conversation threads
- File/image attachments

## Acceptance criteria

- [ ] Chat toggle button visible in dashboard header
- [ ] Click opens slide-in panel (right side, 400px wide)
- [ ] Input field at bottom, message list scrolls up
- [ ] User message appears immediately after send
- [ ] Assistant response streams in token by token
- [ ] Auto-scroll to bottom on new messages
- [ ] Empty state: "Ask me about your project..." placeholder
- [ ] Escape or click-outside closes panel
- [ ] Chat state persists during navigation (SPA-like with HTMX hx-boost)

## Tech requirements

- **Panel:** fixed-position div, z-index above content, CSS transition slide-in
- **Messages:** `<div class="messages">` with append-only pattern
- **Streaming:** EventSource (SSE) connection to backend
- **Input:** textarea with auto-resize, disabled while waiting for response
- **HTMX boost:** `hx-boost="true"` on nav links to preserve chat panel state
- **No framework:** vanilla JS for chat logic (~50 lines)

## Designer requirements

- Panel: white background, subtle left shadow, 400px wide
- Toggle button: chat bubble icon in header, badge with "AI" label
- Messages: user = right-aligned, blue bubble; assistant = left-aligned, gray bubble
- Streaming cursor: blinking "▌" at end of assistant message while streaming
- Input: rounded textarea, send button (arrow icon), 48px min height
- Responsive: on mobile, chat goes full-width overlay
- Animation: slide-in from right, 200ms ease-out

## TDD

```python
# tests/dashboard/test_chat_ui.py (Playwright)

def test_chat_toggle_visible():
    """Chat button in header exists"""

def test_chat_panel_opens():
    """Click toggle → panel slides in from right"""

def test_send_message_shows_in_list():
    """Type + Enter → user message appears in chat"""

def test_escape_closes_panel():
    """Press Escape → panel slides out"""

def test_chat_persists_during_navigation():
    """Navigate to another page → chat panel still open with messages"""
```
