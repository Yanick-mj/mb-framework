# mb-dashboard — Product Requirements Document

**Version:** 2.0
**Status:** Phase 1 complete, Phases 2-7 + Beta planned
**Last updated:** 2026-05-05

---

## 1. Vision

> Make AI-driven product development visible, collaborative, and instantly actionable for the entire product team — not just developers.
>
> Then go further: make the AI team itself learn from elite collaboration patterns, so it behaves like a Telegram, Apple, or SpaceX product squad.

The mb-dashboard evolves from a **read-only viewer** into an **interactive control centre**, and finally into a **training & orchestration console** for an evolving, multi-agent AI team. Markdown files remain the single source of truth throughout.

---

## 2. Phase Overview

| Phase | Name | Core Value | Status |
|-------|------|------------|--------|
| 1 | Read-Only Dashboard (MVP) | Instant visibility of stage, roadmap, board, inbox | Done |
| 2 | Write & Story Management | Update statuses, create stories, edit metadata from UI | Planned |
| 2.1 | Editable Roadmap | Inline editing of mission, milestones in browser | Planned |
| 3 | Live AI Interaction | Execute CLI commands from browser, stream agent output | Planned |
| 4 | Lightweight Multi-User | Identity, activity log, concurrent edits | Planned |
| 5 | Export & Integrations | Jira/Linear, Slack notifications, webhooks | Planned |
| 6 | Advanced Analytics & Automation | Metrics dashboard, auto stage-upgrades | Planned |
| 7 | AI Team Intelligence & Skill Evolution | Dynamic principles, roundtables, culture packs, training loop | Planned |
| Beta | External Team Release | Accounts, project import, onboarding, shared hosting | Planned |

---

## 3. Phase 1: Read-Only Dashboard (MVP) — Done

### 3.1 Goals
- Complete read-only view of any registered mb project.
- Runs entirely locally, zero setup beyond a single Python process.
- Immediately useful for PMs, designers, and stakeholders.

### 3.2 Features Delivered
- Project overview with stage badge + stats grid.
- Roadmap (mission card + milestone cards with tracks tables).
- Kanban board (Backlog, Todo, In Progress, In Review, Done).
- Inbox (in_review + blocked + approvals pending).
- Recent agent runs feed.
- Multi-project dropdown with page-preserving navigation.
- Story detail modal with full markdown content + acceptance criteria.
- HTMX auto-refresh every 5s on all data sections.

### 3.3 Technical Stack
- **Backend:** FastAPI + Jinja2 templates, reading filesystem (`~/.mb/projects.yaml`, `mb-stage.yaml`, `_roadmap.md`, `_backlog/*.md`, `memory/runs.jsonl`).
- **Frontend:** Server-rendered HTML + HTMX (CDN) — zero custom JS to maintain.
- **Deployment:** `python3 -m scripts.dashboard` serves on localhost:5111.
- **Tests:** 50 TDD tests (25 parser unit + 25 route integration).

### 3.4 Key Files
- `scripts/dashboard/server.py` — FastAPI app, routes, Jinja config
- `scripts/dashboard/parsers.py` — data layer wrapping existing v2.1/v2.2 parsers
- `scripts/dashboard/static/style.css` — Notion+BlaBlaCar+Apple aesthetic
- `scripts/dashboard/templates/` — Jinja2 templates + HTMX partials

---

## 4. Phase 2: Write & Story Management — Planned

### 4.1 Goals
- Make the dashboard the primary interface for backlog grooming.
- PMs can manage stories without touching markdown files.

### 4.2 Features
- Drag-and-drop kanban — story status updated in frontmatter.
- Create new story via form (ID auto-generated).
- Inline editing of title, priority, assignee, labels.
- Move story to archive.
- Block / unblock with reasons.

### 4.3 Technical Additions
- `PUT /api/stories/{id}/move` — status change endpoint.
- `POST /api/stories` — create story endpoint.
- `PATCH /api/stories/{id}` — edit metadata endpoint.
- `DELETE /api/stories/{id}` — archive endpoint.
- Atomic writes (`.tmp` + rename) for safe file operations.
- `portalocker` for file locking.

---

## 5. Phase 2.1: Editable Roadmap — Planned

### 5.1 Features
- Inline editing of mission, milestone titles, descriptions, and bullet items (click to edit).
- `PUT /api/projects/{name}/roadmap` endpoint that overwrites `_roadmap.md` while preserving markdown structure.
- Optional automatic backup before each save.

### 5.2 Technical Notes
- Reuse existing roadmap parser to regenerate markdown on save.
- Reuse atomic-write pattern from Phase 2.

---

## 6. Phase 3: Live AI Interaction — Planned

### 6.1 Goals
- Turn the dashboard into a command centre where any team member can trigger AI pipelines and see agent reasoning in real time.

### 6.2 Features
- "Ask Claude" prompt bar with command whitelist.
- WebSocket-based streaming agent output.
- Predefined command shortcuts (validate, ship, sprint, feature).
- Artifact viewer for generated files.

### 6.3 Technical Additions
- WebSocket endpoint `/ws/run` spawning `claude` subprocess.
- Streaming frontend log viewer.

---

## 7. Phase 4: Lightweight Multi-User — Planned

### 7.1 Features
- User identity set in browser (no auth), passed via `X-mb-User` header.
- Activity log (`memory/activity.jsonl`) — who moved what, when.
- Optimistic locking via `If-Match` header vs `last_edited_at`.
- Presence (who is viewing same project) via WebSocket.
- Edit annotations (`last_edited_by`, `last_edited_at`) in story frontmatter.

---

## 8. Phase 5: Export & Integrations — Planned

### 8.1 Features
- Export story to Jira / Linear / GitHub issue (one click).
- Optional two-way sync (linked external ID).
- Slack / Teams notifications on stage upgrade, blocked story, AI run completed.
- Generic webhook for any write event.
- Simple API key authentication for external callers.

---

## 9. Phase 6: Advanced Analytics & Automation — Planned

### 9.1 Features
- DORA-style metrics (lead time, deployment frequency, change failure rate).
- Stage-gate analytics (how long teams spend in each stage).
- Agent performance scoring.
- Custom dashboards with widgets.
- Auto stage-upgrades when criteria are met.

---

## 10. Phase 7: AI Team Intelligence & Skill Evolution — Planned

### 10.1 Core Concept
Transform agents from static `SKILL.md` rules to a **trainable, multi-role AI team** where:
- Each role is driven by a **principle card** — compact decision-making compasses.
- The orchestrator runs **multi-agent roundtables** where PM, engineer, designer debate before decisions.
- The team can follow a **culture pack**: Telegram (hyper-pragmatic), Apple (creative abrasion), SpaceX (first-principles).
- The system **learns from outcomes** via scored decision artifacts.

### 10.2 Components

#### Principle Cards
```yaml
agent: pm
principles:
  - source: "Inspired (M. Cagan)"
    rule: "Fall in love with the problem, not the solution."
  - source: "Teresa Torres"
    rule: "Every feature should start with an assumption test."
```

#### Multi-Agent Roundtable
Facilitator kicks off prompt -> PM proposes scope -> Engineer challenges feasibility -> Designer brings UX constraints -> Facilitator synthesizes final decision. Transcript stored as training record.

#### Culture Packs
- **Telegram:** Collapsed roles, minimal deliberation, quick async decisions.
- **Apple:** High creative tension, design as non-negotiable, elegant solutions.
- **SpaceX:** First-principles physics, challenge industry norms, radically simpler.

Selected via dashboard, stored in `mb-stage.yaml` as `culture:` field.

#### Training Loop (RLHF / DPO)
1. Collect traces — roundtable transcripts + artifacts.
2. Score — boldness, simplicity, testability, first-principles usage.
3. Preference dataset — pair good/mediocre transcripts.
4. Fine-tune — DPO on base model or prompt-tuning.
5. Regression tests — replay canonical scenarios.

### 10.3 New File Structure
```
mb-framework/
├── agents-dynamic/    # Principle card overrides
├── culture_packs/     # telegram.yaml, apple.yaml, spacex.yaml
├── training/          # Scoring + fine-tuning scripts
└── memory/training/   # Debate logs + decision scores
```

---

## 11. Beta Release: External Team Testing — Planned

### 11.1 Requirements
- External teams can create an account (simple auth).
- Import existing mb-framework project (Git clone or ZIP upload).
- Create new project directly from dashboard.
- Self-contained product experience.

### 11.2 Deployment Options
- **A. Self-hosted:** One-line Docker command or Python install script.
- **B. Centralised cloud (for beta):** Single-tenant instance, workspace per team.

### 11.3 Implementation
- FastAPI + SQLite user store for accounts.
- Workspaces with isolated directories (`/var/mb-data/workspaces/{id}/`).
- Login/Register pages + workspace selector.
- Import wizard (Git clone, ZIP upload, or create new).
- Sandboxed `claude` subprocess per workspace.

---

## 12. Timeline

```
Phase 1:   ████████████████████████████ 100%  (Done)
Phase 2:   ░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  (~2 weeks)
Phase 2.1: ░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  (~2 days)
Phase 3:   ░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  (~2 weeks)
Beta:      ░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  (~3 weeks)
Phase 4:   ░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  (~2 weeks)
Phase 5:   ░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  (~2 weeks)
Phase 6:   ░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  (~2 weeks)
Phase 7:   ░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  (~6 weeks)
```

Beta can start after Phase 2.1 is stable — it adds multi-tenancy that later phases build on.
