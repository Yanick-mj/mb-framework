# Roadmap — mb-framework

## Current Stage

`pmf` — mb is in active use by the author (1 real user), refining with feedback.
Full v1 gates ON (TDD, Atomic, DS gate, RLS double-check).

## Mission

Build a markdown-only, zero-infra agent framework that helps solo-entrepreneurs
and small dev agencies structure their AI-assisted workflow from idea validation
through production scale. Stage-aware. Works with Claude today, any LLM tomorrow.

## Next Milestone

Ship v2.2.0 (governance + layers + views) within 2 weeks. Dogfood on Otoqi +
Studio IRIS + one new project. Decide on v3 commercial direction based on usage.

---

## Phases

### Phase 1 — v2.2 structural (2 weeks)

**Goal:** Add the 5 features that make mb viable for multi-project, stage-safe usage.

| Track | Work | Owner |
|---|---|---|
| Governance | Tool RBAC + audit (STU-F) | Yanick |
| Layers | Memory reorganization + migration (STU-H) | Yanick |
| Discovery | Skills namespace + registry (STU-G) | Yanick |
| Visibility | /mb:inbox (STU-I) | Yanick |
| Visibility | /mb:board (STU-J) | Yanick |

Recommended execution order: **F → H → G → I → J**.

**Exit criteria:**
- All 5 backlog stories (STU-F..J) are `done`
- Tag `v2.2.0` pushed
- mb v2.2.0 installed on Otoqi, Studio IRIS, one new project (dogfood)
- Zero regression: all v2.1 tests still green

### Phase 1b — Read-Only Dashboard MVP

**Goal:** Browser-based dashboard giving PMs and stakeholders instant visibility without CLI access

| Track | Work | Owner |
|---|---|---|
| Backend | FastAPI server + parsers + routes | Claude (be-dev) |
| Frontend | Jinja2 + HTMX templates + CSS | Claude (fe-dev) |
| Product | Validate with PMs, smoke test | Yanick |

**Exit criteria:** All 8 stories done, 50 tests passing, Playwright smoke test approved

### Phase 2 — v2.3 polish + early stage-transition triggers (1 month)

**Goal:** Based on v2.2 dogfood, fix the 3-5 biggest friction points found.

| Track | Work (TBD) | Owner |
|---|---|---|
| UX | Inbox bulk actions? | TBD |
| DevX | Auto-clone git skills in /mb:skill add? | TBD |
| Data | Split runs.jsonl per-agent? | TBD |

**Exit criteria:** decided after 2 weeks of v2.2 real usage. No speculative scope.

### Phase 2b — Dashboard Write & Story Management

**Goal:** Make the dashboard the primary interface for backlog grooming

| Track | Work | Owner |
|---|---|---|
| Backend | CRUD endpoints + atomic writes + file locking | TBD |
| Frontend | Drag-drop kanban + inline editing + create form | TBD |
| Product | Test with real backlog workflow | Yanick |

**Exit criteria:** PM can create, edit, move, and archive stories entirely from the browser

### Phase 3 — v3.0 commercial (starts earliest month 3)

**Goal:** Implement the commercial roadmap from `docs/vision/roadmap.md` §2.

| Track | Work | Owner |
|---|---|---|
| Adapter layer | Claude / Ollama / OpenAI swappable | Yanick |
| MCP server | Expose /mb:validate + /mb:ship as MCP tools | Yanick |
| Web UI local | mb-studio (read-only first) | Yanick |

**Entry gate:** 50+ GitHub stars OR 3+ non-Yanick users actively using v2.2.
Otherwise, stay solo-focus.

### Phase 3b — Dashboard Live AI Interaction

**Goal:** Trigger AI pipelines from the browser and see agent reasoning in real time

| Track | Work | Owner |
|---|---|---|
| Backend | WebSocket endpoint + subprocess spawning | TBD |
| Frontend | Streaming log viewer + command shortcuts | TBD |

**Exit criteria:** User can run /mb:feature from dashboard and watch agent output live

---

## Decisions log

- 2026-04-19 — Ship v2.1.0 (solo quality-of-life: A-E) — inspired by paperclip analysis
- 2026-04-19 — Ship v2.1.1 (code review fixes: I1-I4, M3, M7, M8)
- 2026-04-19 — Ship v2.1.2 (emoji coherence + M10 strict priority)
- 2026-04-19 — Agree v2.2 scope: F-J, 5 features, 5 backlog stories, detailed plan
- 2026-04-19 — Decision order for execution: F → H → G → I → J (safety-first, then structural)
- 2026-04-19 — Strict mode as global pattern: reject invalid values (no silent defaults)
- 2026-05-04 — Stack: FastAPI + Jinja2 + HTMX (server-rendered, 0 JS to maintain)
- 2026-05-04 — Design: Notion + BlaBlaCar + Apple aesthetic
- 2026-05-05 — Phase 1 dashboard shipped, merged via PR #1 (23 commits, 50 tests)
