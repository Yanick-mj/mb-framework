"""FastAPI application for mb-dashboard."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
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


def _get_project_path(name: str) -> Path:
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    return Path(project["path"])


@app.get("/")
def root():
    projects = parsers.load_projects()
    if not projects:
        return HTMLResponse("<h1>No projects registered</h1><p>Run install.sh in a project to register it.</p>")
    first = projects[0]["name"]
    return RedirectResponse(url=f"/projects/{first}/overview")


@app.get("/projects/{name}/overview", response_class=HTMLResponse)
def overview(request: Request, name: str):
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    path = Path(project["path"])
    return templates.TemplateResponse(request, "overview.html", context={
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
    return templates.TemplateResponse(request, "board.html", context={
        "project": project,
        "columns": parsers.get_board_data(path),
        "projects": parsers.load_projects(),
        "current_page": "board",
        "inbox_count": parsers.get_inbox_data(path)["total"],
    })


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


# --- Partial routes (HTMX fragments) ---


@app.get("/partials/{name}/stage", response_class=HTMLResponse)
def partial_stage(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/stage_badge.html", context={
        "stage": parsers.get_stage_data(path),
    })


@app.get("/partials/{name}/stats", response_class=HTMLResponse)
def partial_stats(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/stats_grid.html", context={
        "stats": parsers.get_story_stats(path),
    })


@app.get("/partials/{name}/runs", response_class=HTMLResponse)
def partial_runs(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/runs_table.html", context={
        "runs": parsers.get_recent_runs(path),
    })


@app.get("/partials/{name}/board", response_class=HTMLResponse)
def partial_board(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/board_columns.html", context={
        "columns": parsers.get_board_data(path),
        "project": {"name": name},
    })


@app.get("/partials/{name}/inbox", response_class=HTMLResponse)
def partial_inbox(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/inbox_items.html", context={
        "inbox": parsers.get_inbox_data(path),
        "project": {"name": name},
    })


@app.get("/partials/{name}/inbox-count", response_class=HTMLResponse)
def partial_inbox_count(name: str):
    path = _get_project_path(name)
    count = parsers.get_inbox_data(path)["total"]
    return HTMLResponse(str(count))


@app.get("/partials/{name}/roadmap", response_class=HTMLResponse)
def partial_roadmap(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/roadmap_content.html", context={
        "project": {"name": name},
        "roadmap": parsers.get_roadmap_data(path),
    })


@app.get("/partials/{name}/phase/{idx}", response_class=HTMLResponse)
def partial_phase_modal(request: Request, name: str, idx: int):
    path = _get_project_path(name)
    data = parsers.get_roadmap_data(path)
    phases = data.get("phases", [])
    if idx < 0 or idx >= len(phases):
        raise HTTPException(404, f"Phase {idx} not found")
    return templates.TemplateResponse(request, "partials/phase_modal.html", context={
        "phase": phases[idx],
    })


@app.get("/partials/{name}/story/{story_id}", response_class=HTMLResponse)
def partial_story_modal(request: Request, name: str, story_id: str):
    path = _get_project_path(name)
    detail = parsers.get_story_detail(path, story_id)
    if not detail:
        raise HTTPException(404, f"Story '{story_id}' not found")
    return templates.TemplateResponse(request, "partials/story_modal.html", context={
        "story": detail,
    })
