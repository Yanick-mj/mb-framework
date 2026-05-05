---
story_id: STU-P2S2.4
title: Deliverable viewer in story modal
priority: high
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint2
---

# Deliverable viewer in story modal

## Why

Before approving, the builder needs to see what the agent produced. Deliverables live in `_bmad-output/deliverables/STU-{id}/` — the modal should display them.

## Scope

**In:**
- Tab or section in story modal: "Deliverables"
- List deliverable files (PLAN-rev1.md, IMPL-rev1.md, etc.)
- Click a deliverable → render markdown content inline
- Show latest revision by default, toggle to see older revisions
- Syntax highlighting for code blocks in deliverables

**Out:**
- Editing deliverables from the UI
- Diff view between revisions (nice-to-have, v2.3)
- File attachments or images

## Acceptance criteria

- [ ] "Deliverables" tab/section visible in story modal
- [ ] Lists all files from `_bmad-output/deliverables/STU-{id}/`
- [ ] Each file clickable → renders markdown content
- [ ] Code blocks have syntax highlighting (highlight.js or Prism)
- [ ] Latest revision shown by default (PLAN-rev2 > PLAN-rev1)
- [ ] Empty state: "No deliverables yet" when directory doesn't exist
- [ ] Long content scrollable within modal (no page scroll)

## Tech requirements

- **Endpoint:** `GET /api/stories/{id}/deliverables` → list of files
- **Endpoint:** `GET /api/stories/{id}/deliverables/{filename}` → rendered HTML
- **Markdown rendering:** server-side with `markdown` or `mistune` library
- **Syntax highlight:** Prism.js CDN (client-side, lightweight)
- **HTMX:** lazy-load deliverable content on tab click (`hx-get`, `hx-trigger="click"`)

## Designer requirements

- Tab bar in modal: "Details" | "Deliverables" (underline active tab)
- File list: icon per type (📋 PLAN, 🔨 IMPL, ✅ REVIEW, 📝 DOC)
- Active file: highlighted in list, content shown in right panel
- Scrollable content area with max-height (70vh)
- Code blocks: dark theme (matches Apple aesthetic)
- Revision toggle: small "v1 | v2 | v3" pills above content

## TDD

```python
# tests/dashboard/test_deliverable_view.py

def test_deliverables_endpoint_lists_files():
    """GET /api/stories/{id}/deliverables → list of filenames"""

def test_deliverable_content_rendered_as_html():
    """GET deliverable file → markdown converted to HTML"""

def test_no_deliverables_returns_empty_list():
    """Story with no _bmad-output dir → empty array"""

def test_deliverables_tab_visible_in_modal(page):
    """Playwright: story modal has 'Deliverables' tab"""

def test_click_deliverable_shows_content(page):
    """Playwright: click file → content appears"""
```
