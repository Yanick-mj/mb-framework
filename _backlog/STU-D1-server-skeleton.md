---
story_id: STU-D1
title: Server skeleton + project loader
priority: critical
status: todo
created: 2026-05-04
assignee: be-dev
---

# Server skeleton + project loader

## Why

Every other dashboard story depends on a working FastAPI server that can load project data. This is the foundation — nothing renders without it.

## Scope

**In:**
- `scripts/dashboard/__init__.py` + `__main__.py` (uvicorn launch)
- `scripts/dashboard/server.py` — FastAPI app, Jinja2 config, static mount
- `scripts/dashboard/parsers.py` — `project_context()` manager + `load_projects()`
- `scripts/dashboard/templates/base.html` — layout with sidebar, HTMX CDN, CSS link
- `scripts/dashboard/static/style.css` — full CSS from validated prototype
- Root route `/` redirects to first project's overview
- Route `/projects/{name}/overview` returns base template with project name

**Out:**
- Actual page content (STU-D2 through STU-D5)
- Multi-project switching UI (STU-D7)
- Entry points / install integration (STU-D8)

## Acceptance criteria

- [ ] `python3 -m scripts.dashboard` starts uvicorn on port 5111
- [ ] `GET /` redirects to `/projects/{first_project}/overview`
- [ ] `GET /projects/drivia/overview` returns HTML with sidebar + empty main area
- [ ] `parsers.load_projects()` reads `~/.mb/projects.yaml` and returns list of dicts
- [ ] `parsers.project_context(path)` context manager overrides `_paths.project_root()`
- [ ] Static CSS served at `/static/style.css`
- [ ] Server gracefully handles missing `~/.mb/projects.yaml` (shows "no projects" page)

## Technical notes

- FastAPI + Jinja2Templates + StaticFiles mount
- Port 5111 to avoid conflict with common dev servers (3000, 5173, 8000)
- `__main__.py` checks for fastapi/uvicorn import and prints install hint if missing
- `parsers.project_context()` monkey-patches `scripts.v2_2._paths.project_root` temporarily
- Single-threaded uvicorn (no threading issues with monkey-patch)

## Testing

- Manual: `python3 -m scripts.dashboard` → open localhost:5111
- Verify redirect, verify CSS loads, verify sidebar renders
- Test with 0 projects registered (graceful fallback)
- Test with 2+ projects registered (correct first-project redirect)
