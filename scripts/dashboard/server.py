"""FastAPI application for mb-dashboard."""
from __future__ import annotations

from pathlib import Path

from typing import Literal

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator

from scripts.dashboard import crud, parsers

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
def board(request: Request, name: str, priority: str | None = None):
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    path = Path(project["path"])
    return templates.TemplateResponse(request, "board.html", context={
        "project": project,
        "columns": parsers.get_board_data(path, priority_filter=priority),
        "projects": parsers.load_projects(),
        "current_page": "board",
        "inbox_count": parsers.get_inbox_data(path)["total"],
        "priority_filter": priority or "",
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


@app.get("/projects/{name}/sprints/{sprint_id}", response_class=HTMLResponse)
def sprint_detail(request: Request, name: str, sprint_id: str):
    project = _resolve_project(name)
    if not project:
        raise HTTPException(404, f"Project '{name}' not found")
    path = Path(project["path"])
    sprint = parsers.get_sprint(path, sprint_id)
    if not sprint:
        raise HTTPException(404, f"Sprint '{sprint_id}' not found")
    from scripts.v2_2.board import COLUMNS
    board = {c: [] for c in COLUMNS}
    for story in sprint["resolved_stories"]:
        status = story.get("status", "backlog")
        if status in board:
            board[status].append(story)
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
def partial_board(request: Request, name: str, priority: str | None = None):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/board_columns.html", context={
        "columns": parsers.get_board_data(path, priority_filter=priority),
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


@app.get("/partials/{name}/sprints", response_class=HTMLResponse)
def partial_sprints(request: Request, name: str):
    path = _get_project_path(name)
    return templates.TemplateResponse(request, "partials/sprint_list.html", context={
        "sprints": parsers.get_sprints_data(path),
        "project": {"name": name},
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
    deliverables = parsers.get_deliverables_list(path, story_id)
    return templates.TemplateResponse(request, "partials/story_modal.html", context={
        "story": detail,
        "project_name": name,
        "deliverables": deliverables,
    })


@app.get("/partials/{name}/create-story", response_class=HTMLResponse)
def partial_create_story_form(request: Request, name: str):
    _get_project_path(name)  # validates project exists
    return templates.TemplateResponse(request, "partials/create_story_form.html", context={
        "project_name": name,
    })


@app.get("/partials/{name}/edit-story/{story_id}", response_class=HTMLResponse)
def partial_edit_story_form(request: Request, name: str, story_id: str):
    path = _get_project_path(name)
    detail = parsers.get_story_detail(path, story_id)
    if not detail:
        raise HTTPException(404, f"Story '{story_id}' not found")
    return templates.TemplateResponse(request, "partials/edit_story_form.html", context={
        "project_name": name,
        "story": detail,
    })


# --- CRUD API routes ---


AllowedStatus = Literal["backlog", "todo", "in_progress", "in_review", "done"]
AllowedPriority = Literal["critical", "high", "medium", "low"]


class CreateStoryRequest(BaseModel):
    title: str
    description: str = ""
    priority: AllowedPriority = "medium"
    status: AllowedStatus = "todo"


class UpdateStoryRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: AllowedPriority | None = None
    status: AllowedStatus | None = None


class PatchStatusRequest(BaseModel):
    status: AllowedStatus


def _do_create(name: str, title: str, description: str, priority: str, status: str) -> dict:
    path = _get_project_path(name)
    return crud.create_story(project_path=path, title=title, description=description,
                             priority=priority, status=status)


def _do_update(name: str, story_id: str, updates: dict) -> dict:
    path = _get_project_path(name)
    result = crud.update_story(path, story_id, updates)
    if result is None:
        raise HTTPException(404, f"Story '{story_id}' not found")
    return result


@app.post("/api/stories/{name}", status_code=201)
def api_create_story(name: str, body: CreateStoryRequest):
    return _do_create(name, body.title, body.description, body.priority, body.status)


@app.post("/api/stories/{name}/form", status_code=201, response_class=HTMLResponse)
def api_create_story_form(
    name: str,
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    status: str = Form("todo"),
):
    _do_create(name, title, description, priority, status)
    return HTMLResponse("")


@app.put("/api/stories/{name}/{story_id}")
def api_update_story(name: str, story_id: str, body: UpdateStoryRequest):
    return _do_update(name, story_id, body.model_dump(exclude_none=True))


@app.post("/api/stories/{name}/{story_id}/form", response_class=HTMLResponse)
def api_update_story_form(
    name: str,
    story_id: str,
    title: str = Form(None),
    description: str = Form(None),
    priority: str = Form(None),
    status: str = Form(None),
):
    updates = {k: v for k, v in {"title": title, "description": description,
               "priority": priority, "status": status}.items() if v is not None}
    _do_update(name, story_id, updates)
    return HTMLResponse("")


@app.get("/api/stories/{name}/{story_id}/deliverables")
def api_list_deliverables(name: str, story_id: str):
    path = _get_project_path(name)
    if not crud._find_story_file(path, story_id):
        raise HTTPException(404, f"Story '{story_id}' not found")
    return parsers.get_deliverables_list(path, story_id)


@app.get("/api/stories/{name}/{story_id}/deliverables/{filename}")
def api_get_deliverable(name: str, story_id: str, filename: str):
    path = _get_project_path(name)
    result = parsers.get_deliverable_content(path, story_id, filename)
    if result is None:
        raise HTTPException(404, f"Deliverable '{filename}' not found")
    return result


class CommentRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Comment text cannot be empty")
        return v


@app.post("/api/stories/{name}/{story_id}/comment")
def api_add_comment(name: str, story_id: str, body: CommentRequest):
    path = _get_project_path(name)
    result = crud.add_comment(path, story_id, body.text)
    if result is None:
        raise HTTPException(404, f"Story '{story_id}' not found")
    return result


class ReorderRequest(BaseModel):
    sort_order: int


@app.patch("/api/stories/{name}/{story_id}/reorder")
def api_reorder_story(name: str, story_id: str, body: ReorderRequest):
    path = _get_project_path(name)
    result = crud.reorder_story(path, story_id, body.sort_order)
    if result is None:
        raise HTTPException(404, f"Story '{story_id}' not found")
    return result


@app.patch("/api/stories/{name}/{story_id}/status")
def api_patch_status(name: str, story_id: str, body: PatchStatusRequest):
    path = _get_project_path(name)
    result = crud.patch_status(path, story_id, body.status)
    if result is None:
        raise HTTPException(404, f"Story '{story_id}' not found")
    return result


@app.delete("/api/stories/{name}/{story_id}")
def api_delete_story(name: str, story_id: str):
    path = _get_project_path(name)
    result = crud.delete_story(path, story_id)
    if result is None:
        raise HTTPException(404, f"Story '{story_id}' not found")
    return result


# --- Sprint API routes ---


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
