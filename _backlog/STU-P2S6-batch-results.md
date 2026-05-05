---
story_id: STU-P2S6.4
title: Batch results view
priority: medium
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint6
parent_story: STU-P2S6.3
---

# Batch results view

## Why

After launching 3 agents, the builder returns and needs to see all results at a glance — what succeeded, what failed, what needs review.

## Scope

**In:**
- Results panel: accessible from notification or action bar
- Per-story card: status (done/failed), elapsed time, link to deliverable
- Failed stories: show error summary + "Retry" button
- Successful stories: auto-moved to "in_review" status
- "Validate all" shortcut for batch approval

**Out:**
- Diff view between old and new code
- Cost per agent run
- Detailed agent logs (link to chat log instead)

## Acceptance criteria

- [ ] Results view shows all stories from batch
- [ ] Each card: story title + status icon + elapsed time
- [ ] Successful: link to deliverable + "in_review" status
- [ ] Failed: error message + "Retry" button
- [ ] "Validate all" approves all successful stories at once
- [ ] Retry relaunches only the failed story
- [ ] Results accessible from chat notification link

## Tech requirements

- **Data source:** batch status endpoint (from S6.3)
- **Auto-status:** successful runs → `PATCH /api/stories/{id}/status` to "in_review"
- **Retry:** `POST /api/agent/launch` with single story_id
- **Validate all:** reuses bulk status change endpoint (S6.2)
- **Template:** `templates/partials/batch_results.html` (HTMX partial)

## Designer requirements

- Results cards: horizontal layout, compact
- Status icon: large (24px) — ✅ green / ❌ red / ⏳ yellow
- Elapsed time: muted text "2m 34s"
- Failed card: light red background, error text below
- "Validate all" button: green, prominent, top-right
- "Retry" button: small, on failed cards only
- Link to deliverable: "View result →" text link

## TDD

```python
# tests/dashboard/test_batch_results.py (Playwright)

def test_results_show_all_stories(page):
    """Batch of 3 → results show 3 cards"""

def test_successful_shows_deliverable_link(page):
    """Completed story → 'View result' link present"""

def test_failed_shows_retry(page):
    """Failed story → Retry button present"""

def test_validate_all_moves_to_done(page):
    """Click 'Validate all' → all successful stories become done"""

def test_retry_relaunches(page):
    """Click Retry → agent relaunched for that story"""
```
