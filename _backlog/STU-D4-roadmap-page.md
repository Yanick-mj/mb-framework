---
story_id: STU-D4
title: Roadmap page — mission + milestones
priority: high
status: todo
created: 2026-05-04
assignee: fe-dev
parent_story: STU-D1
---

# Roadmap page — mission + milestones

## Why

The roadmap gives strategic context — why the team is building what they're building. PMs and stakeholders need to see the mission, current milestone, and what's next without reading raw markdown.

## Scope

**In:**
- `templates/roadmap.html` — mission card + milestone cards with tracks tables
- `server.py` route: `GET /projects/{name}/roadmap`
- `parsers.py`: `get_roadmap_data(path)` — parses `_roadmap.md` into structured data
  - Extracts: mission (text under ## Mission), current stage
  - Extracts phases/milestones: title, goal, tracks table, exit criteria
  - First phase = "current", second = "next" (or use markdown indicators)

**Out:**
- Editing roadmap from dashboard (Phase 2)

## Acceptance criteria

- [ ] Mission card shows mission text with left accent border
- [ ] Current milestone card has blue ring highlight
- [ ] Next milestone card is dimmed (opacity)
- [ ] Tracks tables render with Track / Work / Owner columns
- [ ] Connector line between current and next milestone
- [ ] Graceful fallback if `_roadmap.md` is missing or empty

## Technical notes

- `_roadmap.md` follows `templates/roadmap.md` structure but users may customize
- Parser strategy: split by `###` headers, detect "Phase N" pattern
- Tables parsed via simple regex (| delimited rows)
- If roadmap doesn't follow template exactly, show raw markdown as fallback (rendered via `markdown` library)

## Testing

- Test with a roadmap that follows the template exactly
- Test with a minimal roadmap (just mission, no phases)
- Test with missing `_roadmap.md`
