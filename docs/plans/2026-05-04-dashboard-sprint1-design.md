# Dashboard Sprint 1 — Design

**Date:** 2026-05-04
**Branch:** feat/dashboard-mvp
**Scope:** D1 + D2 + D3 + D6 + D7-partial

## Value delivered

A PM opens localhost:5111, sees project health (overview), tracks sprint progress (kanban board), clicks any card to read the full story (modal), and data auto-refreshes every 5s. The "standup in 30 seconds" promise.

## Sprint scope

| Story | Title | Why in Sprint 1 |
|-------|-------|-----------------|
| D1 | Server skeleton + project loader | Foundation — everything depends on it |
| D2 | Overview page | Landing page — first thing a PM sees |
| D3 | Kanban board | Most-used view for sprint tracking |
| D6 | Story detail modal | Bridge between card and full story content |
| D7-partial | Polling for overview + board | Live updates without manual refresh |

**Deferred to Sprint 2:** D4 (Roadmap), D5 (Inbox), D7-complete, D8 (Entry points).

## Approach

Thin `scripts/dashboard/` layer over existing v2.1/v2.2 parsers. Maximum reuse, no logic duplication. `project_context()` monkey-patches `_paths.project_root()` — safe because uvicorn is single-threaded.

## File layout

```
scripts/dashboard/
├── __init__.py
├── __main__.py          # uvicorn launcher + dep check
├── server.py            # FastAPI app, routes (full + partials)
├── parsers.py           # project_context() + data wrappers
├── templates/
│   ├── base.html        # sidebar + nav + modal container + HTMX CDN
│   ├── overview.html
│   ├── board.html
│   └── partials/
│       ├── stage_badge.html
│       ├── stats_grid.html
│       ├── runs_table.html
│       ├── board_columns.html
│       └── story_modal.html
├── static/
│   └── style.css        # extracted from prototype-dashboard.html
└── tests/
    ├── __init__.py
    ├── conftest.py       # tmp_project fixtures + TestClient factory
    ├── test_parsers.py   # unit tests for every parser function
    └── test_routes.py    # integration tests via FastAPI TestClient
```

## parsers.py — functions

All functions are pure data (dict/list), no FastAPI dependency.

| Function | Input | Output | Wraps |
|----------|-------|--------|-------|
| `project_context(path)` | Path | context manager | monkeypatches `_paths.project_root()` |
| `load_projects()` | — | list[dict] | `v2_1.projects.load()` |
| `get_stage_data(path)` | Path | dict (stage, since) | reads mb-stage.yaml |
| `get_story_stats(path)` | Path | dict (total + per-status counts) | `board._group_by_status()` |
| `get_board_data(path)` | Path | dict[str, list[dict]] | enhanced `_group_by_status()` with title/priority/labels |
| `get_recent_runs(path, limit)` | Path, int | list[dict] | `runs.load_recent()` |
| `get_story_detail(path, story_id)` | Path, str | dict or None | parses story .md file |
| `get_inbox_data(path)` | Path | dict (in_review, blocked, approvals, total) | `inbox._scan_stories()` + `_scan_approvals()` |

## server.py — routes

### Full page routes
| Method | Path | Template |
|--------|------|----------|
| GET | `/` | redirect or "no projects" page |
| GET | `/projects/{name}/overview` | overview.html |
| GET | `/projects/{name}/board` | board.html |

### Partial routes (HTMX fragments)
| Method | Path | Template |
|--------|------|----------|
| GET | `/partials/{name}/stage` | stage_badge.html |
| GET | `/partials/{name}/stats` | stats_grid.html |
| GET | `/partials/{name}/runs` | runs_table.html |
| GET | `/partials/{name}/board` | board_columns.html |
| GET | `/partials/{name}/inbox-count` | badge number |
| GET | `/partials/{name}/story/{story_id}` | story_modal.html |

Route logic is thin: call parsers, pass to Jinja2 template. No business logic in routes.

### Error handling
- Unknown project name → 404
- Missing story_id → 404
- No projects registered → "no projects" page

## Templates & CSS

- **base.html:** sidebar (project name + stage badge, nav links, inbox badge), modal container div, HTMX CDN
- **overview.html:** stage badge + stats grid + runs table, each in a pollable div (`hx-trigger="every 5s"`)
- **board.html:** 5-column grid, cards with story_id/title/priority dot/labels, cards trigger modal via `hx-get`
- **story_modal.html:** frosted glass overlay, frontmatter fields, Why/Scope/AC sections, checkboxes, close via overlay/X/Escape
- **style.css:** extracted from prototype-dashboard.html, CSS variables (warm palette), no build step

## TDD strategy

- **Mandatory TDD (red-green-refactor):** `test_parsers.py` (unit) + `test_routes.py` (integration via TestClient)
- **Manual testing:** templates/HTML verified in browser
- Tests written BEFORE implementation code
- Fixtures: `tmp_project` with known files on disk, assertions on exact return shapes

## Dependencies

```
pip install fastapi uvicorn jinja2 pyyaml
pip install httpx pytest  # dev only (TestClient needs httpx)
```
