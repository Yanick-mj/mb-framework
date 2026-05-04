# Dashboard Sprint 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver a usable browser dashboard (localhost:5111) where a PM sees project health, kanban board, and story details — auto-refreshing every 5s.

**Architecture:** Thin `scripts/dashboard/` FastAPI layer wrapping existing v2.1/v2.2 parsers. `project_context()` monkey-patches `_paths.project_root()` for multi-project support. HTMX handles polling — no custom JS.

**Tech Stack:** Python 3.13, FastAPI, Jinja2, HTMX (CDN), uvicorn, pytest + httpx (test)

**TDD:** Tests for parsers (unit) and routes (integration via TestClient) written BEFORE implementation. Templates tested manually in browser.

**Repo:** `/Users/yanickmingala/code/Yanick-mj/mb-framework` on branch `feat/dashboard-mvp`

**Existing code to reuse:**
- `scripts/v2_2/_paths.py` — `project_root()` (monkey-patch target)
- `scripts/v2_2/board.py` — `_parse_frontmatter()`, `_group_by_status()`, `COLUMNS`
- `scripts/v2_2/inbox.py` — `_scan_stories()`, `_scan_approvals()`
- `scripts/v2_1/runs.py` — `load_recent()`
- `scripts/v2_1/projects.py` — `load()`
- `scripts/v2_2/tests/conftest.py` — `tmp_project`, `tmp_home` fixture patterns

**CSS source:** `/Users/yanickmingala/mb-bench/prototype-dashboard.html` (extract `<style>` block)

---

## Task 1: Package scaffold + dependency check

**Files:**
- Create: `scripts/dashboard/__init__.py`
- Create: `scripts/dashboard/__main__.py`

**Step 1: Create empty package**

```python
# scripts/dashboard/__init__.py
```

**Step 2: Create `__main__.py` with dep check + uvicorn launch**

```python
# scripts/dashboard/__main__.py
"""Launch the mb-dashboard server.

Usage: python3 -m scripts.dashboard [--port PORT]
"""
import importlib.util
import sys

REQUIRED = ["fastapi", "uvicorn", "jinja2"]


def _check_deps() -> list[str]:
    return [pkg for pkg in REQUIRED if importlib.util.find_spec(pkg) is None]


def main() -> None:
    missing = _check_deps()
    if missing:
        print(
            f"Missing dependencies: {', '.join(missing)}\n"
            f"\nFix: pip install {' '.join(missing)}\n",
            file=sys.stderr,
        )
        sys.exit(2)

    import uvicorn

    port = 5111
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])

    print(f"mb-dashboard → http://localhost:{port}")
    uvicorn.run("scripts.dashboard.server:app", host="127.0.0.1", port=port, reload=True)


if __name__ == "__main__":
    main()
```

**Step 3: Verify it runs (deps missing = helpful error, deps present = starts)**

Run: `cd /Users/yanickmingala/code/Yanick-mj/mb-framework && python3 -m scripts.dashboard`
Expected: Either starts on :5111 or prints "Missing dependencies" with install command.

**Step 4: Commit**

```bash
git add scripts/dashboard/__init__.py scripts/dashboard/__main__.py
git commit -m "feat(dashboard): D1.1 — package scaffold + dep check"
```

---

## Task 2: Test fixtures (`conftest.py`)

**Files:**
- Create: `scripts/dashboard/tests/__init__.py`
- Create: `scripts/dashboard/tests/conftest.py`

**Step 1: Create test package and fixtures**

```python
# scripts/dashboard/tests/__init__.py
```

```python
# scripts/dashboard/tests/conftest.py
"""Shared fixtures for dashboard tests."""
import json
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


@pytest.fixture
def tmp_home(monkeypatch):
    """Redirect ~ to tmpdir so tests never touch real $HOME."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("HOME", tmpdir)
        yield Path(tmpdir)


@pytest.fixture
def tmp_project(tmp_path, monkeypatch):
    """Minimal mb project layout, cd'd into it."""
    project = tmp_path / "demo-project"
    project.mkdir()
    (project / "mb-stage.yaml").write_text("stage: mvp\nsince: 2026-04-19\n")
    (project / "memory").mkdir()
    (project / "_bmad-output").mkdir()
    monkeypatch.chdir(project)
    return project


def write_story(root: Path, story_id: str, status: str,
                title: str = "", priority: str = "medium",
                labels: list[str] | None = None) -> None:
    """Helper: write a story .md with frontmatter to stories dir."""
    d = root / "_bmad-output" / "implementation-artifacts" / "stories"
    d.mkdir(parents=True, exist_ok=True)
    fm = {
        "story_id": story_id,
        "title": title or story_id,
        "status": status,
        "priority": priority,
    }
    if labels:
        fm["labels"] = labels
    content = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---\n\n## Why\nBecause.\n\n## Scope\nDo the thing.\n\n## Acceptance criteria\n- [ ] First item\n- [x] Done item\n"
    (d / f"{story_id}.md").write_text(content)


def write_backlog_story(root: Path, story_id: str, status: str,
                        title: str = "", priority: str = "medium") -> None:
    """Helper: write a story to _backlog/ dir."""
    d = root / "_backlog"
    d.mkdir(parents=True, exist_ok=True)
    fm = {
        "story_id": story_id,
        "title": title or story_id,
        "status": status,
        "priority": priority,
    }
    content = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---\n\n## Why\nReason.\n"
    (d / f"{story_id}.md").write_text(content)


def write_runs(root: Path, count: int = 3) -> None:
    """Helper: write N run entries to runs.jsonl."""
    log = root / "memory" / "runs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        entry = {
            "run_id": f"run{i:03d}",
            "ts": f"2026-05-04T10:{i:02d}:00.000000+00:00",
            "agent": f"agent-{i}",
            "story": f"STU-{i}",
            "action": f"action_{i}",
            "tokens_in": 100,
            "tokens_out": 50,
            "summary": f"Did thing {i}",
        }
        with log.open("a") as f:
            f.write(json.dumps(entry) + "\n")


def register_projects(tmp_home: Path, projects: list[dict]) -> None:
    """Helper: write projects to ~/.mb/projects.yaml."""
    mb_dir = tmp_home / ".mb"
    mb_dir.mkdir(parents=True, exist_ok=True)
    (mb_dir / "projects.yaml").write_text(
        yaml.safe_dump({"version": 1, "projects": projects}, sort_keys=False)
    )
```

**Step 2: Verify fixtures load**

Run: `cd /Users/yanickmingala/code/Yanick-mj/mb-framework && python3 -m pytest scripts/dashboard/tests/ --collect-only`
Expected: "no tests ran" (no test files yet), but no import errors.

**Step 3: Commit**

```bash
git add scripts/dashboard/tests/
git commit -m "test(dashboard): D1.2 — test fixtures + helpers"
```

---

## Task 3: TDD `parsers.py` — `project_context` + `load_projects`

**Files:**
- Create: `scripts/dashboard/tests/test_parsers.py`
- Create: `scripts/dashboard/parsers.py`

**Step 1: Write failing tests**

```python
# scripts/dashboard/tests/test_parsers.py
"""Unit tests for dashboard parsers — TDD, tests first."""
from pathlib import Path

import pytest

from scripts.dashboard import parsers
from scripts.dashboard.tests.conftest import register_projects


class TestProjectContext:
    def test_overrides_project_root(self, tmp_project):
        target = Path("/tmp/fake-project")
        with parsers.project_context(target):
            from scripts.v2_2 import _paths
            assert _paths.project_root() == target

    def test_restores_after_exit(self, tmp_project):
        from scripts.v2_2 import _paths
        original = _paths.project_root()
        with parsers.project_context(Path("/tmp/other")):
            pass
        assert _paths.project_root() == original

    def test_restores_on_exception(self, tmp_project):
        from scripts.v2_2 import _paths
        original = _paths.project_root()
        with pytest.raises(ValueError):
            with parsers.project_context(Path("/tmp/other")):
                raise ValueError("boom")
        assert _paths.project_root() == original


class TestLoadProjects:
    def test_returns_empty_when_no_registry(self, tmp_home):
        assert parsers.load_projects() == []

    def test_returns_project_list(self, tmp_home):
        register_projects(tmp_home, [
            {"name": "demo", "path": "/tmp/demo", "stage": "mvp"},
        ])
        result = parsers.load_projects()
        assert len(result) == 1
        assert result[0]["name"] == "demo"
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/yanickmingala/code/Yanick-mj/mb-framework && python3 -m pytest scripts/dashboard/tests/test_parsers.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.dashboard.parsers'`

**Step 3: Implement minimal code**

```python
# scripts/dashboard/parsers.py
"""Data layer for the dashboard — wraps existing v2.1/v2.2 parsers.

All functions return plain dicts/lists. No FastAPI dependency.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

from scripts.v2_2 import _paths


@contextmanager
def project_context(path: Path):
    """Temporarily override _paths.project_root() to point at `path`."""
    original = _paths.project_root

    _paths.project_root = lambda: path
    try:
        yield
    finally:
        _paths.project_root = original


def load_projects() -> list[dict[str, Any]]:
    """Load registered projects from ~/.mb/projects.yaml."""
    from scripts.v2_1 import projects
    return projects.load()
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/yanickmingala/code/Yanick-mj/mb-framework && python3 -m pytest scripts/dashboard/tests/test_parsers.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add scripts/dashboard/parsers.py scripts/dashboard/tests/test_parsers.py
git commit -m "feat(dashboard): D1.3 — project_context + load_projects (TDD)"
```

---

## Task 4: TDD `parsers.py` — `get_stage_data` + `get_story_stats`

**Files:**
- Modify: `scripts/dashboard/tests/test_parsers.py`
- Modify: `scripts/dashboard/parsers.py`

**Step 1: Write failing tests**

Append to `test_parsers.py`:

```python
class TestGetStageData:
    def test_reads_stage_yaml(self, tmp_project):
        result = parsers.get_stage_data(tmp_project)
        assert result["stage"] == "mvp"
        assert result["since"] == "2026-04-19"

    def test_missing_file_returns_unknown(self, tmp_path):
        result = parsers.get_stage_data(tmp_path)
        assert result["stage"] == "unknown"
        assert result["since"] is None


class TestGetStoryStats:
    def test_counts_by_status(self, tmp_project):
        from scripts.dashboard.tests.conftest import write_story
        write_story(tmp_project, "S1", "todo")
        write_story(tmp_project, "S2", "todo")
        write_story(tmp_project, "S3", "in_progress")
        write_story(tmp_project, "S4", "done")
        result = parsers.get_story_stats(tmp_project)
        assert result["total"] == 4
        assert result["todo"] == 2
        assert result["in_progress"] == 1
        assert result["done"] == 1
        assert result["backlog"] == 0

    def test_empty_project(self, tmp_project):
        result = parsers.get_story_stats(tmp_project)
        assert result["total"] == 0
```

**Step 2: Run — expect FAIL**

Run: `python3 -m pytest scripts/dashboard/tests/test_parsers.py::TestGetStageData -v`
Expected: FAIL — `AttributeError: module 'scripts.dashboard.parsers' has no attribute 'get_stage_data'`

**Step 3: Implement**

Add to `parsers.py`:

```python
import yaml


def get_stage_data(path: Path) -> dict[str, Any]:
    """Read mb-stage.yaml from project root."""
    stage_file = path / "mb-stage.yaml"
    if not stage_file.exists():
        return {"stage": "unknown", "since": None}
    try:
        data = yaml.safe_load(stage_file.read_text()) or {}
    except yaml.YAMLError:
        return {"stage": "unknown", "since": None}
    return {
        "stage": data.get("stage", "unknown"),
        "since": str(data["since"]) if "since" in data else None,
    }


def get_story_stats(path: Path) -> dict[str, int]:
    """Count stories by status using board._group_by_status()."""
    from scripts.v2_2 import board
    with project_context(path):
        groups = board._group_by_status()
    result = {col: len(stories) for col, stories in groups.items()}
    result["total"] = sum(result.values())
    return result
```

**Step 4: Run — expect PASS**

Run: `python3 -m pytest scripts/dashboard/tests/test_parsers.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add scripts/dashboard/parsers.py scripts/dashboard/tests/test_parsers.py
git commit -m "feat(dashboard): D1.4 — get_stage_data + get_story_stats (TDD)"
```

---

## Task 5: TDD `parsers.py` — `get_board_data`

**Files:**
- Modify: `scripts/dashboard/tests/test_parsers.py`
- Modify: `scripts/dashboard/parsers.py`

**Step 1: Write failing tests**

```python
class TestGetBoardData:
    def test_returns_enriched_stories_by_column(self, tmp_project):
        from scripts.dashboard.tests.conftest import write_story
        write_story(tmp_project, "S1", "todo", "My Title", "high", ["frontend"])
        result = parsers.get_board_data(tmp_project)
        assert "todo" in result
        assert len(result["todo"]) == 1
        card = result["todo"][0]
        assert card["story_id"] == "S1"
        assert card["title"] == "My Title"
        assert card["priority"] == "high"
        assert card["labels"] == ["frontend"]

    def test_includes_backlog_dir_stories(self, tmp_project):
        from scripts.dashboard.tests.conftest import write_backlog_story
        write_backlog_story(tmp_project, "B1", "backlog", "Backlog Item")
        result = parsers.get_board_data(tmp_project)
        assert len(result["backlog"]) == 1
        assert result["backlog"][0]["story_id"] == "B1"

    def test_empty_project_returns_empty_columns(self, tmp_project):
        result = parsers.get_board_data(tmp_project)
        for col in ["backlog", "todo", "in_progress", "in_review", "done"]:
            assert result[col] == []

    def test_stories_without_labels_get_empty_list(self, tmp_project):
        from scripts.dashboard.tests.conftest import write_story
        write_story(tmp_project, "S1", "todo", "No Labels")
        card = parsers.get_board_data(tmp_project)["todo"][0]
        assert card["labels"] == []
```

**Step 2: Run — expect FAIL**

Run: `python3 -m pytest scripts/dashboard/tests/test_parsers.py::TestGetBoardData -v`

**Step 3: Implement**

Add to `parsers.py`:

```python
import re

_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)


def _parse_frontmatter(text: str) -> dict:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _scan_all_stories(path: Path) -> list[dict]:
    """Scan both _bmad-output stories and _backlog for story files."""
    from scripts.v2_2 import board
    stories = []
    # Stories dir
    stories_dir = path / "_bmad-output" / "implementation-artifacts" / "stories"
    if stories_dir.exists():
        for f in sorted(stories_dir.glob("*.md")):
            fm = _parse_frontmatter(f.read_text())
            if fm:
                fm.setdefault("labels", [])
                fm["_path"] = str(f)
                stories.append(fm)
    # Backlog dir
    backlog_dir = path / "_backlog"
    if backlog_dir.exists():
        for f in sorted(backlog_dir.glob("*.md")):
            fm = _parse_frontmatter(f.read_text())
            if fm and fm.get("story_id"):
                fm.setdefault("labels", [])
                fm["_path"] = str(f)
                stories.append(fm)
    return stories


def get_board_data(path: Path) -> dict[str, list[dict]]:
    """Group stories into kanban columns with enriched card data."""
    from scripts.v2_2.board import COLUMNS
    groups: dict[str, list[dict]] = {c: [] for c in COLUMNS}
    for story in _scan_all_stories(path):
        status = story.get("status")
        if status in groups:
            groups[status].append({
                "story_id": story.get("story_id", "?"),
                "title": story.get("title", ""),
                "status": status,
                "priority": story.get("priority", "medium"),
                "labels": story.get("labels") or [],
            })
    return groups
```

**Step 4: Run — expect PASS**

Run: `python3 -m pytest scripts/dashboard/tests/test_parsers.py -v`

**Step 5: Commit**

```bash
git add scripts/dashboard/parsers.py scripts/dashboard/tests/test_parsers.py
git commit -m "feat(dashboard): D1.5 — get_board_data with backlog scan (TDD)"
```

---

## Task 6: TDD `parsers.py` — `get_recent_runs` + `get_story_detail` + `get_inbox_data`

**Files:**
- Modify: `scripts/dashboard/tests/test_parsers.py`
- Modify: `scripts/dashboard/parsers.py`

**Step 1: Write failing tests**

```python
class TestGetRecentRuns:
    def test_returns_runs_newest_first(self, tmp_project):
        from scripts.dashboard.tests.conftest import write_runs
        write_runs(tmp_project, count=3)
        result = parsers.get_recent_runs(tmp_project, limit=2)
        assert len(result) == 2
        assert result[0]["run_id"] == "run002"

    def test_empty_project_returns_empty(self, tmp_project):
        result = parsers.get_recent_runs(tmp_project)
        assert result == []


class TestGetStoryDetail:
    def test_returns_full_story(self, tmp_project):
        from scripts.dashboard.tests.conftest import write_story
        write_story(tmp_project, "S1", "todo", "Build Widget", "high")
        result = parsers.get_story_detail(tmp_project, "S1")
        assert result is not None
        assert result["story_id"] == "S1"
        assert result["title"] == "Build Widget"
        assert result["priority"] == "high"
        assert result["status"] == "todo"
        assert "why" in result["sections"]
        assert "scope" in result["sections"]
        assert "acceptance_criteria" in result["sections"]

    def test_acceptance_criteria_parsed(self, tmp_project):
        from scripts.dashboard.tests.conftest import write_story
        write_story(tmp_project, "S1", "todo")
        result = parsers.get_story_detail(tmp_project, "S1")
        ac = result["sections"]["acceptance_criteria"]
        assert len(ac) == 2
        assert ac[0]["done"] is False
        assert ac[1]["done"] is True

    def test_missing_story_returns_none(self, tmp_project):
        result = parsers.get_story_detail(tmp_project, "NOPE")
        assert result is None

    def test_finds_story_in_backlog(self, tmp_project):
        from scripts.dashboard.tests.conftest import write_backlog_story
        write_backlog_story(tmp_project, "B1", "backlog", "Backlog Thing")
        result = parsers.get_story_detail(tmp_project, "B1")
        assert result is not None
        assert result["story_id"] == "B1"


class TestGetInboxData:
    def test_counts_actionable_items(self, tmp_project):
        from scripts.dashboard.tests.conftest import write_story
        write_story(tmp_project, "S1", "in_review")
        write_story(tmp_project, "S2", "blocked")
        write_story(tmp_project, "S3", "done")  # not actionable
        result = parsers.get_inbox_data(tmp_project)
        assert result["total"] == 2
        assert len(result["in_review"]) == 1
        assert len(result["blocked"]) == 1
        assert len(result["approvals"]) == 0

    def test_empty_inbox(self, tmp_project):
        result = parsers.get_inbox_data(tmp_project)
        assert result["total"] == 0
```

**Step 2: Run — expect FAIL**

Run: `python3 -m pytest scripts/dashboard/tests/test_parsers.py -v -k "Runs or StoryDetail or Inbox"`

**Step 3: Implement**

Add to `parsers.py`:

```python
def get_recent_runs(path: Path, limit: int = 5) -> list[dict]:
    """Load recent agent runs from runs.jsonl."""
    from scripts.v2_1 import runs
    with project_context(path):
        return runs.load_recent(limit=limit)


def get_story_detail(path: Path, story_id: str) -> dict[str, Any] | None:
    """Find and parse a single story by its story_id."""
    for story in _scan_all_stories(path):
        if story.get("story_id") == story_id:
            file_path = Path(story["_path"])
            text = file_path.read_text()
            sections = _parse_sections(text)
            return {
                "story_id": story.get("story_id"),
                "title": story.get("title", ""),
                "priority": story.get("priority", "medium"),
                "status": story.get("status", "unknown"),
                "created": str(story.get("created", "")),
                "sections": sections,
            }
    return None


def _parse_sections(text: str) -> dict[str, Any]:
    """Extract Why, Scope, Acceptance criteria from story body."""
    # Strip frontmatter
    body = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)

    sections: dict[str, Any] = {"why": "", "scope": "", "acceptance_criteria": []}

    # Split by ## headers
    parts = re.split(r"^## (.+)$", body, flags=re.MULTILINE)
    # parts = [pre, header1, content1, header2, content2, ...]
    for i in range(1, len(parts) - 1, 2):
        header = parts[i].strip().lower()
        content = parts[i + 1].strip()
        if "why" in header:
            sections["why"] = content
        elif "scope" in header:
            sections["scope"] = content
        elif "acceptance" in header or "criteria" in header:
            sections["acceptance_criteria"] = _parse_checklist(content)

    return sections


def _parse_checklist(text: str) -> list[dict[str, Any]]:
    """Parse markdown checklist items."""
    items = []
    for m in re.finditer(r"- \[([ xX])\] (.+)", text):
        items.append({
            "done": m.group(1).lower() == "x",
            "text": m.group(2).strip(),
        })
    return items


def get_inbox_data(path: Path) -> dict[str, Any]:
    """Get actionable items: in_review + blocked + approvals."""
    from scripts.v2_2 import inbox
    with project_context(path):
        stories = inbox._scan_stories()
        approvals = inbox._scan_approvals()

    in_review = [s for s in stories if s.get("status") == "in_review"]
    blocked = [s for s in stories if s.get("status") == "blocked"]

    return {
        "in_review": in_review,
        "blocked": blocked,
        "approvals": approvals,
        "total": len(in_review) + len(blocked) + len(approvals),
    }
```

**Step 4: Run — expect PASS**

Run: `python3 -m pytest scripts/dashboard/tests/test_parsers.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add scripts/dashboard/parsers.py scripts/dashboard/tests/test_parsers.py
git commit -m "feat(dashboard): D1.6 — get_recent_runs + get_story_detail + get_inbox_data (TDD)"
```

---

## Task 7: TDD `server.py` — app factory + root redirect + static mount

**Files:**
- Create: `scripts/dashboard/server.py`
- Create: `scripts/dashboard/tests/test_routes.py`

**Step 1: Write failing tests**

```python
# scripts/dashboard/tests/test_routes.py
"""Integration tests for dashboard routes via FastAPI TestClient."""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fastapi.testclient import TestClient
from scripts.dashboard.server import app
from scripts.dashboard.tests.conftest import (
    register_projects, write_story, write_runs,
)


class TestRootRedirect:
    def test_redirects_to_first_project_overview(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        client = TestClient(app, follow_redirects=False)
        resp = client.get("/")
        assert resp.status_code == 307
        assert "/projects/demo/overview" in resp.headers["location"]

    def test_no_projects_returns_200_with_message(self, tmp_home):
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        assert "no project" in resp.text.lower()
```

**Step 2: Run — expect FAIL**

Run: `python3 -m pytest scripts/dashboard/tests/test_routes.py -v`

**Step 3: Implement server.py**

```python
# scripts/dashboard/server.py
"""FastAPI application for mb-dashboard."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from scripts.dashboard import parsers

_HERE = Path(__file__).resolve().parent

app = FastAPI(title="mb-dashboard")
app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")
templates = Jinja2Templates(directory=_HERE / "templates")


def _resolve_project(name: str) -> dict | None:
    """Find project by name in registry."""
    for p in parsers.load_projects():
        if p.get("name") == name:
            return p
    return None


@app.get("/")
def root():
    projects = parsers.load_projects()
    if not projects:
        return HTMLResponse("<h1>No projects registered</h1><p>Run install.sh in a project to register it.</p>")
    first = projects[0]["name"]
    return RedirectResponse(url=f"/projects/{first}/overview")
```

**Step 4: Create minimal template + static dirs so app loads**

```bash
mkdir -p scripts/dashboard/templates/partials
mkdir -p scripts/dashboard/static
touch scripts/dashboard/static/style.css
```

Create minimal `base.html` (placeholder — fleshed out in Task 9):

```html
<!-- scripts/dashboard/templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>mb-dashboard</title>
  <link rel="stylesheet" href="/static/style.css">
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
</head>
<body>
  {% block content %}{% endblock %}
  <div id="modal-container"></div>
</body>
</html>
```

**Step 5: Run — expect PASS**

Run: `python3 -m pytest scripts/dashboard/tests/test_routes.py -v`

**Step 6: Commit**

```bash
git add scripts/dashboard/server.py scripts/dashboard/tests/test_routes.py \
  scripts/dashboard/templates/ scripts/dashboard/static/
git commit -m "feat(dashboard): D1.7 — server app + root redirect + static mount (TDD)"
```

---

## Task 8: TDD routes — overview + board + 404

**Files:**
- Modify: `scripts/dashboard/tests/test_routes.py`
- Modify: `scripts/dashboard/server.py`

**Step 1: Write failing tests**

Append to `test_routes.py`:

```python
class TestOverviewPage:
    def test_returns_200_with_stage(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        client = TestClient(app)
        resp = client.get("/projects/demo/overview")
        assert resp.status_code == 200
        assert "mvp" in resp.text.lower()

    def test_unknown_project_returns_404(self, tmp_home):
        client = TestClient(app)
        resp = client.get("/projects/nope/overview")
        assert resp.status_code == 404


class TestBoardPage:
    def test_returns_200_with_columns(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        write_story(tmp_project, "S1", "todo", "My Story")
        client = TestClient(app)
        resp = client.get("/projects/demo/board")
        assert resp.status_code == 200
        assert "S1" in resp.text

    def test_unknown_project_returns_404(self, tmp_home):
        client = TestClient(app)
        resp = client.get("/projects/nope/board")
        assert resp.status_code == 404
```

**Step 2: Run — expect FAIL**

**Step 3: Add routes to server.py**

```python
from fastapi import HTTPException


@app.get("/projects/{name}/overview", response_class=HTMLResponse)
def overview(request: Request, name: str):
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    path = Path(project["path"])
    return templates.TemplateResponse("overview.html", {
        "request": request,
        "project": project,
        "stage": parsers.get_stage_data(path),
        "stats": parsers.get_story_stats(path),
        "runs": parsers.get_recent_runs(path),
        "projects": parsers.load_projects(),
        "current_page": "overview",
        "inbox_count": parsers.get_inbox_data(path)["total"],
    })


@app.get("/projects/{name}/board", response_class=HTMLResponse)
def board(request: Request, name: str):
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    path = Path(project["path"])
    return templates.TemplateResponse("board.html", {
        "request": request,
        "project": project,
        "columns": parsers.get_board_data(path),
        "projects": parsers.load_projects(),
        "current_page": "board",
        "inbox_count": parsers.get_inbox_data(path)["total"],
    })
```

Create minimal `overview.html` and `board.html` templates (just enough to pass tests):

```html
<!-- scripts/dashboard/templates/overview.html -->
{% extends "base.html" %}
{% block content %}
<div>{{ stage.stage }}</div>
{% endblock %}
```

```html
<!-- scripts/dashboard/templates/board.html -->
{% extends "base.html" %}
{% block content %}
{% for col, stories in columns.items() %}
  {% for s in stories %}
    <div>{{ s.story_id }}</div>
  {% endfor %}
{% endfor %}
{% endblock %}
```

**Step 4: Run — expect PASS**

Run: `python3 -m pytest scripts/dashboard/tests/test_routes.py -v`

**Step 5: Commit**

```bash
git add scripts/dashboard/server.py scripts/dashboard/tests/test_routes.py \
  scripts/dashboard/templates/overview.html scripts/dashboard/templates/board.html
git commit -m "feat(dashboard): D2+D3.1 — overview + board routes (TDD)"
```

---

## Task 9: TDD partial routes — stage, stats, runs, board, inbox-count, story modal

**Files:**
- Modify: `scripts/dashboard/tests/test_routes.py`
- Modify: `scripts/dashboard/server.py`

**Step 1: Write failing tests**

Append to `test_routes.py`:

```python
class TestPartials:
    @pytest.fixture(autouse=True)
    def setup_project(self, tmp_home, tmp_project):
        register_projects(tmp_home, [
            {"name": "demo", "path": str(tmp_project), "stage": "mvp"},
        ])
        self.project_path = tmp_project
        self.client = TestClient(app)

    def test_stage_partial(self):
        resp = self.client.get("/partials/demo/stage")
        assert resp.status_code == 200
        assert "mvp" in resp.text.lower()

    def test_stats_partial(self):
        write_story(self.project_path, "S1", "todo")
        resp = self.client.get("/partials/demo/stats")
        assert resp.status_code == 200

    def test_runs_partial(self):
        write_runs(self.project_path, count=2)
        resp = self.client.get("/partials/demo/runs")
        assert resp.status_code == 200

    def test_board_partial(self):
        write_story(self.project_path, "S1", "todo", "Board Card")
        resp = self.client.get("/partials/demo/board")
        assert resp.status_code == 200
        assert "S1" in resp.text

    def test_inbox_count_partial(self):
        resp = self.client.get("/partials/demo/inbox-count")
        assert resp.status_code == 200

    def test_story_modal_returns_detail(self):
        write_story(self.project_path, "S1", "todo", "My Story", "high")
        resp = self.client.get("/partials/demo/story/S1")
        assert resp.status_code == 200
        assert "My Story" in resp.text

    def test_story_modal_404_if_missing(self):
        resp = self.client.get("/partials/demo/story/NOPE")
        assert resp.status_code == 404

    def test_partial_404_unknown_project(self):
        resp = self.client.get("/partials/nope/stage")
        assert resp.status_code == 404
```

**Step 2: Run — expect FAIL**

**Step 3: Add partial routes to server.py**

```python
# --- Partial routes (HTMX fragments) ---

def _get_project_path(name: str) -> Path:
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    return Path(project["path"])


@app.get("/partials/{name}/stage", response_class=HTMLResponse)
def partial_stage(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse("partials/stage_badge.html", {
        "request": request, "stage": parsers.get_stage_data(path),
    })


@app.get("/partials/{name}/stats", response_class=HTMLResponse)
def partial_stats(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse("partials/stats_grid.html", {
        "request": request, "stats": parsers.get_story_stats(path),
    })


@app.get("/partials/{name}/runs", response_class=HTMLResponse)
def partial_runs(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse("partials/runs_table.html", {
        "request": request, "runs": parsers.get_recent_runs(path),
    })


@app.get("/partials/{name}/board", response_class=HTMLResponse)
def partial_board(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse("partials/board_columns.html", {
        "request": request, "columns": parsers.get_board_data(path),
    })


@app.get("/partials/{name}/inbox-count", response_class=HTMLResponse)
def partial_inbox_count(name: str):
    path = _get_project_path(name)
    count = parsers.get_inbox_data(path)["total"]
    return HTMLResponse(str(count))


@app.get("/partials/{name}/story/{story_id}", response_class=HTMLResponse)
def partial_story_modal(request: Request, name: str, story_id: str):
    path = _get_project_path(name)
    detail = parsers.get_story_detail(path, story_id)
    if not detail:
        raise HTTPException(404, f"Story '{story_id}' not found")
    return templates.TemplateResponse("partials/story_modal.html", {
        "request": request, "story": detail,
    })
```

Create minimal partial templates:

```html
<!-- partials/stage_badge.html -->
<span class="stage-badge stage-{{ stage.stage }}">{{ stage.stage }}</span>
```

```html
<!-- partials/stats_grid.html -->
<div class="stats-grid">{{ stats }}</div>
```

```html
<!-- partials/runs_table.html -->
<div class="runs-table">{% for r in runs %}<div>{{ r.agent }}</div>{% endfor %}</div>
```

```html
<!-- partials/board_columns.html -->
{% for col, stories in columns.items() %}
  {% for s in stories %}<div>{{ s.story_id }}</div>{% endfor %}
{% endfor %}
```

```html
<!-- partials/story_modal.html -->
<div class="modal-overlay"><div class="modal-sheet">
  <h2>{{ story.title }}</h2>
  <p>{{ story.story_id }} — {{ story.priority }}</p>
</div></div>
```

**Step 4: Run — expect PASS**

Run: `python3 -m pytest scripts/dashboard/tests/ -v`

**Step 5: Commit**

```bash
git add scripts/dashboard/
git commit -m "feat(dashboard): D6+D7.1 — partial routes for polling + story modal (TDD)"
```

---

## Task 10: Full templates — `base.html` with sidebar

**Files:**
- Modify: `scripts/dashboard/templates/base.html`

**Step 1: Write the full base template with sidebar, nav, HTMX, modal container**

Extract the sidebar structure from prototype. Key elements:
- Logo mark ("mb") + "mb-dashboard" text
- Section label "PROJECT"
- Project name with stage badge
- Nav items: Overview (icon), Board (icon)
- Inbox badge with count (polled via HTMX)
- `<div id="modal-container"></div>` for story modal
- HTMX CDN + Google Fonts links

Template variables expected: `project`, `projects`, `current_page`, `inbox_count`

**Step 2: Verify manually**

Run: `cd /Users/yanickmingala/code/Yanick-mj/mb-framework && python3 -m scripts.dashboard`
Open: http://localhost:5111 — verify sidebar renders with nav.

**Step 3: Commit**

```bash
git add scripts/dashboard/templates/base.html
git commit -m "feat(dashboard): D1.8 — base template with sidebar + nav"
```

---

## Task 11: Full templates — overview page

**Files:**
- Modify: `scripts/dashboard/templates/overview.html`
- Modify: `scripts/dashboard/templates/partials/stage_badge.html`
- Modify: `scripts/dashboard/templates/partials/stats_grid.html`
- Modify: `scripts/dashboard/templates/partials/runs_table.html`

**Step 1: Build overview with pollable sections**

- Stage badge with color coding (discovery=purple, mvp=orange, pmf=blue, scale=green)
- 4 stat cards in a grid: Total, In Progress, Blocked, Done
- Runs table: last 5 runs with agent, story, action, summary, timestamp
- Each section wrapped in `hx-get="/partials/{name}/..."` + `hx-trigger="every 5s"`

**Step 2: Verify manually**

Test with a registered project that has stories + runs. Verify counts, stage badge, runs table.

**Step 3: Commit**

```bash
git add scripts/dashboard/templates/
git commit -m "feat(dashboard): D2 — overview page templates"
```

---

## Task 12: Full templates — board page

**Files:**
- Modify: `scripts/dashboard/templates/board.html`
- Modify: `scripts/dashboard/templates/partials/board_columns.html`

**Step 1: Build 5-column kanban board**

- Column headers: BACKLOG, TODO, IN PROGRESS, IN REVIEW, DONE with counts
- Story cards with: story_id, title, priority dot (critical=red, high=orange, medium=blue, low=gray), label tags
- Cards have `hx-get="/partials/{name}/story/{id}"` + `hx-target="#modal-container"` + `hx-swap="innerHTML"`
- Board section polled via `hx-trigger="every 5s"`

**Step 2: Verify manually**

Create story files on disk, verify they appear in correct columns. Click a card — should trigger modal (basic at this point).

**Step 3: Commit**

```bash
git add scripts/dashboard/templates/
git commit -m "feat(dashboard): D3 — kanban board templates"
```

---

## Task 13: Full templates — story modal

**Files:**
- Modify: `scripts/dashboard/templates/partials/story_modal.html`

**Step 1: Build modal overlay with story detail**

- Frosted glass backdrop (`backdrop-filter: blur(8px)`)
- Sheet with: story_id badge, title, priority + status pills, created date
- Sections: Why, Scope, Acceptance Criteria (with checkboxes reflecting done state)
- Close: overlay click, X button, Escape key (inline JS, ~10 lines)
- Smooth open animation: scale(0.97) + opacity transition

**Step 2: Verify manually**

Click a board card, verify modal opens with correct data. Close via overlay, X, Escape. Click different cards — modal updates.

**Step 3: Commit**

```bash
git add scripts/dashboard/templates/partials/story_modal.html
git commit -m "feat(dashboard): D6 — story detail modal"
```

---

## Task 14: Extract CSS from prototype

**Files:**
- Modify: `scripts/dashboard/static/style.css`

**Step 1: Extract full `<style>` block from prototype**

Source: `/Users/yanickmingala/mb-bench/prototype-dashboard.html`

Copy the entire CSS (variables, layout, sidebar, cards, board, modal, etc.) into `style.css`. Remove any prototype-only demo styles (inline data, fake content styling).

**Step 2: Verify manually**

Reload localhost:5111. Verify the warm palette, Notion-like sidebar, card shadows, typography all match the prototype aesthetic.

**Step 3: Commit**

```bash
git add scripts/dashboard/static/style.css
git commit -m "feat(dashboard): D1.9 — production CSS from validated prototype"
```

---

## Task 15: Run full test suite + manual smoke test

**Files:** None (verification only)

**Step 1: Run all dashboard tests**

Run: `cd /Users/yanickmingala/code/Yanick-mj/mb-framework && python3 -m pytest scripts/dashboard/tests/ -v`
Expected: All tests PASS

**Step 2: Run existing v2.1 + v2.2 tests (no regressions)**

Run: `python3 -m pytest scripts/v2_1/tests/ scripts/v2_2/tests/ -v`
Expected: All existing tests still PASS

**Step 3: Manual smoke test**

1. Start server: `python3 -m scripts.dashboard`
2. Open http://localhost:5111
3. Verify redirect to first project's overview
4. Check: stage badge, stats grid, runs table
5. Click "Board" in sidebar — verify kanban columns
6. Click a story card — verify modal opens
7. Close modal (X, overlay, Escape)
8. Create a new story file on disk — wait 5s — verify it appears on board
9. Test with 0 projects (remove ~/.mb/projects.yaml) — verify "no projects" page

**Step 4: Commit any fixes**

---

## Task 16: Final cleanup + sprint summary commit

**Step 1: Review all files for leftover debug code, TODOs, print statements**

**Step 2: Final commit**

```bash
git add -A
git commit -m "feat(dashboard): Sprint 1 complete — D1+D2+D3+D6+D7-partial

Delivers:
- FastAPI server on :5111 with project loader
- Overview page (stage, stats, runs)
- Kanban board (5 columns, priority dots, labels)
- Story detail modal (HTMX-powered, frosted glass)
- HTMX polling every 5s on all data sections
- TDD test suite for parsers + routes"
```
