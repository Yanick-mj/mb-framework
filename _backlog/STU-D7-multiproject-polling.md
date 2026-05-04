---
story_id: STU-D7
title: Multi-project switcher + HTMX polling
priority: high
status: todo
created: 2026-05-04
assignee: fe-dev
parent_story: STU-D1
---

# Multi-project switcher + HTMX polling

## Why

The dashboard serves multiple mb projects. The switcher lets a PM jump between drivia and studio-iris without restarting anything. HTMX polling makes data refresh automatically as developers run `/mb:feature` in their terminals.

## Scope

**In:**
- Sidebar project switcher: dropdown listing all registered projects with stage badge
- URL-based routing: `/projects/{name}/board` — switching preserves current page
- All data sections get `hx-trigger="every 5s"` + `hx-get="/partials/{name}/..."` + `hx-swap="innerHTML"`
- Partial routes in server.py:
  - `GET /partials/{name}/stage` — stage badge
  - `GET /partials/{name}/stats` — stats grid
  - `GET /partials/{name}/board` — board columns
  - `GET /partials/{name}/runs` — runs table
  - `GET /partials/{name}/inbox` — inbox items + sidebar badge count
- Sidebar inbox badge updates via polling

**Out:**
- SSE / WebSocket (Phase 2 if needed)

## Acceptance criteria

- [ ] Project dropdown shows all projects from `~/.mb/projects.yaml`
- [ ] Clicking a project navigates to `/projects/{new_name}/{current_page}`
- [ ] Current project highlighted in dropdown with stage color
- [ ] All data sections auto-refresh every 5 seconds via HTMX
- [ ] Page does not flicker on refresh (HTMX only swaps if content changed)
- [ ] Adding a story file to disk → appears on board within 5 seconds
- [ ] Sidebar inbox badge count updates with polling

## Technical notes

- HTMX `hx-trigger="every 5s"` is built-in, no JS needed
- Partial routes return HTML fragments (no full page)
- Project switcher uses `<a href>` for navigation (full page load on switch)
- HTMX includes `HX-Request` header — server can detect partial vs full requests

## Testing

- Switch between 2 projects — verify all data changes
- Create a story file on disk while dashboard is open — verify it appears within 5s
- Change a story status in the .md file — verify board updates
- Test with 1 project registered (no dropdown arrow)
