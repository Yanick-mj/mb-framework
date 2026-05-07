# mb-framework

Portable, markdown-only AI agent framework for Claude Code. Zero code dependencies.

Replaces complex AI agent infrastructure (embeddings, vector stores, message buses) with structured markdown files that Claude Code natively understands.

**v2 is stage-aware**: the framework adapts its pipeline from idea validation (discovery) through production (scale). v1 projects keep working unchanged — v2 is additive and opt-in. See [docs/v2-migration.md](docs/v2-migration.md).

## Quick Start

```bash
# Add as submodule to your project
cd your-project
git submodule add git@github.com:Yanick-mj/mb-framework.git .claude/mb
cd .claude/mb && git checkout v2.2.2 && cd ../..   # pin to stable

# One-time global dep
pip3 install --user pyyaml

# Install: wires Claude Code symlinks + registers project + offers shell helper
bash .claude/mb/install.sh
# → pick stage: 1=discovery 2=mvp 3=pmf 4=scale (default)

# Initialize: scaffold directories, generate CLAUDE.md + _roadmap.md
# + seed first backlog story. Deterministic Python + Claude pattern detection.
# Then in Claude Code:
/mb:init
```

After `/mb:init` you have:
- `CLAUDE.md` (stack-aware, edit to add conventions)
- `_roadmap.md` (fill in mission + next milestone)
- `_backlog/STU-1-initial-setup.md` (first task)
- `_mb-output/` + `memory/` directory skeleton
- `memory/project.md` + `memory/codebase-index.md` (auto-generated)

## The 4 Stages (v2)

| Stage | Purpose | Key commands | Gates |
|---|---|---|---|
| **discovery** | Validate an idea before coding | `/mb:validate` | 1-liner gate, YC 10Q, anti-tarpit |
| **mvp** | Ship a janky wedge in < 48h | `/mb:ship` | Deploy + 1 real user only |
| **pmf** | Refine with real users | `/mb:feature`, `/mb:sprint` | Full v1 pipeline activates |
| **scale** | Production discipline | `/mb:feature`, `/mb:sprint` | TDD + Atomic + DS UPDATE GATE + RLS |

Projects without `mb-stage.yaml` default to `scale` → strict v1 behavior (zero-risk retrocompat).

## What's Inside

| Folder | Purpose |
|---|---|
| `agents/` | 13 v1 agent personas (orchestrator, lead-dev, be-dev, fe-dev, devops, architect, verifier, tea, pm, sm, ux-designer, quick-flow, tech-writer) |
| `agents-early/` | **v2** 4 early-stage agents (stage-advisor, idea-validator, user-interviewer, wedge-builder) |
| `commands/` | Entry points: `/mb:feature`, `/mb:sprint`, `/mb:fix`, `/mb:review`, `/mb:init`, **v2**: `/mb:stage`, `/mb:validate`, `/mb:ship` |
| `skills/` | Injectable domain knowledge (ux-design, project-specific) |
| `scripts/dashboard/` | **v2.3** Browser dashboard — FastAPI + Jinja2 + HTMX (localhost:5111) |
| `templates/` | Code scaffolding, validation checklists, stack conventions |
| `tools/` | External tool catalog + permissions |
| `creds/` | Credentials (.gitignored) |
| `memory/` | Persistent project memory + ephemeral session state + **v2** stage/wedge logs |
| `docs/` | **v2** PRD, migration guide |

## Commands

### v1 (all stages)

| Command | Description |
|---|---|
| `/mb:feature "description"` | Classify task, route to agent pipeline, implement |
| `/mb:sprint` | Pick next ready-for-dev story, execute pipeline |
| `/mb:fix "bug"` | Debug and fix a bug |
| `/mb:review` | Code review current changes |
| `/mb:init` | Scan project, generate codebase index + memory |

### v2 (stage-aware)

| Command | Stage | Description |
|---|---|---|
| `/mb:stage` | any | Show current stage, criteria progress, upgrade / downgrade |
| `/mb:validate "idea"` | discovery | 1-liner gate → YC 10Q scoring → anti-tarpit → go/no-go report |
| `/mb:ship "wedge"` | mvp | Skip all v1 gates, build single-file wedge, deploy, invite 5 users |

### v2.1 (solo quality-of-life)

| Command | Description |
|---|---|
| `/mb:projects` | List every registered mb project (multi-project overview) |
| `/mb:tree [STU-X]` | Show story hierarchy as ASCII tree (optional: focus on one) |
| `/mb:runs [N]` | Show last N structured agent runs from `memory/runs.jsonl` |
| `/mb:deliverables STU-X` | List typed artifacts (PLAN/IMPL/REVIEW/DOC) for a story |
| `/mb:backlog` | Show `_backlog/` priority-sorted |
| `/mb:roadmap` | Show `_roadmap.md` at project root |

Also installs a `mb <name>` shell helper so `mb drivia` = `cd ~/projects/drivia && claude`.
`mb dashboard` launches the browser dashboard.

### v2.2 (structural — governance, layers, views)

| Command | Description |
|---|---|
| `/mb:tool list` | Show external tools declared in `tools/_catalog.yaml` |
| `/mb:tool check <agent> <tool> <action>` | RBAC check — deny-by-default, stage-aware |
| `/mb:tool audit [N]` | Last N tool access decisions (ALLOWED/DENIED log) |
| `/mb:skill list` | Registered skills (only these are discoverable) |
| `/mb:skill add <tier>/<key> [source]` | Register a new skill |
| `/mb:skill remove <tier>/<key>` | Unregister (files preserved) |
| `/mb:inbox` | Unified blockers: in_review + blocked + approvals pending |
| `/mb:board` | ASCII kanban of all stories by status |

**Architecture change (v2.2):** agents are now split into 3 layers —
`AGENT.md` (persona), `uses-skills.yaml` (declared skills), and
`skills/core/*/SKILL.md` (shared capabilities). At install time,
`scripts/v2_2/agent_loader.py` composes these into the single
`.claude/skills/mb-{name}/SKILL.md` file Claude Code loads. Legacy
unmigrated agents keep working via fallback.

### v2.4 — Independence cut from BMAD naming (rc1)

mb writes its artifacts under `_mb-output/` instead of `_bmad-output/`.
A read-compat fallback in `scripts.v2_2._paths.output_root_for()` keeps
pre-v2.4 projects working without migration; new projects scaffolded by
`/mb:init` always create `_mb-output/`. The fallback is removed at v2.5
— migrate by renaming the directory:

```bash
mv _bmad-output _mb-output
```

Currently shipped as `v2.4.0-rc1` for dogfood. Promotion to `v2.4.0`
after real-usage validation.

### v2.3 — Browser Dashboard

| Command | Description |
|---|---|
| `/mb:dashboard` | Launch browser dashboard on localhost:5111 |

Also available from terminal: `mb dashboard` (opens browser automatically).

**Requires:** `pip install fastapi uvicorn jinja2` (one-time). Missing deps produce a helpful error with install command.

#### Current (Phase 1 — Read-Only MVP)
- **Overview:** stage badge, story stats, recent agent runs
- **Board:** 5-column kanban with priority dots, labels, click-to-open story modal
- **Roadmap:** mission card, milestone cards with tracks tables
- **Inbox:** in_review + blocked + approvals pending
- **Multi-project switcher** with page-preserving navigation
- **HTMX auto-refresh** every 5s on all data sections
- Design: Notion + BlaBlaCar + Apple aesthetic (warm palette, frosted glass modals)

#### Planned Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | Read-Only Dashboard (MVP) | Done |
| 2 | Write & Story Management (drag-drop kanban, create/edit stories) | Planned |
| 2.1 | Editable Roadmap (inline editing of mission & milestones) | Planned |
| 3 | Live AI Interaction (trigger CLI commands from browser, stream output) | Planned |
| 4 | Lightweight Multi-User (identity, activity log, presence) | Planned |
| 5 | Export & Integrations (Jira/Linear, Slack, webhooks) | Planned |
| 6 | Advanced Analytics & Automation (DORA metrics, auto stage-upgrades) | Planned |
| 7 | AI Team Intelligence (principle cards, multi-agent roundtables, culture packs) | Planned |
| Beta | External Team Release (accounts, project import, shared hosting) | Planned |

See [`docs/dashboard-prd.md`](docs/dashboard-prd.md) for full phase details.

### v2.2.1 / v2.2.2 — Orchestrator auto-invoke (hook)

On install, mb adds a `UserPromptSubmit` hook to `.claude/settings.json`
that injects a system-reminder asking Claude to invoke `mb-orchestrator`
BEFORE any file edit — so free-form prompts ("fix X", "connect to Vercel",
"implémente Y") route through the orchestrator instead of falling into
ad-hoc edits.

**v2.2.2 change:** the action-verb regex filter was removed. Real prompts
used verbs the list didn't cover (`connect`, `lier`, `pointer`, `switch`…)
and got false-negatived. The orchestrator itself now decides if a prompt
is Q&A (direct answer) or action (pipeline). Four hard guards stay silent:

1. Slash commands (`/mb:feature` etc. — they handle their own routing)
2. Empty prompt
3. Fewer than 4 words
4. Explicit opt-out phrase or env var (below)

**Opt-out per prompt:** include `"skip orchestrator"`, `"quick answer"`,
`"no orchestrator"`, or `"sans orchestrator"` anywhere in your message.
**Opt-out per session:** `export MB_ORCHESTRATOR_AUTOINVOKE=off`.
**Opt-out permanently:** `python3 -m scripts.v2_2.install_hooks $(pwd)/.claude/mb --remove`.

**Requires:** `pip install pyyaml` once (helpers degrade gracefully if missing).

## How It Works (v1 pipeline, e.g. scale stage)

```
/mb:feature "add pagination"
  → orchestrator Step 0.5: read mb-stage.yaml (or default scale)
  → orchestrator classifies (feature_frontend, medium)
  → reads mb-config.yaml + codebase-index.md
  → pipeline: architect → fe-dev → verifier
  → each agent reads/writes memory/_session/handoff.md
  → verifier runs lint + tsc + tests
  → cost logged to memory/cost-log.md
```

## How It Works (v2 early-stage, e.g. discovery)

```
/mb:validate "Uber for X"
  → orchestrator Step 0.5: reads stage=discovery
  → Stage Routing Table: discovery + "validate" → idea-validator
  → idea-validator:
      1-liner gate (≤10 words, grandmother test)
      10Q YC framework (score /30)
      anti-tarpit checklist (CISP, tarpit, perfect-idea, first-idea-reflex)
      WebFetch market research
  → writes _discovery/{slug}/go-no-go-report.md
  → verdict: go | validate-with-interviews | no-go
```

## Configuration

- `mb-config.yaml` — agent toggles, pipeline behavior, tracking. Includes `stage_aware` section (v2).
- `mb-stage.yaml` (at YOUR project root) — current stage, upgrade criteria, per-gate overrides. See [mb-stage.yaml.template](mb-stage.yaml.template).

## Adding Project-Specific Skills

After `/mb:init`, add domain knowledge to `project-skills/`:

```
project-skills/
└── my-api/SKILL.md     # API patterns, conventions, gotchas
```

## Versioning

Tags trace the trajectory. Pin one in your submodule with `git checkout <tag>`.

| Tag | What it brings | Status |
|---|---|---|
| `v2.0.0` | Stage-aware mode (4 stages, agents-early, /mb:stage, /mb:validate, /mb:ship). Retrocompat: projects without `mb-stage.yaml` keep v1. | superseded |
| `v2.1.0` → `v2.1.6` | Solo quality-of-life: multi-project, /mb:tree, /mb:runs, /mb:deliverables, /mb:backlog, /mb:roadmap. Plus security and pipeline-enforcement patches. /mb:init scaffolder. | superseded |
| `v2.2.0` | Structural: tool RBAC, 3-layer agents (AGENT.md + uses-skills.yaml + skills/core/*), memory layers, /mb:inbox, /mb:board. | **stable** |
| `v2.2.1` / `v2.2.2` | Orchestrator auto-invoke hook (`UserPromptSubmit`); v2.2.2 drops the action-verb regex filter. | **stable** |
| `v2.4.0-rc1` | Independence cut from BMAD naming (`_mb-output/` becomes default; legacy `_bmad-output/` read-compat fallback until v2.5). | release candidate |

Branches:
- `master` — points at `v2.2.2` (current stable)
- `v2` — historical stage-aware branch (kept for older submodule pins)
- `feat/dashboard-sprint3` — v2.3 dashboard work (sprint 3 in progress, not yet merged)
- `v2.4-independence` — v2.4 cut, where `v2.4.0-rc1` is tagged

Submodule pins: `git submodule add -b v2 ...` or `git checkout <tag>` after add.

## Documentation

- [`_roadmap.md`](_roadmap.md) — current roadmap (active phases, decisions log)
- [`docs/vision/roadmap.md`](docs/vision/roadmap.md) — long-term commercial trajectory
- [`docs/v2-prd.md`](docs/v2-prd.md) — full v2 PRD (16 sections, 566 lines)
- [`docs/v2-migration.md`](docs/v2-migration.md) — v1 → v2 migration guide
- [`docs/dashboard-prd.md`](docs/dashboard-prd.md) — dashboard PRD (8 phases)
- `agents/*/SKILL.md` — per-agent specs (interface, persona, rules, stage adaptation)
- `agents-early/*/SKILL.md` — v2 early-stage agent specs

## License

MIT
