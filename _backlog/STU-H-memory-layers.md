---
story_id: STU-H
title: Memory layers (project/agents/stories/session) + migration
priority: high
created: 2026-04-19
plan_ref: docs/plans/2026-04-19-v2.2-tools-skills-memory-inbox-board.md
tasks: [H1, H2, H3]
---

# Memory layers

## Why

`memory/` in v2.1 is flat: long-term artifacts (cost-log, codebase-index) mix with
per-story handoff, per-run log, per-agent instructions. Inbox (I) and board (J)
need clear boundaries to aggregate sanely. Four layers: project, agents, stories,
session.

## Scope

In:
- `scripts/v2_2/memory.py` — `write/read/append(layer, filename, ...)`
- `scripts/v2_2/migrate_memory.py` — idempotent dry-run/apply migrator
- `scripts/v2_1/runs.py` — v2.2-aware fallback (prefers new path if layout exists)

Out:
- Automatic migration on install (opt-in via `--apply`)
- Cloud sync (Phase 3 of commercial roadmap)
- Per-agent runs.jsonl separation (v2.2 keeps one shared log in `agents/_common/runs.jsonl`;
  v2.3 can split if agents-specific queries become frequent)

## Acceptance criteria

- [ ] `memory.write("project", "mission.md", "x")` writes to `memory/project/mission.md`
- [ ] `memory.write("agents", "instructions.md", "x", agent="fe-dev")` writes correctly
- [ ] `memory.write("spaceship", ...)` raises ValueError
- [ ] migrate_memory dry-run reports what would move, touches nothing
- [ ] migrate_memory --apply moves the 5 known files + _session/ dir
- [ ] Running migrate_memory --apply twice is a no-op (idempotent)
- [ ] runs.py writes to new path (agents/_common/runs.jsonl) if dir exists, else old path

## Dependencies / blockers

Depends on: Task 0 (scaffold)
Blocks: I (inbox uses stories/ path), J (board uses stories/ path)

## Notes

Migration is backward-compatible. Existing otoqi-test can run v2.2.0 without
migrating — flat memory/ keeps working. Migration is a choice, not a requirement.
