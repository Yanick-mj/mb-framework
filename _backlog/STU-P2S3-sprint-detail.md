---
story_id: STU-P2S3.3
title: Sprint detail page with drill-down
priority: high
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint3
parent_story: STU-P2S3.1
---

# Sprint detail page with drill-down

## Why

The builder needs to drill into a sprint to see all its tickets, their statuses, and measure what shipped vs what's left.

## Scope

**In:**
- Route: `GET /projects/{name}/sprints/{sprint_id}`
- Header: sprint name, goal, dates, status
- Metrics row: total stories, done, in progress, blocked, % completion
- Story list grouped by status (mini-kanban or grouped list)
- Click story → opens story modal (reuse STU-D6)
- "Close Sprint" button (when active)

**Out:**
- Velocity comparison across sprints
- Burndown chart (Phase 6)

## Acceptance criteria

- [ ] Sprint detail page shows all sprint metadata
- [ ] Metrics row: counts per status + % bar
- [ ] Stories grouped by status with colored indicators
- [ ] Stories clickable → opens existing story modal
- [ ] "Close Sprint" button visible when status=active
- [ ] Close sprint → confirmation → status=closed + end_date=today
- [ ] Closed sprint shows "Completed on {date}" instead of close button

## Tech requirements

- **Template:** `templates/sprint_detail.html`
- **Data:** reuse `get_sprint(id)` with resolved stories
- **Close action:** `POST /api/sprints/{id}/close`
- **Modal reuse:** same `hx-get="/api/stories/{id}/modal"` pattern

## Designer requirements

- Header: large sprint name + goal subtitle
- Metrics: 4 stat boxes in a row (Total | Done | In Progress | Blocked)
- Stat boxes: number large + label small below, colored accent per type
- Story list: compact cards (smaller than kanban), grouped with status header
- Close button: red/orange secondary button, top-right
- Completed state: green banner "Sprint completed on May 8, 2026"

## TDD

```python
# tests/dashboard/test_sprint_detail.py

def test_sprint_detail_renders_metadata():
    """Page shows name, goal, dates"""

def test_sprint_detail_shows_story_count():
    """Metrics row shows correct counts"""

def test_story_click_opens_modal(page):
    """Click story in list → modal appears"""

def test_close_sprint_button_works(page):
    """Click Close → confirmation → sprint becomes closed"""

def test_closed_sprint_shows_completion_date():
    """Closed sprint → 'Completed on' banner, no close button"""
```
