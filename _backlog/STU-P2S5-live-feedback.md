---
story_id: STU-P2S5.4
title: Agent output streamed in chat
priority: high
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint5
parent_story: STU-P2S5.3
---

# Agent output streamed in chat

## Why

After launching an agent, the builder needs to see progress — not wait blindly. Streaming agent stdout into the chat gives real-time visibility.

## Scope

**In:**
- Agent stdout/stderr piped to SSE stream
- Chat shows agent output in a special "agent log" block
- Collapsible: shows last 5 lines by default, expand to see all
- Completion: final message "Agent finished. Result: {summary}"
- Link to deliverable when done

**Out:**
- Full terminal emulation (just text streaming)
- Syntax highlighting of agent output
- Real-time diff view of files changed

## Acceptance criteria

- [ ] After agent launch, chat shows "Agent running..." with live log
- [ ] Agent stdout lines appear in chat as they're produced
- [ ] Log block is collapsible (last 5 lines visible by default)
- [ ] On completion: "✅ Agent finished" + link to deliverable
- [ ] On failure: "❌ Agent failed" + last error lines
- [ ] Long-running agents show elapsed time indicator
- [ ] Multiple agent logs coexist in chat (one per launched story)

## Tech requirements

- **SSE events:** `{"type": "agent_log", "story_id": "...", "line": "..."}`
- **Pipe:** `asyncio` read loop on subprocess stdout
- **Buffering:** batch lines in 500ms windows (don't flood client)
- **Completion event:** `{"type": "agent_done", "story_id": "...", "success": bool}`
- **Deliverable link:** check `_bmad-output/deliverables/{id}/` after completion

## Designer requirements

- Agent log block: monospace font, dark background (terminal-like)
- Collapsed: "▸ Agent log (12 lines)" with expand button
- Expanded: scrollable, max-height 300px
- Status indicator: green pulse while running, static check when done
- Elapsed time: "Running for 1m 23s" updated every 5s
- Completion banner: green (success) or red (failure) with icon

## TDD

```python
# tests/dashboard/test_live_feedback.py (Playwright)

def test_agent_log_appears_in_chat(page):
    """After launch → agent log block appears"""

def test_log_lines_stream_in(page):
    """Mock subprocess output → lines appear in log block"""

def test_completion_shows_success(page):
    """Agent finishes → success message + deliverable link"""

def test_failure_shows_error(page):
    """Agent crashes → error message with last lines"""

def test_log_collapsible(page):
    """Log shows 5 lines by default, expand shows all"""
```
