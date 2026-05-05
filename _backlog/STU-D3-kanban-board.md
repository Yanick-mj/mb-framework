---
story_id: STU-D3
title: Kanban board page
priority: critical
status: todo
created: 2026-05-04
assignee: fe-dev
parent_story: STU-D1
---

# Kanban board page

## Why

The board is the most-used view for PMs tracking sprint progress. It replaces the ASCII `/mb:board` with a visual kanban that non-developers can read instantly.

## Scope

**In:**
- `templates/board.html` — 5-column grid layout (backlog, todo, in_progress, in_review, done)
- Story cards with: id, title, priority indicator (colored dot), label tags
- Cards are clickable (link to story modal — STU-D6)
- `templates/partials/board_columns.html` — partial for HTMX polling
- `server.py` route: `GET /projects/{name}/board`
- `parsers.py`: `get_board_data(path)` — wraps `board._group_by_status()` with full frontmatter

**Out:**
- Drag-and-drop (Phase 2 — write capability)
- Story modal content (STU-D6)

## Acceptance criteria

- [ ] 5 columns render with correct headers and story counts
- [ ] Stories appear in correct columns based on frontmatter `status`
- [ ] Priority shown as colored dot (critical=red, high=orange, medium=blue, low=gray)
- [ ] Labels from frontmatter shown as tags on cards
- [ ] Cards have `onclick` or `hx-get` to trigger story modal
- [ ] Empty columns show no placeholder (clean empty state)
- [ ] Column header dot colors match status semantics

## Technical notes

- Reuses `scripts.v2_2.board._group_by_status()` — but needs full frontmatter, not just story_id
- Enhance `_group_by_status()` return or re-parse in `parsers.py` to include title, priority, labels
- Story files can be in `_bmad-output/.../stories/` OR `_backlog/` — parse both
- Labels field in frontmatter is optional (may not exist on all stories)

## Testing

- Test with project that has stories in multiple statuses
- Test with project that has 0 stories (empty board message)
- Verify column order matches `/mb:board` order
