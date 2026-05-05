---
story_id: STU-P2S3.2
title: Sprints list page
priority: critical
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint3
parent_story: STU-P2S3.1
---

# Sprints list page

## Why

The builder needs a historical view of all sprints — what shipped, what's in progress, what's planned.

## Scope

**In:**
- Route: `GET /projects/{name}/sprints`
- Page shows all sprints as cards (newest first)
- Each card: name, goal, date range, status badge, story count, % completion
- Active sprint highlighted at top
- Sidebar link: "Sprints" added to navigation

**Out:**
- Sprint detail page (S3.3)
- Sprint creation form (S3.5)
- Velocity charts

## Acceptance criteria

- [ ] `/sprints` page renders list of all sprints
- [ ] Active sprint appears at top with "Active" badge
- [ ] Each card shows: name, goal, dates, X/Y stories done
- [ ] % completion shown as progress bar
- [ ] Closed sprints show in muted style
- [ ] Empty state: "No sprints yet. Create one?" with CTA
- [ ] Sidebar has "Sprints" link (active state when on page)

## Tech requirements

- **Template:** `templates/sprints.html` extending `base.html`
- **Partial:** `templates/partials/sprint_list.html` for HTMX refresh
- **Data:** `parsers.get_sprints_data(path)` → list with computed % completion
- **% calc:** `len([s for s in stories if s.status == 'done']) / len(stories) * 100`

## Designer requirements

- Sprint cards: horizontal layout, subtle border, rounded corners
- Active sprint: left border accent (primary color), slightly elevated shadow
- Progress bar: thin (4px), colored by status (green=closed, blue=active, gray=planned)
- Status badge: pill shape (green/blue/gray)
- Date range: small muted text below name
- Goal: italic, truncated to 1 line with ellipsis
- Card hover: slight lift (translateY -2px)

## TDD

```python
# tests/dashboard/test_sprint_page.py (Playwright)

def test_sprints_page_renders():
    """GET /sprints → 200 with sprint cards"""

def test_active_sprint_at_top():
    """Active sprint rendered first regardless of date"""

def test_progress_bar_reflects_completion():
    """Sprint with 3/5 done → 60% progress bar width"""

def test_empty_state_shown():
    """No sprint files → 'No sprints yet' message"""

def test_sidebar_sprints_link_active():
    """On /sprints page → sidebar link has active class"""
```
