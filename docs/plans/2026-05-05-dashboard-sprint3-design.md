# Sprint 3 Design — Sprint Management

## Overview

Add sprint management to the dashboard: data model, list page, detail page with kanban/list toggle, roadmap integration, and CRUD operations. All sprint data stored as YAML files in `_sprints/` per project.

## Architecture

Same-file approach — extend existing modules:

| Layer | File | Additions |
|-------|------|-----------|
| Data | `parsers.py` | `load_sprints()`, `get_sprint(id)`, `get_sprints_data()`, enrich `get_roadmap_data()` |
| CRUD | `crud.py` | `create_sprint()`, `close_sprint()`, `add_story_to_sprint()`, `remove_story_from_sprint()` |
| Routes | `server.py` | 2 pages + 6 API endpoints + 3 partials |
| Templates | `templates/` | `sprints.html`, `sprint_detail.html`, partials |
| Storage | `_sprints/` | `sprint-{N}.yaml` per project |

## Data Model

Sprint YAML at `{project}/_sprints/sprint-{N}.yaml`:

```yaml
id: sprint-1
name: "Phase 2 - CRUD"
goal: "Builder can create/edit/delete stories"
start_date: 2026-05-06
end_date: 2026-05-08
status: active        # planned | active | closed
phase: "Phase 2"
stories: [STU-P2S1.1, STU-P2S1.2]
```

Stories get optional `sprint: sprint-1` backref in frontmatter.

Constraint: only one sprint can be `active` at a time.

## Routes

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/projects/{name}/sprints` | Sprints list page |
| `GET` | `/projects/{name}/sprints/{sprint_id}` | Sprint detail page |
| `POST` | `/api/sprints/{name}` | Create sprint (JSON) |
| `POST` | `/api/sprints/{name}/form` | Create sprint (form) |
| `POST` | `/api/sprints/{name}/{id}/close` | Close sprint |
| `POST` | `/api/sprints/{name}/{id}/stories` | Add story to sprint |
| `DELETE` | `/api/sprints/{name}/{id}/stories/{story_id}` | Remove story |
| `GET` | `/partials/{name}/sprints` | Sprint list HTMX refresh |
| `GET` | `/partials/{name}/sprint/{id}` | Sprint detail HTMX refresh |
| `GET` | `/partials/{name}/create-sprint` | Create sprint form partial |

## UI Design

### Sidebar
New "Sprints" link between Board and Roadmap.

### Sprints List Page
- Cards with progress bars, active sprint pinned to top with blue accent border
- Each card: name, goal (italic, truncated), dates, phase tag, X/Y stories, % bar
- Closed sprints muted (opacity 0.6)
- "+ New Sprint" button top-right opens modal
- Empty state: "No sprints yet" with CTA

### Sprint Detail Page
- Breadcrumb: `Sprints / sprint-3`
- Header card with status pill, phase tag, goal, dates
- Stat cards row (reuse overview `stat-card` pattern): Total, Done, In Progress, Todo
- **Board/List toggle** — kanban (5-column board) is default, list view groups by status
- Click any story → opens existing `story_modal.html` via `hx-get="/partials/{name}/story/{story_id}"`
- "Close Sprint" button (active sprints only) → confirmation → sets status=closed + end_date=today
- Closed sprint: green "Completed on {date}" banner, no close button

### Roadmap Enrichment
- Phase cards show "N sprints, X% complete" line with mini progress bar
- Click "View sprints →" navigates to sprints page filtered by phase
- Phase with no sprints: "No sprints yet"

### Story Modal Addition
- New "Sprint" field in sheet-meta showing which sprint the story belongs to
- "Add to Sprint" dropdown in story modal for planned/active sprints (P2S3.5)

## Dependency Order (TDD)

1. **STU-P2S3.1** — Sprint data model: parsers + CRUD functions
2. **STU-P2S3.2** — Sprints list page: route + template + sidebar link
3. **STU-P2S3.3** — Sprint detail page: route + template + kanban/list toggle + close action
4. **STU-P2S3.4** — Roadmap ↔ Sprint links: parser enrichment + phase filter
5. **STU-P2S3.5** — Sprint CRUD from UI: create form modal + add/remove stories

## Prototype

Interactive HTML mockup: `docs/plans/sprint3-preview.html`
