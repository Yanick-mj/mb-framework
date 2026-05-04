# mb-dashboard MVP — Implementation Plan

**Goal:** Add a browser-based dashboard to the mb-framework that reads project markdown files and presents them as a visual interface for non-technical team members.

**Architecture:** FastAPI server + Jinja2 templates + HTMX polling. Reuses existing Python parsers (board.py, inbox.py, runs.py, projects.py). Served at localhost:5111.

**Tech stack:** Python 3.10+, FastAPI, uvicorn, Jinja2, HTMX (CDN), pyyaml, markdown

**Design validated:** Prototype at `mb-bench/prototype-dashboard.html` — Notion + BlaBlaCar + Apple aesthetic (light mode, warm palette, sidebar navigation, frosted glass modals)

**Entry points:** `/mb:dashboard` command + `mb dashboard` shell helper

---

## Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Location | In mb-framework repo | Part of the framework, ships with install |
| 2 | Backend | FastAPI | Reuses existing Python modules directly |
| 3 | Frontend | HTMX + Jinja2 | Server-rendered, 0 JS to maintain, Notion-like feel |
| 4 | Live updates | HTMX polling (5s) | `hx-trigger="every 5s"` — free, no deps |
| 5 | Multi-project | Read `~/.mb/projects.yaml` | Existing registry, single source of truth |
| 6 | Launch | Both CLI + command | `/mb:dashboard` + `mb dashboard` |
| 7 | Scope | 5 features | Overview, Board, Roadmap, Inbox, Multi-project |

---

## Stories (execution order)

Stories are filed in `_backlog/` with IDs STU-D1 through STU-D8.
Execute sequentially via `/mb:sprint` or `/mb:feature`.

### STU-D1: Server skeleton + project loader
Foundation: FastAPI app, Jinja2 setup, static files, project registry loader.

### STU-D2: Overview page
Stage badge, stats grid, progress bar, upgrade criteria — parsed from mb-stage.yaml + stories.

### STU-D3: Kanban board page
5-column board parsed from stories. Cards with priority, labels, click-to-open.

### STU-D4: Roadmap page
Mission + milestones parsed from `_roadmap.md`. Current/next with tracks table.

### STU-D5: Inbox page
In-review + blocked + approvals-pending. Reuses inbox.py scanner.

### STU-D6: Story detail modal
HTMX-powered modal showing full markdown content of a story (why, scope, criteria).

### STU-D7: Multi-project switcher + HTMX polling
Project dropdown, URL-based routing, hx-trigger polling on all partials.

### STU-D8: Entry points + install integration
`commands/dashboard.md`, `mb dashboard` in shell helper, deps check at startup.

---

## File structure (target)

```
scripts/dashboard/
├── __init__.py
├── __main__.py           # python3 -m scripts.dashboard → starts uvicorn
├── server.py             # FastAPI app, routes, Jinja config
├── parsers.py            # Multi-project wrappers around existing modules
├── templates/
│   ├── base.html         # Layout + sidebar + HTMX CDN + CSS
│   ├── overview.html
│   ├── board.html
│   ├── roadmap.html
│   ├── inbox.html
│   └── partials/
│       ├── stage_badge.html
│       ├── stats_grid.html
│       ├── board_columns.html
│       ├── runs_table.html
│       ├── inbox_items.html
│       └── story_modal.html
└── static/
    └── style.css
```

Plus:
- `commands/dashboard.md`
- Update to `scripts/v2_1/mb_shell_helper.sh`

---

## Key technical decisions

### Multi-project without modifying existing modules

`parsers.py` uses a context manager that temporarily overrides `_paths.project_root()` to point to the selected project's path:

```python
@contextmanager
def project_context(project_path: Path):
    original = _paths.project_root
    _paths.project_root = lambda: project_path
    try:
        yield
    finally:
        _paths.project_root = original
```

### Roadmap parsing

`_roadmap.md` is freeform markdown. Parser extracts:
- H2 "Mission" → text below
- H3 sections matching "Phase N" or milestone pattern → structured data
- Tables within milestones → tracks

### CSS from prototype

The validated prototype CSS is extracted into `static/style.css` — same Notion+BlaBlaCar+Apple aesthetic.
