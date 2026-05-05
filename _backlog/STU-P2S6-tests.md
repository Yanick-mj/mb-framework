---
story_id: STU-P2S6.5
title: Sprint 6 integration tests (batch & concurrency)
priority: high
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint6
---

# Sprint 6 integration tests

## Why

Batch operations + concurrent subprocess management is the most complex feature. Integration tests prevent race conditions and ensure reliability.

## Scope

**In:**
- E2E: select 3 → launch → wait → validate all → all done
- Concurrency: 5 stories launched, verify queuing works
- Stress: bulk status change on 10 stories simultaneously
- Error recovery: kill subprocess mid-run → graceful failure
- Regression: Sprint 1-5 features still work

**Out:**
- Load testing (not the goal here)
- Cross-browser (Chromium only)

## Acceptance criteria

- [ ] 6+ tests passing covering batch + concurrency
- [ ] Full E2E: select → launch → results → validate flow
- [ ] Queue test: 5 launched, max 3 concurrent proven
- [ ] Graceful failure: killed process → "failed" status, not crash
- [ ] Regression suite (Sprint 1-5) still green
- [ ] All tests complete in < 60s

## Tech requirements

- **Subprocess mocking:** mock `asyncio.create_subprocess_exec` for speed
- **Concurrency test:** use `asyncio.gather` to simulate simultaneous requests
- **Kill test:** send SIGKILL to subprocess, verify cleanup
- **Fixtures:** pre-created stories + mock agent script

## Designer requirements

- N/A (tests only)

## TDD

```python
# tests/dashboard/test_sprint6_e2e.py

def test_full_batch_flow(page):
    """Select 3 → Launch → Wait → Validate all → all in done"""

def test_queue_respects_limit():
    """5 launched → only 3 PIDs active at once"""

def test_killed_process_shows_failed():
    """SIGKILL subprocess → status becomes 'failed'"""

def test_bulk_and_batch_dont_conflict():
    """Bulk status change while agent running → both succeed"""

def test_sprint1_to_5_regression():
    """CRUD + drag-drop + sprints + chat + actions all still work"""
```
