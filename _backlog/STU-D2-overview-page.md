---
story_id: STU-D2
title: Overview page — stage, stats, criteria, runs
priority: critical
status: todo
created: 2026-05-04
assignee: fe-dev
parent_story: STU-D1
---

# Overview page — stage, stats, criteria, runs

## Why

The overview is the landing page — the "standup in 30 seconds" view. A PM opens the dashboard and immediately sees project health: stage, velocity, blockers, and what the AI agents did recently.

## Scope

**In:**
- `templates/overview.html` — extends base, shows stage badge, stats grid, progress bar, criteria list, runs table
- `templates/partials/stage_badge.html` — stage pill component (discovery/mvp/pmf/scale with colors)
- `templates/partials/stats_grid.html` — 4 stat cards (total, in_progress, blocked, done_this_week)
- `templates/partials/runs_table.html` — last 5 agent runs from runs.jsonl
- `server.py` route: `GET /projects/{name}/overview` renders with data
- `parsers.py` functions:
  - `get_stage_data(path)` — reads mb-stage.yaml
  - `get_story_stats(path)` — counts stories by status
  - `get_recent_runs(path, limit=5)` — reads runs.jsonl via existing `runs.load_recent()`
  - `get_upgrade_criteria(path)` — extracts criteria + progress percentage

**Out:**
- HTMX polling (STU-D7)
- Multi-project switching (STU-D7)

## Acceptance criteria

- [ ] Stage badge shows correct stage with color coding (discovery=purple, mvp=orange, pmf=blue, scale=green)
- [ ] Stats grid shows 4 cards with correct counts from actual story files
- [ ] Progress bar shows upgrade criteria completion percentage
- [ ] Criteria list shows each criterion with done/pending icon and current value
- [ ] Runs table shows last 5 entries from runs.jsonl with agent, story, action, summary
- [ ] Graceful fallback if mb-stage.yaml missing (assume scale, show "no stage file")
- [ ] Graceful fallback if runs.jsonl missing (show "no runs yet")

## Technical notes

- Reuses `scripts.v2_2.board._group_by_status()` for story counts
- Reuses `scripts.v2_1.runs.load_recent()` for runs
- `mb-stage.yaml` is at project root (not in .claude/mb/)
- Stage colors match prototype CSS variables

## Testing

- Test with a project that has mb-stage.yaml + stories + runs.jsonl (full view)
- Test with empty project (all fallbacks)
- Verify counts match `/mb:board` output
