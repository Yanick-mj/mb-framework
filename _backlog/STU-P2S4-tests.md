---
story_id: STU-P2S4.5
title: Sprint 4 integration tests (chat)
priority: high
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint4
---

# Sprint 4 integration tests

## Why

Chat involves streaming, LLM calls, and context assembly. Integration tests ensure the full pipeline works end-to-end.

## Scope

**In:**
- E2E: open chat → send message → receive streamed response
- Mock Claude API for deterministic testing
- Context builder integration: verify correct data flows to prompt
- Error cases: missing API key, timeout, malformed input
- Regression: Sprint 1-3 features unaffected

**Out:**
- LLM quality testing (prompt tuning is manual)
- Performance benchmarks

## Acceptance criteria

- [ ] 6+ tests passing covering chat pipeline
- [ ] E2E Playwright: send message → response appears
- [ ] Mocked Claude API for CI (no real API calls in tests)
- [ ] Error handling tested (missing key, timeout)
- [ ] Sprint 1-3 regressions checked

## Tech requirements

- **Mock:** `unittest.mock.patch` on anthropic client
- **Fixture:** mock SSE stream response
- **Playwright:** test chat panel open → send → receive

## Designer requirements

- N/A (tests only)

## TDD

```python
# tests/dashboard/test_chat_e2e.py

def test_chat_full_flow(page):
    """Open panel → type message → response streams in"""

def test_chat_with_mocked_api():
    """POST /api/chat with mocked Claude → valid SSE"""

def test_missing_api_key_error():
    """No ANTHROPIC_API_KEY → helpful error message"""

def test_chat_context_contains_current_data():
    """Context builder includes latest sprint data (not stale)"""
```
