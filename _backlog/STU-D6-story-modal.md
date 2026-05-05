---
story_id: STU-D6
title: Story detail modal
priority: high
status: todo
created: 2026-05-04
assignee: fe-dev
parent_story: STU-D3
---

# Story detail modal

## Why

Clicking a card on the board or inbox needs to show the full story content — why, scope, acceptance criteria — without leaving the page. This is the bridge between "I see a card" and "I understand the work".

## Scope

**In:**
- `templates/partials/story_modal.html` — modal overlay with sheet content
- HTMX-powered: `hx-get="/partials/{name}/story/{story_id}"` triggered by card click
- `server.py` route: `GET /partials/{name}/story/{story_id}` returns modal HTML fragment
- `parsers.py`: `get_story_detail(path, story_id)` — reads story .md file, parses frontmatter + body
- Modal shows: id, title, priority, status, created date, why, scope, acceptance criteria (with checkboxes)
- Close via: click overlay, X button, Escape key
- Apple-style frosted glass backdrop (backdrop-filter: blur)

**Out:**
- Editing story from modal (Phase 2)
- Markdown rendering of full body (MVP uses structured extraction; full markdown in Phase 2)

## Acceptance criteria

- [ ] Click card on board → modal appears with story content
- [ ] Click card on inbox → same modal
- [ ] Modal shows frontmatter fields (priority, status, created)
- [ ] Modal shows Why, Scope, Acceptance criteria sections
- [ ] Acceptance criteria checkboxes reflect `- [x]` vs `- [ ]` in markdown
- [ ] Close with overlay click, X button, and Escape key
- [ ] Smooth open animation (scale + fade)

## Technical notes

- Story files have consistent structure: frontmatter + ## Why + ## Scope + ## Acceptance criteria
- Parse body by splitting on `## ` headers
- Checkbox regex: `- \[x\]` = done, `- \[ \]` = todo
- HTMX: card has `hx-get` + `hx-target="#modal-container"` + `hx-swap="innerHTML"`
- Modal container is a fixed div in base.html, always present

## Testing

- Click multiple different stories — modal updates correctly each time
- Story with all sections filled
- Story with missing sections (graceful, show what's available)
- Escape key and overlay click both close
