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
