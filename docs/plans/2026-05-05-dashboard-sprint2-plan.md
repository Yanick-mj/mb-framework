# Dashboard Sprint 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the mb-dashboard MVP by adding the Roadmap page, Inbox page, multi-project switcher polish, and CLI entry points (stories D4, D5, D7, D8).

**Architecture:** Extend the existing `scripts/dashboard/` FastAPI layer from Sprint 1. New `get_roadmap_data()` parser for `_roadmap.md`. New routes + templates for roadmap and inbox. Shell helper update for `mb dashboard`.

**Tech Stack:** Python 3.13, FastAPI, Jinja2, HTMX (CDN), uvicorn, pytest + httpx (test), markdown (for fallback rendering)

**TDD:** Tests for parsers (unit) and routes (integration via TestClient) written BEFORE implementation.

**Repo:** `/Users/yanickmingala/code/Yanick-mj/mb-framework` on branch `feat/dashboard-mvp`

**Existing code to extend:**
- `scripts/dashboard/parsers.py` — add `get_roadmap_data()`
- `scripts/dashboard/server.py` — add roadmap, inbox routes + inbox partial
- `scripts/dashboard/tests/conftest.py` — add `write_roadmap()` helper
- `scripts/dashboard/tests/test_parsers.py` — add roadmap tests
- `scripts/dashboard/tests/test_routes.py` — add roadmap, inbox route tests
- `scripts/v2_1/mb_shell_helper.sh` — add `dashboard` subcommand
- `commands/dashboard.md` — new `/mb:dashboard` command

**CSS:** Already complete from Sprint 1 prototype extraction (roadmap + inbox styles included).

**Sprint 1 reference:** `docs/plans/2026-05-04-dashboard-sprint1-plan.md`

---

## Task 1: TDD `parsers.py` — `get_roadmap_data`

**Files:**
- Modify: `scripts/dashboard/tests/conftest.py`
- Modify: `scripts/dashboard/tests/test_parsers.py`
- Modify: `scripts/dashboard/parsers.py`

**Step 1: Add `write_roadmap` helper to conftest.py**

Append to `scripts/dashboard/tests/conftest.py`:

```python
def write_roadmap(root: Path, mission: str = "", phases: list[dict] | None = None) -> None:
    """Helper: write a _roadmap.md file."""
    lines = ["# Roadmap — Test Project", ""]
    if mission:
        lines += ["## Mission", "", mission, ""]
    if phases:
        lines += ["---", "", "## Phases", ""]
        for p in phases:
            lines.append(f"### Phase {p.get('num', '?')} — {p.get('name', 'Unnamed')} ({p.get('timeframe', 'TBD')})")
            lines.append("")
            if p.get("goal"):
                lines.append(f"**Goal:** {p['goal']}")
                lines.append("")
            if p.get("tracks"):
                lines.append("| Track | Work | Owner |")
                lines.append("|---|---|---|")
                for t in p["tracks"]:
                    lines.append(f"| {t[0]} | {t[1]} | {t[2]} |")
                lines.append("")
            if p.get("exit"):
                lines.append(f"**Exit criteria:** {p['exit']}")
                lines.append("")
    (root / "_roadmap.md").write_text("\n".join(lines))
```

**Step 2: Write failing tests**

Append to `scripts/dashboard/tests/test_parsers.py`:

```python
from scripts.dashboard.tests.conftest import write_roadmap


class TestGetRoadmapData:
    def test_parses_mission(self, tmp_project):
        write_roadmap(tmp_project, mission="Build the best thing ever.")
        result = parsers.get_roadmap_data(tmp_project)
        assert result["mission"] == "Build the best thing ever."

    def test_parses_phases(self, tmp_project):
        write_roadmap(tmp_project, mission="Ship it.", phases=[
            {
                "num": 1, "name": "Foundation", "timeframe": "weeks 1-2",
                "goal": "Get the basics working",
                "tracks": [["Backend", "API endpoints", "Alice"], ["Frontend", "UI components", "Bob"]],
                "exit": "All tests green",
            },
            {
                "num": 2, "name": "Polish", "timeframe": "weeks 3-4",
                "goal": "Make it beautiful",
                "tracks": [["Design", "Visual polish", "Carol"]],
                "exit": "User approval",
            },
        ])
        result = parsers.get_roadmap_data(tmp_project)
        assert len(result["phases"]) == 2
        p1 = result["phases"][0]
        assert p1["name"] == "Foundation"
        assert p1["goal"] == "Get the basics working"
        assert len(p1["tracks"]) == 2
        assert p1["tracks"][0] == {"track": "Backend", "work": "API endpoints", "owner": "Alice"}
        assert p1["exit"] == "All tests green"
        assert p1["current"] is True
        p2 = result["phases"][1]
        assert p2["current"] is False

    def test_missing_roadmap_returns_empty(self, tmp_project):
        result = parsers.get_roadmap_data(tmp_project)
        assert result["mission"] == ""
        assert result["phases"] == []
        assert result["raw"] == ""

    def test_fallback_raw_for_non_standard_format(self, tmp_project):
        (tmp_project / "_roadmap.md").write_text("# My Custom Roadmap\n\nJust some freeform text.\n")
        result = parsers.get_roadmap_data(tmp_project)
        assert result["mission"] == ""
        assert result["phases"] == []
        assert "freeform text" in result["raw"]
```

**Step 3: Run — expect FAIL**

Run: `cd /Users/yanickmingala/code/Yanick-mj/mb-framework && python3 -m pytest scripts/dashboard/tests/test_parsers.py::TestGetRoadmapData -v`
Expected: FAIL — `AttributeError: module 'scripts.dashboard.parsers' has no attribute 'get_roadmap_data'`

**Step 4: Implement**

Add to `scripts/dashboard/parsers.py`:

```python
def get_roadmap_data(path: Path) -> dict[str, Any]:
    """Parse _roadmap.md into structured roadmap data."""
    roadmap_file = path / "_roadmap.md"
    if not roadmap_file.exists():
        return {"mission": "", "phases": [], "raw": ""}

    text = roadmap_file.read_text()
    mission = _extract_roadmap_mission(text)
    phases = _extract_roadmap_phases(text)

    return {
        "mission": mission,
        "phases": phases,
        "raw": text if not mission and not phases else "",
    }


def _extract_roadmap_mission(text: str) -> str:
    """Extract text under ## Mission header."""
    m = re.search(r"^## Mission\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return ""
    return m.group(1).strip().strip("<!-- -->").strip()


def _extract_roadmap_phases(text: str) -> list[dict[str, Any]]:
    """Extract ### Phase N sections with goal, tracks table, exit criteria."""
    phases = []
    pattern = r"^### Phase (\d+)\s*[—–-]\s*(.+?)(?:\(([^)]+)\))?\s*$"
    parts = re.split(pattern, text, flags=re.MULTILINE)
    # parts: [pre, num1, name1, timeframe1, body1, num2, name2, timeframe2, body2, ...]
    for i in range(1, len(parts) - 3, 4):
        num = parts[i].strip()
        name = parts[i + 1].strip()
        timeframe = (parts[i + 2] or "").strip()
        body = parts[i + 3]

        goal = ""
        gm = re.search(r"\*\*Goal:\*\*\s*(.+)", body)
        if gm:
            goal = gm.group(1).strip()

        tracks = []
        # Parse markdown table rows (skip header + separator)
        table_rows = re.findall(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|$", body, re.MULTILINE)
        for row in table_rows:
            cells = [c.strip() for c in row]
            if cells[0].startswith("---") or cells[0].lower() == "track":
                continue
            tracks.append({"track": cells[0], "work": cells[1], "owner": cells[2]})

        exit_criteria = ""
        em = re.search(r"\*\*Exit criteria:\*\*\s*(.+)", body)
        if em:
            exit_criteria = em.group(1).strip()

        phases.append({
            "num": num,
            "name": name,
            "timeframe": timeframe,
            "goal": goal,
            "tracks": tracks,
            "exit": exit_criteria,
            "current": len(phases) == 0,
        })

    return phases
```

**Step 5: Run — expect PASS**

Run: `cd /Users/yanickmingala/code/Yanick-mj/mb-framework && python3 -m pytest scripts/dashboard/tests/test_parsers.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add scripts/dashboard/parsers.py scripts/dashboard/tests/test_parsers.py scripts/dashboard/tests/conftest.py
git commit -m "feat(dashboard): D4.1 — get_roadmap_data parser (TDD)"
```

---

## Task 2: TDD routes — roadmap page + partial

**Files:**
- Modify: `scripts/dashboard/tests/test_routes.py`
- Modify: `scripts/dashboard/server.py`
- Create: `scripts/dashboard/templates/roadmap.html`
- Create: `scripts/dashboard/templates/partials/roadmap_content.html`

**Step 1: Write failing tests**

Add import at top of `test_routes.py`:

```python
from scripts.dashboard.tests.conftest import (
    register_projects, write_story, write_runs, write_roadmap,
)
```

Append to `test_routes.py`:

```python
class TestRoadmapPage:
    def test_returns_200_with_mission(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        write_roadmap(tmp_project, mission="Build greatness.")
        client = TestClient(app)
        resp = client.get("/projects/demo/roadmap")
        assert resp.status_code == 200
        assert "Build greatness" in resp.text

    def test_unknown_project_returns_404(self, tmp_home):
        client = TestClient(app)
        resp = client.get("/projects/nope/roadmap")
        assert resp.status_code == 404

    def test_missing_roadmap_returns_200(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        client = TestClient(app)
        resp = client.get("/projects/demo/roadmap")
        assert resp.status_code == 200


class TestRoadmapPartial:
    def test_roadmap_partial(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        write_roadmap(tmp_project, mission="Ship it.", phases=[
            {"num": 1, "name": "Foundation", "timeframe": "weeks 1-2",
             "goal": "Basics", "tracks": [["BE", "API", "Alice"]], "exit": "Tests green"},
        ])
        client = TestClient(app)
        resp = client.get("/partials/demo/roadmap")
        assert resp.status_code == 200
        assert "Foundation" in resp.text
```

**Step 2: Run — expect FAIL**

Run: `python3 -m pytest scripts/dashboard/tests/test_routes.py::TestRoadmapPage -v`
Expected: FAIL — 404 (no route)

**Step 3: Add routes to server.py**

```python
@app.get("/projects/{name}/roadmap", response_class=HTMLResponse)
def roadmap(request: Request, name: str):
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    path = Path(project["path"])
    return templates.TemplateResponse(request, "roadmap.html", context={
        "project": project,
        "roadmap": parsers.get_roadmap_data(path),
        "projects": parsers.load_projects(),
        "current_page": "roadmap",
        "inbox_count": parsers.get_inbox_data(path)["total"],
    })


@app.get("/partials/{name}/roadmap", response_class=HTMLResponse)
def partial_roadmap(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/roadmap_content.html", context={
        "roadmap": parsers.get_roadmap_data(path),
    })
```

**Step 4: Create templates**

`scripts/dashboard/templates/roadmap.html`:

```html
{% extends "base.html" %}
{% block page_title %}Roadmap{% endblock %}
{% block page_subtitle %}Mission & milestones{% endblock %}

{% block content %}
<div hx-get="/partials/{{ project.name }}/roadmap"
     hx-trigger="every 5s"
     hx-swap="innerHTML">
  {% include "partials/roadmap_content.html" %}
</div>
{% endblock %}
```

`scripts/dashboard/templates/partials/roadmap_content.html`:

```html
{% if roadmap.mission %}
<div class="mission-card">
  <div class="mission-overline">Mission</div>
  <div class="mission-text">{{ roadmap.mission }}</div>
</div>
{% endif %}

{% if roadmap.phases %}
<div class="section-label">Milestones</div>
{% for phase in roadmap.phases %}
{% if not loop.first %}
<div class="ms-connector"><div class="vline"></div></div>
{% endif %}
<div class="milestone-card {{ 'current-ms' if phase.current else 'next-ms' }}">
  <div class="milestone-tag {{ 'curr' if phase.current else 'nxt' }}">{{ 'Current' if phase.current else 'Next' }}</div>
  <h3>Phase {{ phase.num }} — {{ phase.name }}</h3>
  {% if phase.goal %}<p>{{ phase.goal }}{% if phase.timeframe %} ({{ phase.timeframe }}){% endif %}</p>{% endif %}
  {% if phase.tracks %}
  <table class="tracks-table">
    <thead><tr><th>Track</th><th>Work</th><th>Owner</th></tr></thead>
    <tbody>
      {% for t in phase.tracks %}
      <tr><td>{{ t.track }}</td><td>{{ t.work }}</td><td>{{ t.owner }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
  {% endif %}
  {% if phase.exit %}<p style="margin-top:12px;font-size:12px;color:var(--text-tertiary)"><strong>Exit:</strong> {{ phase.exit }}</p>{% endif %}
</div>
{% endfor %}

{% elif roadmap.raw %}
<div class="mission-card">
  <div class="mission-overline">Roadmap</div>
  <div class="mission-text" style="font-size:14px;white-space:pre-wrap">{{ roadmap.raw }}</div>
</div>

{% else %}
<div style="padding:48px;text-align:center;color:var(--text-tertiary)">
  <p>No roadmap yet. Create <code>_roadmap.md</code> in your project root.</p>
</div>
{% endif %}
```

**Step 5: Add Roadmap nav link to base.html sidebar**

In `scripts/dashboard/templates/base.html`, add after the Board link:

```html
<a class="sidebar-item {{ 'active' if current_page == 'roadmap' else '' }}" href="/projects/{{ project.name }}/roadmap">
  <span class="icon">&#9656;</span> Roadmap
</a>
```

**Step 6: Run — expect PASS**

Run: `python3 -m pytest scripts/dashboard/tests/ -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add scripts/dashboard/
git commit -m "feat(dashboard): D4 — roadmap page + partial (TDD)"
```

---

## Task 3: TDD routes — inbox page + partial

**Files:**
- Modify: `scripts/dashboard/tests/test_routes.py`
- Modify: `scripts/dashboard/server.py`
- Create: `scripts/dashboard/templates/inbox.html`
- Create: `scripts/dashboard/templates/partials/inbox_items.html`

**Step 1: Write failing tests**

Append to `test_routes.py`:

```python
class TestInboxPage:
    def test_returns_200_with_items(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        write_story(tmp_project, "S1", "in_review", "Review This")
        client = TestClient(app)
        resp = client.get("/projects/demo/inbox")
        assert resp.status_code == 200
        assert "Review This" in resp.text or "in_review" in resp.text.lower()

    def test_empty_inbox_returns_200(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        client = TestClient(app)
        resp = client.get("/projects/demo/inbox")
        assert resp.status_code == 200
        assert "clear" in resp.text.lower() or "nothing" in resp.text.lower()

    def test_unknown_project_returns_404(self, tmp_home):
        client = TestClient(app)
        resp = client.get("/projects/nope/inbox")
        assert resp.status_code == 404


class TestInboxPartial:
    def test_inbox_partial(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        write_story(tmp_project, "S1", "blocked", "Stuck Item")
        client = TestClient(app)
        resp = client.get("/partials/demo/inbox")
        assert resp.status_code == 200
```

**Step 2: Run — expect FAIL**

Run: `python3 -m pytest scripts/dashboard/tests/test_routes.py::TestInboxPage -v`
Expected: FAIL — 404 (no route)

**Step 3: Add routes to server.py**

```python
@app.get("/projects/{name}/inbox", response_class=HTMLResponse)
def inbox_page(request: Request, name: str):
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    path = Path(project["path"])
    inbox_data = parsers.get_inbox_data(path)
    return templates.TemplateResponse(request, "inbox.html", context={
        "project": project,
        "inbox": inbox_data,
        "projects": parsers.load_projects(),
        "current_page": "inbox",
        "inbox_count": inbox_data["total"],
    })


@app.get("/partials/{name}/inbox", response_class=HTMLResponse)
def partial_inbox(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/inbox_items.html", context={
        "inbox": parsers.get_inbox_data(path),
        "project": {"name": name},
    })
```

**Step 4: Create templates**

`scripts/dashboard/templates/inbox.html`:

```html
{% extends "base.html" %}
{% block page_title %}Inbox{% endblock %}
{% block page_subtitle %}Items that need attention{% endblock %}

{% block content %}
<div hx-get="/partials/{{ project.name }}/inbox"
     hx-trigger="every 5s"
     hx-swap="innerHTML">
  {% include "partials/inbox_items.html" %}
</div>
{% endblock %}
```

`scripts/dashboard/templates/partials/inbox_items.html`:

```html
{% if inbox.total == 0 %}
<div class="inbox-empty-state">
  <div class="empty-icon">&#9745;</div>
  <p>Inbox clear — nothing needs your attention right now.</p>
</div>
{% else %}

{% if inbox.in_review %}
<div class="inbox-group">
  <div class="inbox-group-head">
    <div class="gh-icon" style="background:var(--orange-light);color:var(--orange)">&#9679;</div>
    <h2>In Review</h2>
    <span class="gh-count">{{ inbox.in_review | length }}</span>
  </div>
  {% for s in inbox.in_review %}
  <div class="inbox-row"
       hx-get="/partials/{{ project.name }}/story/{{ s.story_id }}"
       hx-target="#modal-container"
       hx-swap="innerHTML">
    <span class="row-id">{{ s.story_id }}</span>
    <span class="row-title">{{ s.title or s.story_id }}</span>
    <span class="row-badge" style="background:var(--orange-light);color:var(--orange)">{{ s.priority or 'medium' }}</span>
  </div>
  {% endfor %}
</div>
{% endif %}

{% if inbox.blocked %}
<div class="inbox-group">
  <div class="inbox-group-head">
    <div class="gh-icon" style="background:var(--red-light);color:var(--red)">&#9632;</div>
    <h2>Blocked</h2>
    <span class="gh-count">{{ inbox.blocked | length }}</span>
  </div>
  {% for s in inbox.blocked %}
  <div class="inbox-row"
       hx-get="/partials/{{ project.name }}/story/{{ s.story_id }}"
       hx-target="#modal-container"
       hx-swap="innerHTML">
    <span class="row-id">{{ s.story_id }}</span>
    <span class="row-title">{{ s.title or s.story_id }}</span>
    <span class="row-badge" style="background:var(--red-light);color:var(--red)">{{ s.priority or 'medium' }}</span>
  </div>
  {% endfor %}
</div>
{% endif %}

{% if inbox.approvals %}
<div class="inbox-group">
  <div class="inbox-group-head">
    <div class="gh-icon" style="background:var(--teal-light);color:var(--teal)">&#9201;</div>
    <h2>Approvals pending</h2>
    <span class="gh-count">{{ inbox.approvals | length }}</span>
  </div>
  {% for a in inbox.approvals %}
  <div class="inbox-row">
    <span class="row-id">{{ a._name or 'approve' }}</span>
    <span class="row-title">{{ a.title or a._name or 'Pending approval' }}</span>
    <span class="row-badge" style="background:var(--teal-light);color:var(--teal)">pending</span>
  </div>
  {% endfor %}
</div>
{% endif %}

{% endif %}
```

**Step 5: Update sidebar Inbox link in base.html**

Replace the existing Inbox sidebar link with:

```html
<a class="sidebar-item {{ 'active' if current_page == 'inbox' else '' }}" href="/projects/{{ project.name }}/inbox">
  <span class="icon">&#9993;</span> Inbox
  <span class="badge" hx-get="/partials/{{ project.name }}/inbox-count" hx-trigger="every 5s" hx-swap="innerHTML">{{ inbox_count }}</span>
</a>
```

**Step 6: Run — expect PASS**

Run: `python3 -m pytest scripts/dashboard/tests/ -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add scripts/dashboard/
git commit -m "feat(dashboard): D5 — inbox page + partial (TDD)"
```

---

## Task 4: Multi-project switcher polish (D7 completion)

**Files:**
- Modify: `scripts/dashboard/tests/test_routes.py`
- Modify: `scripts/dashboard/templates/base.html`

**Step 1: Write tests for project switching**

Append to `test_routes.py`:

```python
class TestMultiProjectSwitcher:
    def test_switcher_shows_all_projects(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "alpha", "path": str(tmp_project), "stage": "mvp"},
            {"name": "beta", "path": str(tmp_project), "stage": "scale"},
        ])
        client = TestClient(app)
        resp = client.get("/projects/alpha/overview")
        assert resp.status_code == 200
        assert "alpha" in resp.text
        assert "beta" in resp.text

    def test_switcher_links_preserve_current_page(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "alpha", "path": str(tmp_project), "stage": "mvp"},
            {"name": "beta", "path": str(tmp_project), "stage": "scale"},
        ])
        client = TestClient(app)
        resp = client.get("/projects/alpha/board")
        assert resp.status_code == 200
        assert "/projects/beta/board" in resp.text

    def test_single_project_no_dropdown(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "solo", "path": str(tmp_project), "stage": "mvp"},
        ])
        client = TestClient(app)
        resp = client.get("/projects/solo/overview")
        assert resp.status_code == 200
        assert "project-dropdown" not in resp.text
```

**Step 2: Run tests**

Run: `python3 -m pytest scripts/dashboard/tests/test_routes.py::TestMultiProjectSwitcher -v`

These should already PASS if `base.html` is correctly implemented from Sprint 1. If any fail, fix the template.

**Step 3: Verify HTMX polling on all pages**

Verify that `roadmap.html` and `inbox.html` also have HTMX polling wired up (already done in Tasks 2-3). Verify sidebar inbox badge polls on all pages (already in `base.html`).

**Step 4: Commit (only if changes needed)**

```bash
git add scripts/dashboard/
git commit -m "feat(dashboard): D7 — multi-project switcher tests + polish"
```

---

## Task 5: Entry points — `/mb:dashboard` command

**Files:**
- Create: `commands/dashboard.md`

**Step 1: Create the command file**

```markdown
---
name: 'dashboard'
description: 'Launch the mb-dashboard browser UI on localhost:5111'
allowed-tools: ['Bash']
---

# /mb:dashboard

Launch the browser-based dashboard.

## Usage

```
/mb:dashboard
/mb:dashboard --port 8080
```

## Process

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -m scripts.dashboard "$@"
```
```

**Step 2: Commit**

```bash
git add commands/dashboard.md
git commit -m "feat(dashboard): D8.1 — /mb:dashboard command"
```

---

## Task 6: Entry points — `mb dashboard` shell helper

**Files:**
- Modify: `scripts/v2_1/mb_shell_helper.sh`
- Modify: `scripts/dashboard/__main__.py`

**Step 1: Add `dashboard` case to shell helper**

In `scripts/v2_1/mb_shell_helper.sh`, add a new case before `*)`:

```bash
    dashboard)
      shift
      local port="${MB_DASHBOARD_PORT:-5111}"
      if [[ "$1" == "--port" && -n "$2" ]]; then
        port="$2"
        shift 2
      fi
      PYTHONPATH="$mb_repo" python3 -m scripts.dashboard --port "$port" &
      local pid=$!
      sleep 1
      python3 -m webbrowser "http://localhost:$port" 2>/dev/null
      echo "mb-dashboard running on http://localhost:$port (PID: $pid)"
      echo "Press Ctrl+C to stop."
      wait $pid
      return 0
      ;;
```

**Step 2: Update help text**

In the help case, add:

```bash
      echo "mb dashboard — launch browser dashboard on localhost:5111"
```

**Step 3: Commit**

```bash
git add scripts/v2_1/mb_shell_helper.sh
git commit -m "feat(dashboard): D8.2 — mb dashboard shell helper"
```

---

## Task 7: Full test suite + smoke test

**Files:** None (verification only)

**Step 1: Run all dashboard tests**

Run: `cd /Users/yanickmingala/code/Yanick-mj/mb-framework && python3 -m pytest scripts/dashboard/tests/ -v`
Expected: All tests PASS

**Step 2: Run v2.1 + v2.2 regression tests**

Run: `python3 -m pytest scripts/v2_1/tests/ scripts/v2_2/tests/ -v`
Expected: All existing tests still PASS

**Step 3: Manual smoke test with Playwright**

1. Start server: `python3 -m scripts.dashboard`
2. Open http://localhost:5111
3. Verify redirect to first project's overview
4. Check: stage badge, stats grid, runs table
5. Click "Board" — verify kanban columns with cards
6. Click a story card — verify modal opens, close with Escape
7. Click "Roadmap" — verify mission card + milestones (or empty state)
8. Click "Inbox" — verify sections or empty state
9. If multiple projects registered: test project switcher dropdown
10. Wait 5s — verify HTMX polling fires on network tab
11. Test `mb dashboard` from terminal (if shell helper sourced)

**Step 4: Commit any fixes found**

---

## Task 8: Sprint 2 summary commit

**Step 1: Review all files for leftover debug code, TODOs, print statements**

**Step 2: Final commit**

```bash
git add -A
git commit -m "feat(dashboard): Sprint 2 complete — D4+D5+D7+D8

Delivers:
- Roadmap page (mission card, milestone cards, tracks tables)
- Inbox page (in_review, blocked, approvals sections)
- Multi-project switcher with page-preserving navigation
- /mb:dashboard command + mb dashboard shell helper
- TDD test suite extended for all new routes + parsers"
```
