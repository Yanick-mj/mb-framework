# Roadmap — mb-framework

## Current Stage

mvp

## Mission

Make mb-framework the standard toolkit for solo developers and small teams managing multi-project portfolios with Claude Code — from idea validation to production.

## Next Milestone

Phase 2 — Write & Story Management: drag-drop kanban, create/edit stories from the dashboard.

---

## Phases

### Phase 1 — Read-Only Dashboard MVP (weeks 1-2)

**Goal:** Browser-based dashboard giving PMs and stakeholders instant visibility without CLI access

| Track | Work | Owner |
|---|---|---|
| Backend | FastAPI server + parsers + routes | Claude (be-dev) |
| Frontend | Jinja2 + HTMX templates + CSS | Claude (fe-dev) |
| Product | Validate with PMs, smoke test | Yanick |

**Exit criteria:** All 8 stories done, 50 tests passing, Playwright smoke test approved

### Phase 2 — Write & Story Management (weeks 3-4)

**Goal:** Make the dashboard the primary interface for backlog grooming

| Track | Work | Owner |
|---|---|---|
| Backend | CRUD endpoints + atomic writes + file locking | TBD |
| Frontend | Drag-drop kanban + inline editing + create form | TBD |
| Product | Test with real backlog workflow | Yanick |

**Exit criteria:** PM can create, edit, move, and archive stories entirely from the browser

### Phase 3 — Live AI Interaction (weeks 5-6)

**Goal:** Trigger AI pipelines from the browser and see agent reasoning in real time

| Track | Work | Owner |
|---|---|---|
| Backend | WebSocket endpoint + subprocess spawning | TBD |
| Frontend | Streaming log viewer + command shortcuts | TBD |

**Exit criteria:** User can run /mb:feature from dashboard and watch agent output live

---

## Decisions log

- 2026-05-04 — Stack: FastAPI + Jinja2 + HTMX (server-rendered, 0 JS to maintain) — rationale: simplicity, reuses existing Python parsers
- 2026-05-04 — Design: Notion + BlaBlaCar + Apple aesthetic — rationale: validated prototype with stakeholders
- 2026-05-05 — Phase 1 shipped, merged via PR #1 (23 commits, 50 tests)
