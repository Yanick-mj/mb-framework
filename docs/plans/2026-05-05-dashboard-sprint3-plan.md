# Sprint 3 — Sprint Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add sprint management to the dashboard — data model, list page, detail page (kanban + list views), roadmap integration, and CRUD operations.

**Architecture:** Extend existing `parsers.py`, `crud.py`, and `server.py`. Sprint data stored as YAML files in `{project}/_sprints/sprint-{N}.yaml`. Stories get optional `sprint` backref in frontmatter. Reuse existing stat-card, board-column, and modal patterns from Sprint 1-2.

**Tech Stack:** FastAPI, Jinja2, HTMX, YAML, pytest (TDD)

**Backlog tickets:** STU-P2S3.1 through STU-P2S3.5 (see `_backlog/STU-P2S3-*.md`)

**Run all tests:** `python3 -m pytest scripts/dashboard/tests/ -v`

---

## Task 1: Sprint Data Model — Parsers (STU-P2S3.1a)

**Files:**
- Create: `scripts/dashboard/tests/test_sprint_model.py`
- Modify: `scripts/dashboard/parsers.py`
- Modify: `scripts/dashboard/tests/conftest.py`

### Step 1: Add `write_sprint` helper to conftest

Add to `scripts/dashboard/tests/conftest.py`:

```python
def write_sprint(root: Path, sprint_id: str, name: str, goal: str,
                 status: str = "planned", phase: str = "Phase 1",
                 start_date: str = "2026-05-01", end_date: str = "2026-05-03",
                 stories: list[str] | None = None) -> None:
    """Helper: write a sprint YAML file to _sprints/."""
    d = root / "_sprints"
    d.mkdir(parents=True, exist_ok=True)
    data = {
        "id": sprint_id,
        "name": name,
        "goal": goal,
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
        "phase": phase,
        "stories": stories or [],
    }
    (d / f"{sprint_id}.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
```

### Step 2: Write failing tests for `load_sprints` and `get_sprint`

Create `scripts/dashboard/tests/test_sprint_model.py`:

```python
"""TDD tests for sprint data model — STU-P2S3.1."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_sprint, write_story


class TestLoadSprints:
    def test_returns_empty_list_when_no_sprints(self, tmp_project):
        from scripts.dashboard.parsers import load_sprints
        assert load_sprints(tmp_project) == []

    def test_returns_sprints_sorted_by_start_date(self, tmp_project):
        from scripts.dashboard.parsers import load_sprints
        write_sprint(tmp_project, "sprint-2", "Second", "Goal B",
                     start_date="2026-05-04")
        write_sprint(tmp_project, "sprint-1", "First", "Goal A",
                     start_date="2026-05-01")
        result = load_sprints(tmp_project)
        assert len(result) == 2
        assert result[0]["id"] == "sprint-1"
        assert result[1]["id"] == "sprint-2"

    def test_sprint_has_all_fields(self, tmp_project):
        from scripts.dashboard.parsers import load_sprints
        write_sprint(tmp_project, "sprint-1", "My Sprint", "Build things",
                     status="active", phase="Phase 2",
                     start_date="2026-05-01", end_date="2026-05-03",
                     stories=["S1", "S2"])
        result = load_sprints(tmp_project)
        s = result[0]
        assert s["id"] == "sprint-1"
        assert s["name"] == "My Sprint"
        assert s["goal"] == "Build things"
        assert s["status"] == "active"
        assert s["phase"] == "Phase 2"
        assert s["stories"] == ["S1", "S2"]

    def test_ignores_non_yaml_files(self, tmp_project):
        from scripts.dashboard.parsers import load_sprints
        d = tmp_project / "_sprints"
        d.mkdir(parents=True, exist_ok=True)
        (d / "README.md").write_text("# Sprints")
        write_sprint(tmp_project, "sprint-1", "Real", "Goal")
        result = load_sprints(tmp_project)
        assert len(result) == 1

    def test_ignores_malformed_yaml(self, tmp_project):
        from scripts.dashboard.parsers import load_sprints
        d = tmp_project / "_sprints"
        d.mkdir(parents=True, exist_ok=True)
        (d / "bad.yaml").write_text(":::: not valid yaml {{{")
        write_sprint(tmp_project, "sprint-1", "Good", "Goal")
        result = load_sprints(tmp_project)
        assert len(result) == 1


class TestGetSprint:
    def test_returns_sprint_by_id(self, tmp_project):
        from scripts.dashboard.parsers import get_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint One", "Goal")
        result = get_sprint(tmp_project, "sprint-1")
        assert result is not None
        assert result["id"] == "sprint-1"
        assert result["name"] == "Sprint One"

    def test_returns_none_for_unknown_id(self, tmp_project):
        from scripts.dashboard.parsers import get_sprint
        assert get_sprint(tmp_project, "nope") is None

    def test_resolves_story_objects(self, tmp_project):
        from scripts.dashboard.parsers import get_sprint
        write_story(tmp_project, "S1", "done", "Story One", "high")
        write_story(tmp_project, "S2", "todo", "Story Two", "medium")
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     stories=["S1", "S2"])
        result = get_sprint(tmp_project, "sprint-1")
        resolved = result["resolved_stories"]
        assert len(resolved) == 2
        assert resolved[0]["story_id"] == "S1"
        assert resolved[0]["title"] == "Story One"
        assert resolved[0]["status"] == "done"

    def test_unresolved_stories_included_as_stubs(self, tmp_project):
        from scripts.dashboard.parsers import get_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     stories=["MISSING"])
        result = get_sprint(tmp_project, "sprint-1")
        resolved = result["resolved_stories"]
        assert len(resolved) == 1
        assert resolved[0]["story_id"] == "MISSING"
        assert resolved[0]["status"] == "unknown"


class TestGetSprintsData:
    def test_returns_sprints_with_completion(self, tmp_project):
        from scripts.dashboard.parsers import get_sprints_data
        write_story(tmp_project, "S1", "done", "Done")
        write_story(tmp_project, "S2", "todo", "Todo")
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     status="active", stories=["S1", "S2"])
        result = get_sprints_data(tmp_project)
        assert len(result) == 1
        s = result[0]
        assert s["done_count"] == 1
        assert s["total_count"] == 2
        assert s["pct"] == 50

    def test_active_sprint_first(self, tmp_project):
        from scripts.dashboard.parsers import get_sprints_data
        write_sprint(tmp_project, "sprint-1", "Old", "Goal",
                     status="closed", start_date="2026-05-01")
        write_sprint(tmp_project, "sprint-2", "Active", "Goal",
                     status="active", start_date="2026-05-04")
        write_sprint(tmp_project, "sprint-3", "New", "Goal",
                     status="planned", start_date="2026-05-07")
        result = get_sprints_data(tmp_project)
        assert result[0]["status"] == "active"

    def test_empty_sprint_zero_pct(self, tmp_project):
        from scripts.dashboard.parsers import get_sprints_data
        write_sprint(tmp_project, "sprint-1", "Empty", "Goal")
        result = get_sprints_data(tmp_project)
        assert result[0]["pct"] == 0
        assert result[0]["total_count"] == 0
```

### Step 3: Run tests to verify they fail

Run: `python3 -m pytest scripts/dashboard/tests/test_sprint_model.py -v`
Expected: FAIL — `load_sprints`, `get_sprint`, `get_sprints_data` not defined

### Step 4: Implement parsers

Add to `scripts/dashboard/parsers.py` (after existing imports and before `get_inbox_data`):

```python
SPRINTS_SUBPATH = Path("_sprints")


def load_sprints(path: Path) -> list[dict[str, Any]]:
    """Load all sprint YAML files, sorted by start_date."""
    sprint_dir = path / SPRINTS_SUBPATH
    if not sprint_dir.exists():
        return []
    sprints = []
    for f in sorted(sprint_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text())
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict) or "id" not in data:
            continue
        sprints.append(data)
    sprints.sort(key=lambda s: str(s.get("start_date", "")))
    return sprints


def get_sprint(path: Path, sprint_id: str) -> dict[str, Any] | None:
    """Load a single sprint by ID with resolved story objects."""
    for sprint in load_sprints(path):
        if sprint["id"] == sprint_id:
            stories_index = {s["story_id"]: s for s in _scan_all_stories(path)}
            resolved = []
            for sid in sprint.get("stories", []):
                if sid in stories_index:
                    s = stories_index[sid]
                    resolved.append({
                        "story_id": s.get("story_id"),
                        "title": s.get("title", ""),
                        "status": s.get("status", "unknown"),
                        "priority": s.get("priority", "medium"),
                        "labels": s.get("labels", []),
                    })
                else:
                    resolved.append({
                        "story_id": sid,
                        "title": sid,
                        "status": "unknown",
                        "priority": "medium",
                        "labels": [],
                    })
            sprint["resolved_stories"] = resolved
            return sprint
    return None


def get_sprints_data(path: Path) -> list[dict[str, Any]]:
    """Load sprints with computed completion %, active sprint first."""
    stories_index = {s["story_id"]: s for s in _scan_all_stories(path)}
    sprints = load_sprints(path)
    result = []
    for s in sprints:
        story_ids = s.get("stories", [])
        done = sum(1 for sid in story_ids
                   if stories_index.get(sid, {}).get("status") == "done")
        total = len(story_ids)
        result.append({
            **s,
            "done_count": done,
            "total_count": total,
            "pct": round(done * 100 / total) if total else 0,
        })
    # Active sprint first, then by start_date descending
    result.sort(key=lambda x: (x["status"] != "active", str(x.get("start_date", ""))),
                reverse=False)
    # Within same active-flag group, newest first (except active stays top)
    active = [s for s in result if s["status"] == "active"]
    rest = [s for s in result if s["status"] != "active"]
    rest.sort(key=lambda x: str(x.get("start_date", "")), reverse=True)
    return active + rest
```

### Step 5: Run tests to verify they pass

Run: `python3 -m pytest scripts/dashboard/tests/test_sprint_model.py -v`
Expected: All PASS

### Step 6: Run full suite to check no regressions

Run: `python3 -m pytest scripts/dashboard/tests/ -v`
Expected: 127 existing + new tests all PASS

### Step 7: Commit

```bash
git add scripts/dashboard/parsers.py scripts/dashboard/tests/test_sprint_model.py scripts/dashboard/tests/conftest.py
git commit -m "feat(sprint3): add sprint parsers — load_sprints, get_sprint, get_sprints_data"
```

---

## Task 2: Sprint CRUD Operations (STU-P2S3.1b)

**Files:**
- Create: `scripts/dashboard/tests/test_sprint_crud.py`
- Modify: `scripts/dashboard/crud.py`

### Step 1: Write failing tests

Create `scripts/dashboard/tests/test_sprint_crud.py`:

```python
"""TDD tests for sprint CRUD — STU-P2S3.1."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_sprint, write_story


class TestCreateSprint:
    def test_creates_yaml_file(self, tmp_project):
        from scripts.dashboard.crud import create_sprint
        result = create_sprint(tmp_project, name="Sprint 1", goal="Ship it",
                               start_date="2026-05-01", end_date="2026-05-03",
                               phase="Phase 1")
        assert result["id"].startswith("sprint-")
        f = tmp_project / "_sprints" / f"{result['id']}.yaml"
        assert f.exists()
        data = yaml.safe_load(f.read_text())
        assert data["name"] == "Sprint 1"
        assert data["goal"] == "Ship it"
        assert data["status"] == "planned"

    def test_auto_increments_id(self, tmp_project):
        from scripts.dashboard.crud import create_sprint
        write_sprint(tmp_project, "sprint-1", "First", "Goal")
        write_sprint(tmp_project, "sprint-2", "Second", "Goal")
        result = create_sprint(tmp_project, name="Third", goal="Goal",
                               start_date="2026-05-07", end_date="2026-05-09",
                               phase="Phase 1")
        assert result["id"] == "sprint-3"


class TestCloseSprint:
    def test_sets_status_closed(self, tmp_project):
        from scripts.dashboard.crud import close_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        result = close_sprint(tmp_project, "sprint-1")
        assert result["status"] == "closed"
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert data["status"] == "closed"

    def test_sets_end_date_to_today(self, tmp_project):
        from scripts.dashboard.crud import close_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        result = close_sprint(tmp_project, "sprint-1")
        assert result["end_date"] is not None

    def test_returns_none_for_unknown(self, tmp_project):
        from scripts.dashboard.crud import close_sprint
        assert close_sprint(tmp_project, "nope") is None

    def test_cannot_close_already_closed(self, tmp_project):
        from scripts.dashboard.crud import close_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="closed")
        assert close_sprint(tmp_project, "sprint-1") is None


class TestAddStoryToSprint:
    def test_updates_sprint_yaml(self, tmp_project):
        from scripts.dashboard.crud import add_story_to_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=[])
        write_story(tmp_project, "S1", "todo", "Story One")
        result = add_story_to_sprint(tmp_project, "sprint-1", "S1")
        assert result is not None
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert "S1" in data["stories"]

    def test_updates_story_frontmatter(self, tmp_project):
        from scripts.dashboard.crud import add_story_to_sprint
        from scripts.dashboard.parsers import _parse_frontmatter
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=[])
        write_story(tmp_project, "S1", "todo", "Story One")
        add_story_to_sprint(tmp_project, "sprint-1", "S1")
        story_file = tmp_project / "_bmad-output" / "implementation-artifacts" / "stories" / "S1.md"
        fm = _parse_frontmatter(story_file.read_text())
        assert fm.get("sprint") == "sprint-1"

    def test_no_duplicate_if_already_in_sprint(self, tmp_project):
        from scripts.dashboard.crud import add_story_to_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=["S1"])
        write_story(tmp_project, "S1", "todo", "Story One")
        add_story_to_sprint(tmp_project, "sprint-1", "S1")
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert data["stories"].count("S1") == 1

    def test_returns_none_unknown_sprint(self, tmp_project):
        from scripts.dashboard.crud import add_story_to_sprint
        write_story(tmp_project, "S1", "todo", "Story")
        assert add_story_to_sprint(tmp_project, "nope", "S1") is None


class TestRemoveStoryFromSprint:
    def test_removes_from_sprint_yaml(self, tmp_project):
        from scripts.dashboard.crud import remove_story_from_sprint
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=["S1", "S2"])
        write_story(tmp_project, "S1", "todo", "Story One")
        result = remove_story_from_sprint(tmp_project, "sprint-1", "S1")
        assert result is not None
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert "S1" not in data["stories"]
        assert "S2" in data["stories"]

    def test_clears_story_sprint_field(self, tmp_project):
        from scripts.dashboard.crud import remove_story_from_sprint
        from scripts.dashboard.parsers import _parse_frontmatter
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=["S1"])
        write_story(tmp_project, "S1", "todo", "Story One")
        # First add the sprint field
        story_file = tmp_project / "_bmad-output" / "implementation-artifacts" / "stories" / "S1.md"
        text = story_file.read_text()
        text = text.replace("status: todo", "status: todo\nsprint: sprint-1")
        story_file.write_text(text)
        remove_story_from_sprint(tmp_project, "sprint-1", "S1")
        fm = _parse_frontmatter(story_file.read_text())
        assert "sprint" not in fm

    def test_returns_none_unknown_sprint(self, tmp_project):
        from scripts.dashboard.crud import remove_story_from_sprint
        assert remove_story_from_sprint(tmp_project, "nope", "S1") is None


class TestActiveSprintConstraint:
    def test_only_one_active_allowed(self, tmp_project):
        from scripts.dashboard.crud import create_sprint
        write_sprint(tmp_project, "sprint-1", "Active", "Goal", status="active")
        result = create_sprint(tmp_project, name="New", goal="Goal",
                               start_date="2026-05-04", end_date="2026-05-06",
                               phase="Phase 1", status="active")
        # Creating second active sprint should auto-close the first
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert data["status"] == "closed"
        assert result["status"] == "active"
```

### Step 2: Run tests to verify they fail

Run: `python3 -m pytest scripts/dashboard/tests/test_sprint_crud.py -v`
Expected: FAIL — `create_sprint`, `close_sprint`, etc. not defined

### Step 3: Implement CRUD functions

Add to `scripts/dashboard/crud.py` (after existing imports, add `from scripts.dashboard.parsers import SPRINTS_SUBPATH, load_sprints`):

```python
from scripts.dashboard.parsers import SPRINTS_SUBPATH, load_sprints


def _sprints_dir(project_path: Path) -> Path:
    d = project_path / SPRINTS_SUBPATH
    d.mkdir(parents=True, exist_ok=True)
    return d


def _next_sprint_id(project_path: Path) -> str:
    """Generate sprint-{max+1} ID."""
    existing = load_sprints(project_path)
    nums = []
    for s in existing:
        try:
            nums.append(int(s["id"].split("-")[1]))
        except (IndexError, ValueError):
            continue
    return f"sprint-{max(nums, default=0) + 1}"


def _write_sprint(project_path: Path, data: dict) -> None:
    """Atomically write a sprint YAML file."""
    _atomic_write(
        _sprints_dir(project_path) / f"{data['id']}.yaml",
        yaml.safe_dump(data, sort_keys=False),
    )


def create_sprint(
    project_path: Path,
    name: str,
    goal: str,
    start_date: str,
    end_date: str,
    phase: str,
    status: str = "planned",
) -> dict[str, Any]:
    """Create a new sprint YAML file."""
    sprint_id = _next_sprint_id(project_path)
    # If activating, close any existing active sprint
    if status == "active":
        _close_active_sprints(project_path)
    data = {
        "id": sprint_id,
        "name": name,
        "goal": goal,
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
        "phase": phase,
        "stories": [],
    }
    _write_sprint(project_path, data)
    return data


def _close_active_sprints(project_path: Path) -> None:
    """Close any currently active sprints."""
    for sprint in load_sprints(project_path):
        if sprint["status"] == "active":
            sprint["status"] = "closed"
            sprint["end_date"] = str(datetime.now(timezone.utc).date())
            _write_sprint(project_path, sprint)


def close_sprint(project_path: Path, sprint_id: str) -> dict | None:
    """Close a sprint: set status=closed and end_date=today."""
    sprint_dir = project_path / SPRINTS_SUBPATH
    f = sprint_dir / f"{sprint_id}.yaml"
    if not f.exists():
        return None
    data = yaml.safe_load(f.read_text())
    if data.get("status") == "closed":
        return None
    data["status"] = "closed"
    data["end_date"] = str(datetime.now(timezone.utc).date())
    _write_sprint(project_path, data)
    return data


def add_story_to_sprint(
    project_path: Path, sprint_id: str, story_id: str
) -> dict | None:
    """Add a story to a sprint. Updates both sprint YAML and story frontmatter."""
    sprint_file = project_path / SPRINTS_SUBPATH / f"{sprint_id}.yaml"
    if not sprint_file.exists():
        return None
    # Update sprint YAML
    data = yaml.safe_load(sprint_file.read_text())
    if story_id not in data.get("stories", []):
        data.setdefault("stories", []).append(story_id)
        _write_sprint(project_path, data)
    # Update story frontmatter
    story_file = _find_story_file(project_path, story_id)
    if story_file:
        result = _read_story(story_file)
        if result:
            fm, body = result
            fm["sprint"] = sprint_id
            clean = _clean_fm(fm, story_id)
            clean["sprint"] = sprint_id
            _atomic_write(story_file, _build_story_content(clean, body))
    return data


def remove_story_from_sprint(
    project_path: Path, sprint_id: str, story_id: str
) -> dict | None:
    """Remove a story from a sprint. Updates both files."""
    sprint_file = project_path / SPRINTS_SUBPATH / f"{sprint_id}.yaml"
    if not sprint_file.exists():
        return None
    # Update sprint YAML
    data = yaml.safe_load(sprint_file.read_text())
    stories = data.get("stories", [])
    if story_id in stories:
        stories.remove(story_id)
        data["stories"] = stories
        _write_sprint(project_path, data)
    # Clear sprint from story frontmatter
    story_file = _find_story_file(project_path, story_id)
    if story_file:
        result = _read_story(story_file)
        if result:
            fm, body = result
            fm.pop("sprint", None)
            clean = _clean_fm(fm, story_id)
            _atomic_write(story_file, _build_story_content(clean, body))
    return data
```

### Step 4: Run tests to verify they pass

Run: `python3 -m pytest scripts/dashboard/tests/test_sprint_crud.py -v`
Expected: All PASS

### Step 5: Run full suite

Run: `python3 -m pytest scripts/dashboard/tests/ -v`
Expected: All PASS, no regressions

### Step 6: Commit

```bash
git add scripts/dashboard/crud.py scripts/dashboard/tests/test_sprint_crud.py
git commit -m "feat(sprint3): add sprint CRUD — create, close, add/remove stories"
```

---

## Task 3: Sprints List Page (STU-P2S3.2)

**Files:**
- Create: `scripts/dashboard/tests/test_sprint_routes.py`
- Create: `scripts/dashboard/templates/sprints.html`
- Create: `scripts/dashboard/templates/partials/sprint_list.html`
- Modify: `scripts/dashboard/server.py`
- Modify: `scripts/dashboard/templates/base.html`

### Step 1: Write failing route tests

Create `scripts/dashboard/tests/test_sprint_routes.py`:

```python
"""TDD tests for sprint routes — STU-P2S3.2 + STU-P2S3.3."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_sprint, write_story


class TestSprintsListPage:
    def test_returns_200(self, client, tmp_project):
        resp = client.get("/projects/demo/sprints")
        assert resp.status_code == 200

    def test_shows_sprint_cards(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "CRUD", "Ship CRUD",
                     status="closed", phase="Phase 2")
        resp = client.get("/projects/demo/sprints")
        assert resp.status_code == 200
        assert "CRUD" in resp.text

    def test_active_sprint_has_active_class(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Active One", "Goal",
                     status="active")
        resp = client.get("/projects/demo/sprints")
        assert "active-sprint" in resp.text

    def test_shows_progress_info(self, client, tmp_project):
        write_story(tmp_project, "S1", "done", "Done Story")
        write_story(tmp_project, "S2", "todo", "Todo Story")
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     status="active", stories=["S1", "S2"])
        resp = client.get("/projects/demo/sprints")
        assert "1 / 2" in resp.text or "50%" in resp.text

    def test_empty_state_when_no_sprints(self, client, tmp_project):
        resp = client.get("/projects/demo/sprints")
        assert "no sprint" in resp.text.lower() or "No sprints" in resp.text

    def test_404_unknown_project(self, client):
        resp = client.get("/projects/nope/sprints")
        assert resp.status_code == 404

    def test_sidebar_has_sprints_link(self, client, tmp_project):
        resp = client.get("/projects/demo/sprints")
        assert "/projects/demo/sprints" in resp.text
        assert "Sprints" in resp.text


class TestSprintsPartial:
    def test_returns_sprint_list_html(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        resp = client.get("/partials/demo/sprints")
        assert resp.status_code == 200
        assert "sprint-1" in resp.text.lower() or "Sprint" in resp.text

    def test_404_unknown_project(self, client):
        resp = client.get("/partials/nope/sprints")
        assert resp.status_code == 404
```

### Step 2: Run tests to verify they fail

Run: `python3 -m pytest scripts/dashboard/tests/test_sprint_routes.py -v`
Expected: FAIL — 404 on `/projects/demo/sprints`

### Step 3: Add sidebar link

In `scripts/dashboard/templates/base.html`, add the Sprints link between Board and Roadmap:

```html
    <a class="sidebar-item {{ 'active' if current_page == 'sprints' else '' }}" href="/projects/{{ project.name }}/sprints">
      <span class="icon">&#9776;</span> Sprints
    </a>
```

### Step 4: Create sprint list partial

Create `scripts/dashboard/templates/partials/sprint_list.html`:

```html
{% if sprints %}
{% for s in sprints %}
<div class="sprint-card {{ 'active-sprint' if s.status == 'active' else '' }} {{ 'closed-sprint' if s.status == 'closed' else '' }}"
     onclick="window.location='/projects/{{ project.name }}/sprints/{{ s.id }}'">
  <div class="sprint-card-header">
    <h3>{{ s.name }}</h3>
    <span class="sprint-status-pill {{ s.status }}">{{ s.status }}</span>
  </div>
  <div class="sprint-goal">{{ s.goal }}</div>
  <div class="sprint-card-meta">
    <span class="mono">{{ s.start_date }} — {{ s.end_date }}</span>
    <span class="phase-tag">{{ s.phase }}</span>
    <span>{{ s.done_count }} / {{ s.total_count }} stories</span>
    <div class="progress-bar-wrap">
      <div class="progress-bar-fill {{ s.status }}" style="width: {{ s.pct }}%"></div>
    </div>
    <span class="mono">{{ s.pct }}%</span>
  </div>
</div>
{% endfor %}
{% else %}
<div class="empty-state">
  <div class="empty-icon">&#9776;</div>
  <h3>No sprints yet</h3>
  <p>Create your first sprint to start tracking progress.</p>
</div>
{% endif %}
```

### Step 5: Create sprints page template

Create `scripts/dashboard/templates/sprints.html`:

```html
{% extends "base.html" %}
{% block page_title %}Sprints{% endblock %}
{% block page_subtitle %}Track sprint progress and velocity{% endblock %}

{% block content %}
<div class="board-toolbar">
  <button class="btn btn-primary"
          hx-get="/partials/{{ project.name }}/create-sprint"
          hx-target="#modal-container"
          hx-swap="innerHTML">+ New Sprint</button>
</div>
<div class="sprint-list"
     hx-get="/partials/{{ project.name }}/sprints"
     hx-trigger="every 5s"
     hx-swap="innerHTML">
  {% include "partials/sprint_list.html" %}
</div>
{% endblock %}
```

### Step 6: Add routes to server.py

Add to `scripts/dashboard/server.py`:

```python
@app.get("/projects/{name}/sprints", response_class=HTMLResponse)
def sprints_page(request: Request, name: str):
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    path = Path(project["path"])
    return templates.TemplateResponse(request, "sprints.html", context={
        "project": project,
        "sprints": parsers.get_sprints_data(path),
        "projects": parsers.load_projects(),
        "current_page": "sprints",
        "inbox_count": parsers.get_inbox_data(path)["total"],
    })


@app.get("/partials/{name}/sprints", response_class=HTMLResponse)
def partial_sprints(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/sprint_list.html", context={
        "sprints": parsers.get_sprints_data(path),
        "project": {"name": name},
    })
```

### Step 7: Add sprint card CSS to style.css

Add the sprint card styles from the design (`.sprint-card`, `.sprint-status-pill`, `.sprint-goal`, `.sprint-card-meta`, `.phase-tag`, `.progress-bar-wrap`, `.progress-bar-fill`, `.empty-state`). Reference `docs/plans/sprint3-preview.html` for exact CSS.

### Step 8: Run tests to verify they pass

Run: `python3 -m pytest scripts/dashboard/tests/test_sprint_routes.py -v`
Expected: All PASS

### Step 9: Run full suite

Run: `python3 -m pytest scripts/dashboard/tests/ -v`
Expected: All PASS

### Step 10: Commit

```bash
git add scripts/dashboard/server.py scripts/dashboard/templates/ scripts/dashboard/static/style.css scripts/dashboard/tests/test_sprint_routes.py
git commit -m "feat(sprint3): add sprints list page with sidebar link"
```

---

## Task 4: Sprint Detail Page (STU-P2S3.3)

**Files:**
- Modify: `scripts/dashboard/tests/test_sprint_routes.py`
- Create: `scripts/dashboard/templates/sprint_detail.html`
- Create: `scripts/dashboard/templates/partials/sprint_detail_content.html`
- Modify: `scripts/dashboard/server.py`

### Step 1: Add failing tests to test_sprint_routes.py

Append to `scripts/dashboard/tests/test_sprint_routes.py`:

```python
class TestSprintDetailPage:
    def test_returns_200(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        resp = client.get("/projects/demo/sprints/sprint-1")
        assert resp.status_code == 200

    def test_shows_sprint_name_and_goal(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "My Sprint", "Build great things",
                     status="active")
        resp = client.get("/projects/demo/sprints/sprint-1")
        assert "My Sprint" in resp.text
        assert "Build great things" in resp.text

    def test_shows_stat_cards(self, client, tmp_project):
        write_story(tmp_project, "S1", "done", "Done Story")
        write_story(tmp_project, "S2", "in_progress", "WIP Story")
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     status="active", stories=["S1", "S2"])
        resp = client.get("/projects/demo/sprints/sprint-1")
        assert "stat-card" in resp.text or "stat-label" in resp.text

    def test_shows_stories_in_board_view(self, client, tmp_project):
        write_story(tmp_project, "S1", "done", "Done One")
        write_story(tmp_project, "S2", "todo", "Todo One")
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     status="active", stories=["S1", "S2"])
        resp = client.get("/projects/demo/sprints/sprint-1")
        assert "board-column" in resp.text
        assert "Done One" in resp.text
        assert "Todo One" in resp.text

    def test_stories_have_modal_link(self, client, tmp_project):
        write_story(tmp_project, "S1", "todo", "Clickable Story")
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     status="active", stories=["S1"])
        resp = client.get("/projects/demo/sprints/sprint-1")
        assert "/partials/demo/story/S1" in resp.text

    def test_active_sprint_has_close_button(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        resp = client.get("/projects/demo/sprints/sprint-1")
        assert "Close Sprint" in resp.text

    def test_closed_sprint_no_close_button(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="closed")
        resp = client.get("/projects/demo/sprints/sprint-1")
        assert "Close Sprint" not in resp.text

    def test_closed_sprint_shows_completed_banner(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal",
                     status="closed", end_date="2026-05-06")
        resp = client.get("/projects/demo/sprints/sprint-1")
        assert "completed" in resp.text.lower() or "Completed" in resp.text

    def test_has_board_list_toggle(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        resp = client.get("/projects/demo/sprints/sprint-1")
        assert "view-toggle" in resp.text

    def test_breadcrumb_links_to_sprints(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        resp = client.get("/projects/demo/sprints/sprint-1")
        assert "/projects/demo/sprints" in resp.text

    def test_404_unknown_sprint(self, client, tmp_project):
        resp = client.get("/projects/demo/sprints/nope")
        assert resp.status_code == 404

    def test_404_unknown_project(self, client):
        resp = client.get("/projects/nope/sprints/sprint-1")
        assert resp.status_code == 404


class TestCloseSprintAPI:
    def test_close_sprint(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="active")
        resp = client.post("/api/sprints/demo/sprint-1/close")
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    def test_close_sprint_404_unknown(self, client, tmp_project):
        resp = client.post("/api/sprints/demo/nope/close")
        assert resp.status_code == 404

    def test_close_already_closed_returns_400(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", status="closed")
        resp = client.post("/api/sprints/demo/sprint-1/close")
        assert resp.status_code == 400
```

### Step 2: Run tests to verify they fail

Run: `python3 -m pytest scripts/dashboard/tests/test_sprint_routes.py::TestSprintDetailPage -v`
Expected: FAIL

### Step 3: Create sprint detail template

Create `scripts/dashboard/templates/sprint_detail.html`. This is the key template — it must include:

- Breadcrumb back to `/projects/{name}/sprints`
- Header card with status pill, phase tag, goal, dates
- Stat cards row (reusing `stat-card` CSS from overview)
- Board/List view toggle
- Board view: 5-column kanban grid with story cards that `hx-get` the story modal
- List view: stories grouped by status with clickable rows
- Close Sprint button (active only) / completed banner (closed)

Reference the sprint detail section in `docs/plans/sprint3-preview.html` for exact HTML structure. The kanban cards must use `hx-get="/partials/{{ project.name }}/story/{{ s.story_id }}"` and `hx-target="#modal-container"` to open the existing story modal.

### Step 4: Add routes to server.py

```python
@app.get("/projects/{name}/sprints/{sprint_id}", response_class=HTMLResponse)
def sprint_detail(request: Request, name: str, sprint_id: str):
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    path = Path(project["path"])
    sprint = parsers.get_sprint(path, sprint_id)
    if not sprint:
        raise HTTPException(404, f"Sprint '{sprint_id}' not found")
    # Group resolved stories by status for board view
    from scripts.v2_2.board import COLUMNS
    board = {c: [] for c in COLUMNS}
    for story in sprint["resolved_stories"]:
        status = story.get("status", "backlog")
        if status in board:
            board[status].append(story)
    # Count stats
    stories = sprint["resolved_stories"]
    stats = {
        "total": len(stories),
        "done": sum(1 for s in stories if s["status"] == "done"),
        "in_progress": sum(1 for s in stories if s["status"] == "in_progress"),
        "todo": sum(1 for s in stories if s["status"] in ("todo", "backlog")),
    }
    return templates.TemplateResponse(request, "sprint_detail.html", context={
        "project": project,
        "sprint": sprint,
        "board": board,
        "stats": stats,
        "projects": parsers.load_projects(),
        "current_page": "sprints",
        "inbox_count": parsers.get_inbox_data(path)["total"],
    })


@app.post("/api/sprints/{name}/{sprint_id}/close")
def api_close_sprint(name: str, sprint_id: str):
    path = _get_project_path(name)
    result = crud.close_sprint(path, sprint_id)
    if result is None:
        sprint_file = path / "_sprints" / f"{sprint_id}.yaml"
        if not sprint_file.exists():
            raise HTTPException(404, f"Sprint '{sprint_id}' not found")
        raise HTTPException(400, "Sprint is already closed")
    return result
```

### Step 5: Add sprint detail CSS

Add `.sprint-detail-header`, `.completed-banner`, `.view-toggle`, `.detail-toolbar` styles. Reference `docs/plans/sprint3-preview.html`.

### Step 6: Run tests

Run: `python3 -m pytest scripts/dashboard/tests/test_sprint_routes.py -v`
Expected: All PASS

### Step 7: Run full suite

Run: `python3 -m pytest scripts/dashboard/tests/ -v`
Expected: All PASS

### Step 8: Commit

```bash
git add scripts/dashboard/server.py scripts/dashboard/templates/ scripts/dashboard/static/style.css scripts/dashboard/tests/test_sprint_routes.py
git commit -m "feat(sprint3): add sprint detail page with kanban/list toggle"
```

---

## Task 5: Roadmap ↔ Sprint Links (STU-P2S3.4)

**Files:**
- Create: `scripts/dashboard/tests/test_roadmap_sprint_link.py`
- Modify: `scripts/dashboard/parsers.py`
- Modify: `scripts/dashboard/templates/partials/roadmap_content.html`
- Modify: `scripts/dashboard/server.py` (sprints page filter)

### Step 1: Write failing tests

Create `scripts/dashboard/tests/test_roadmap_sprint_link.py`:

```python
"""TDD tests for roadmap ↔ sprint links — STU-P2S3.4."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import (
    write_sprint, write_story, write_roadmap,
)


class TestRoadmapSprintAggregation:
    def test_phase_shows_sprint_count(self, tmp_project):
        from scripts.dashboard.parsers import get_roadmap_data
        write_roadmap(tmp_project, phases=[
            {"num": "2", "name": "Dashboard", "timeframe": "weeks 1-3",
             "goal": "Build dashboard"},
        ])
        write_sprint(tmp_project, "sprint-1", "S1", "G1", phase="Phase 2")
        write_sprint(tmp_project, "sprint-2", "S2", "G2", phase="Phase 2")
        data = get_roadmap_data(tmp_project)
        phase = data["phases"][0]
        assert phase["sprint_count"] == 2

    def test_phase_shows_avg_completion(self, tmp_project):
        from scripts.dashboard.parsers import get_roadmap_data
        write_roadmap(tmp_project, phases=[
            {"num": "2", "name": "Dashboard", "timeframe": "weeks 1-3",
             "goal": "Build it"},
        ])
        write_story(tmp_project, "S1", "done", "Done")
        write_story(tmp_project, "S2", "todo", "Todo")
        write_sprint(tmp_project, "sprint-1", "S1", "G1",
                     phase="Phase 2", stories=["S1"])  # 100%
        write_sprint(tmp_project, "sprint-2", "S2", "G2",
                     phase="Phase 2", stories=["S2"])  # 0%
        data = get_roadmap_data(tmp_project)
        phase = data["phases"][0]
        assert phase["sprint_pct"] == 50

    def test_phase_no_sprints(self, tmp_project):
        from scripts.dashboard.parsers import get_roadmap_data
        write_roadmap(tmp_project, phases=[
            {"num": "3", "name": "Agent", "timeframe": "TBD", "goal": "AI"},
        ])
        data = get_roadmap_data(tmp_project)
        phase = data["phases"][0]
        assert phase["sprint_count"] == 0
        assert phase["sprint_pct"] == 0


class TestSprintsFilterByPhase:
    def test_filter_returns_only_matching_phase(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "S1", "G1", phase="Phase 2")
        write_sprint(tmp_project, "sprint-2", "S2", "G2", phase="Phase 3")
        resp = client.get("/projects/demo/sprints?phase=Phase+2")
        assert resp.status_code == 200
        assert "S1" in resp.text
        assert "S2" not in resp.text

    def test_no_filter_shows_all(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "S1", "G1", phase="Phase 2")
        write_sprint(tmp_project, "sprint-2", "S2", "G2", phase="Phase 3")
        resp = client.get("/projects/demo/sprints")
        assert "S1" in resp.text
        assert "S2" in resp.text


class TestSprintCardShowsPhase:
    def test_phase_tag_visible(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", phase="Phase 2")
        resp = client.get("/projects/demo/sprints")
        assert "Phase 2" in resp.text
```

### Step 2: Run tests to verify they fail

Run: `python3 -m pytest scripts/dashboard/tests/test_roadmap_sprint_link.py -v`
Expected: FAIL — `sprint_count` not in phase data

### Step 3: Enrich `get_roadmap_data` with sprint aggregation

Modify `scripts/dashboard/parsers.py` — in `get_roadmap_data()`, after computing phases, enrich each phase with sprint data:

```python
def get_roadmap_data(path: Path) -> dict[str, Any]:
    """Parse _roadmap.md into structured roadmap data, enriched with sprint info."""
    roadmap_file = path / "_roadmap.md"
    if not roadmap_file.exists():
        return {"mission": "", "phases": [], "raw": ""}

    text = roadmap_file.read_text()
    mission = _extract_roadmap_mission(text)
    phases = _extract_roadmap_phases(text)

    # Enrich phases with sprint aggregation
    sprints_data = get_sprints_data(path)
    for phase in phases:
        phase_name = f"Phase {phase['num']}"
        phase_sprints = [s for s in sprints_data if s.get("phase") == phase_name]
        phase["sprint_count"] = len(phase_sprints)
        if phase_sprints:
            phase["sprint_pct"] = round(
                sum(s["pct"] for s in phase_sprints) / len(phase_sprints)
            )
        else:
            phase["sprint_pct"] = 0

    return {
        "mission": mission,
        "phases": phases,
        "raw": text if not mission and not phases else "",
    }
```

### Step 4: Add phase filter to sprints route

Modify `sprints_page` in `server.py` to accept `?phase=` query param:

```python
@app.get("/projects/{name}/sprints", response_class=HTMLResponse)
def sprints_page(request: Request, name: str, phase: str | None = None):
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    path = Path(project["path"])
    sprints = parsers.get_sprints_data(path)
    if phase:
        sprints = [s for s in sprints if s.get("phase") == phase]
    return templates.TemplateResponse(request, "sprints.html", context={
        "project": project,
        "sprints": sprints,
        "projects": parsers.load_projects(),
        "current_page": "sprints",
        "inbox_count": parsers.get_inbox_data(path)["total"],
        "phase_filter": phase or "",
    })
```

### Step 5: Update roadmap template

Add sprint info line to each phase card in `scripts/dashboard/templates/partials/roadmap_content.html`. After existing phase content, add:

```html
<div class="phase-sprints-line">
  {% if phase.sprint_count > 0 %}
  <span style="font-weight: 600;">{{ phase.sprint_count }} sprint{{ 's' if phase.sprint_count != 1 else '' }}</span>
  <span>&bull;</span>
  <span>{{ phase.sprint_pct }}% complete</span>
  <div class="progress-mini"><div class="progress-mini-fill" style="width: {{ phase.sprint_pct }}%"></div></div>
  <a href="/projects/{{ project.name }}/sprints?phase=Phase+{{ phase.num }}" style="color:var(--accent); font-weight: 600; margin-left: 4px;">View sprints &rarr;</a>
  {% else %}
  <span>No sprints yet</span>
  {% endif %}
</div>
```

### Step 6: Add CSS for phase-sprints-line

Add `.phase-sprints-line`, `.progress-mini`, `.progress-mini-fill` to `style.css`. Reference `docs/plans/sprint3-preview.html`.

### Step 7: Run tests

Run: `python3 -m pytest scripts/dashboard/tests/test_roadmap_sprint_link.py -v`
Expected: All PASS

### Step 8: Run full suite

Run: `python3 -m pytest scripts/dashboard/tests/ -v`
Expected: All PASS

### Step 9: Commit

```bash
git add scripts/dashboard/parsers.py scripts/dashboard/server.py scripts/dashboard/templates/ scripts/dashboard/static/style.css scripts/dashboard/tests/test_roadmap_sprint_link.py
git commit -m "feat(sprint3): add roadmap ↔ sprint bidirectional links"
```

---

## Task 6: Sprint CRUD API + Create Form UI (STU-P2S3.5)

**Files:**
- Create: `scripts/dashboard/tests/test_sprint_crud_api.py`
- Create: `scripts/dashboard/templates/partials/create_sprint_form.html`
- Modify: `scripts/dashboard/server.py`

### Step 1: Write failing API tests

Create `scripts/dashboard/tests/test_sprint_crud_api.py`:

```python
"""TDD tests for sprint CRUD API — STU-P2S3.5."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import write_sprint, write_story


class TestCreateSprintAPI:
    def test_create_sprint_json(self, client, tmp_project):
        resp = client.post("/api/sprints/demo", json={
            "name": "New Sprint",
            "goal": "Build things",
            "start_date": "2026-05-10",
            "end_date": "2026-05-12",
            "phase": "Phase 2",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Sprint"
        assert data["status"] == "planned"
        assert data["id"].startswith("sprint-")

    def test_create_sprint_form(self, client, tmp_project):
        resp = client.post("/api/sprints/demo/form", data={
            "name": "Form Sprint",
            "goal": "Test",
            "start_date": "2026-05-10",
            "end_date": "2026-05-12",
            "phase": "Phase 2",
        })
        assert resp.status_code == 201

    def test_create_sprint_404_unknown_project(self, client):
        resp = client.post("/api/sprints/nope", json={
            "name": "X", "goal": "X",
            "start_date": "2026-05-10", "end_date": "2026-05-12",
            "phase": "Phase 1",
        })
        assert resp.status_code == 404

    def test_create_sprint_422_missing_name(self, client, tmp_project):
        resp = client.post("/api/sprints/demo", json={
            "goal": "No name",
            "start_date": "2026-05-10",
            "end_date": "2026-05-12",
            "phase": "Phase 1",
        })
        assert resp.status_code == 422


class TestAddStoryToSprintAPI:
    def test_add_story(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal")
        write_story(tmp_project, "S1", "todo", "Story One")
        resp = client.post("/api/sprints/demo/sprint-1/stories",
                           json={"story_id": "S1"})
        assert resp.status_code == 200
        data = yaml.safe_load(
            (tmp_project / "_sprints" / "sprint-1.yaml").read_text())
        assert "S1" in data["stories"]

    def test_add_story_404_unknown_sprint(self, client, tmp_project):
        write_story(tmp_project, "S1", "todo", "Story")
        resp = client.post("/api/sprints/demo/nope/stories",
                           json={"story_id": "S1"})
        assert resp.status_code == 404


class TestRemoveStoryFromSprintAPI:
    def test_remove_story(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", stories=["S1"])
        write_story(tmp_project, "S1", "todo", "Story One")
        resp = client.delete("/api/sprints/demo/sprint-1/stories/S1")
        assert resp.status_code == 200

    def test_remove_story_404_unknown_sprint(self, client, tmp_project):
        resp = client.delete("/api/sprints/demo/nope/stories/S1")
        assert resp.status_code == 404


class TestCreateSprintFormPartial:
    def test_returns_form_html(self, client, tmp_project):
        resp = client.get("/partials/demo/create-sprint")
        assert resp.status_code == 200
        assert "<form" in resp.text
        assert 'name="name"' in resp.text
        assert 'name="goal"' in resp.text
        assert 'name="start_date"' in resp.text
        assert 'name="end_date"' in resp.text
        assert 'name="phase"' in resp.text

    def test_phase_dropdown_lists_roadmap_phases(self, client, tmp_project):
        from scripts.dashboard.tests.conftest import write_roadmap
        write_roadmap(tmp_project, phases=[
            {"num": "1", "name": "Foundation", "timeframe": "w1-2", "goal": "Base"},
            {"num": "2", "name": "Dashboard", "timeframe": "w3-4", "goal": "UI"},
        ])
        resp = client.get("/partials/demo/create-sprint")
        assert "Phase 1" in resp.text
        assert "Phase 2" in resp.text
```

### Step 2: Run tests to verify they fail

Run: `python3 -m pytest scripts/dashboard/tests/test_sprint_crud_api.py -v`
Expected: FAIL

### Step 3: Add API routes to server.py

```python
class CreateSprintRequest(BaseModel):
    name: str
    goal: str
    start_date: str
    end_date: str
    phase: str
    status: str = "planned"


class AddStoryToSprintRequest(BaseModel):
    story_id: str


@app.post("/api/sprints/{name}", status_code=201)
def api_create_sprint(name: str, body: CreateSprintRequest):
    path = _get_project_path(name)
    return crud.create_sprint(path, name=body.name, goal=body.goal,
                              start_date=body.start_date, end_date=body.end_date,
                              phase=body.phase, status=body.status)


@app.post("/api/sprints/{name}/form", status_code=201, response_class=HTMLResponse)
def api_create_sprint_form(
    name: str,
    form_name: str = Form(..., alias="name"),
    goal: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    phase: str = Form(...),
):
    path = _get_project_path(name)
    crud.create_sprint(path, name=form_name, goal=goal,
                       start_date=start_date, end_date=end_date, phase=phase)
    return HTMLResponse("")


@app.post("/api/sprints/{name}/{sprint_id}/stories")
def api_add_story_to_sprint(name: str, sprint_id: str, body: AddStoryToSprintRequest):
    path = _get_project_path(name)
    result = crud.add_story_to_sprint(path, sprint_id, body.story_id)
    if result is None:
        raise HTTPException(404, f"Sprint '{sprint_id}' not found")
    return result


@app.delete("/api/sprints/{name}/{sprint_id}/stories/{story_id}")
def api_remove_story_from_sprint(name: str, sprint_id: str, story_id: str):
    path = _get_project_path(name)
    result = crud.remove_story_from_sprint(path, sprint_id, story_id)
    if result is None:
        raise HTTPException(404, f"Sprint '{sprint_id}' not found")
    return result


@app.get("/partials/{name}/create-sprint", response_class=HTMLResponse)
def partial_create_sprint_form(request: Request, name: str):
    path = _get_project_path(name)
    roadmap = parsers.get_roadmap_data(path)
    phases = [f"Phase {p['num']}" for p in roadmap.get("phases", [])]
    return templates.TemplateResponse(request, "partials/create_sprint_form.html", context={
        "project_name": name,
        "phases": phases,
    })
```

### Step 4: Create the form template

Create `scripts/dashboard/templates/partials/create_sprint_form.html`:

```html
{% from "partials/modal_shell.html" import modal %}
{% call modal('NEW', 'New Sprint') %}
<form hx-post="/api/sprints/{{ project_name }}/form"
      hx-target="#modal-container"
      hx-swap="innerHTML"
      hx-on::after-request="if(event.detail.successful){document.querySelector('.modal-overlay').remove(); htmx.trigger(document.body, 'sprint-changed')}">
  <div class="form-group">
    <label>Name</label>
    <input type="text" name="name" placeholder="e.g. Phase 2 — Chat UI" required>
  </div>
  <div class="form-group">
    <label>Goal</label>
    <input type="text" name="goal" placeholder="What does this sprint deliver?" required>
  </div>
  <div class="form-row">
    <div class="form-group">
      <label>Start Date</label>
      <input type="date" name="start_date" required>
    </div>
    <div class="form-group">
      <label>End Date</label>
      <input type="date" name="end_date" required>
    </div>
  </div>
  <div class="form-group">
    <label>Phase</label>
    <select name="phase">
      {% for p in phases %}
      <option value="{{ p }}">{{ p }}</option>
      {% endfor %}
      {% if not phases %}
      <option value="Phase 1">Phase 1</option>
      {% endif %}
    </select>
  </div>
  <div class="form-actions">
    <button type="button" class="btn" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
    <button type="submit" class="btn btn-primary">Create Sprint</button>
  </div>
</form>
{% endcall %}
```

### Step 5: Run tests

Run: `python3 -m pytest scripts/dashboard/tests/test_sprint_crud_api.py -v`
Expected: All PASS

### Step 6: Run full suite

Run: `python3 -m pytest scripts/dashboard/tests/ -v`
Expected: All PASS

### Step 7: Commit

```bash
git add scripts/dashboard/server.py scripts/dashboard/templates/partials/create_sprint_form.html scripts/dashboard/tests/test_sprint_crud_api.py
git commit -m "feat(sprint3): add sprint CRUD API + create form modal"
```

---

## Task 7: Manual Verification + Cleanup

**Files:**
- Modify: `_backlog/STU-P2S3-*.md` (update status)

### Step 1: Start the dashboard

Run: `python3 -m scripts.dashboard`

### Step 2: Verify in browser at localhost:5111

- [ ] Sidebar shows "Sprints" link
- [ ] Click Sprints → list page renders
- [ ] Click "+ New Sprint" → modal opens, form submits, sprint appears
- [ ] Click sprint card → detail page with kanban + stat cards
- [ ] Click Board/List toggle → switches views
- [ ] Click story card → modal opens with full detail
- [ ] Active sprint: "Close Sprint" button works
- [ ] Closed sprint: shows completed banner
- [ ] Roadmap page: phases show sprint count + completion %
- [ ] Roadmap: "View sprints →" link navigates to filtered sprints

### Step 3: Run full test suite one final time

Run: `python3 -m pytest scripts/dashboard/tests/ -v`
Expected: All tests PASS (127 existing + ~60 new)

### Step 4: Update backlog ticket statuses to done

Update `_backlog/STU-P2S3-*.md` files: change `status: todo` → `status: done` in frontmatter.

### Step 5: Commit

```bash
git add _backlog/STU-P2S3-*.md
git commit -m "feat(sprint3): mark all Sprint 3 tickets done"
```

---

## Summary

| Task | Ticket | What | Tests |
|------|--------|------|-------|
| 1 | STU-P2S3.1a | Sprint parsers (load, get, data) | ~12 |
| 2 | STU-P2S3.1b | Sprint CRUD (create, close, add/remove) | ~12 |
| 3 | STU-P2S3.2 | Sprints list page + sidebar | ~8 |
| 4 | STU-P2S3.3 | Sprint detail page (kanban/list + close) | ~14 |
| 5 | STU-P2S3.4 | Roadmap ↔ Sprint links | ~6 |
| 6 | STU-P2S3.5 | Sprint CRUD API + create form | ~10 |
| 7 | — | Manual verification + cleanup | — |

**Total: ~62 new tests, 7 commits**
