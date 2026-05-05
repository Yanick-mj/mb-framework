---
story_id: STU-J
title: /mb:board ASCII kanban
priority: low
created: 2026-04-19
plan_ref: docs/plans/2026-04-19-v2.2-tools-skills-memory-inbox-board.md
parent_story: STU-H
tasks: [J1, J2]
---

# /mb:board

## Why

Visual status glance in the terminal. Paperclip has a kanban UI. mb can
do it in ASCII for free — 5 columns (backlog/todo/in_progress/in_review/done),
counts per column, stories stacked.

## Scope

In:
- `scripts/v2_2/board.py` with 5-column renderer using Unicode box-drawing
- Command `/mb:board`
- Strict column whitelist: unknown statuses silently skipped (like M10)

Out:
- Story drag-between-columns in terminal (out of scope for plain bash)
- Filtering by parent/child, owner, tags — v2.3
- Swimlanes (per-agent rows) — v2.3 if useful

## Acceptance criteria

- [ ] Empty state: "🎯 No stories yet."
- [ ] 5 columns render with headers BACKLOG / TODO / IN PROG / REVIEW / DONE
- [ ] Each header shows count: `BACKLOG (3)`, `TODO (2)`, etc.
- [ ] Stories with non-canonical status (typo) are silently skipped
- [ ] Output uses Unicode box-drawing (┌ ─ ┐ │ etc.)
- [ ] Doesn't crash when a column has 0 stories

## Dependencies / blockers

Depends on: Task 0, H (stories_root path helper)
Blocks: none

## Notes

Lowest priority (J) because /mb:tree already gives visibility. This is nice-to-have
for the visual-thinker morning ritual.
