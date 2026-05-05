---
story_id: STU-P2S2.1
title: Kanban drag-and-drop between columns
priority: critical
status: in_review
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint2
---

# Kanban drag-and-drop between columns

## Why

Changing a story's status requires editing a markdown file. The builder needs to drag a card from "in_review" to "done" in one gesture.

## Scope

**In:**
- Sortable.js integration on kanban columns
- Drag a card → drop in another column → PATCH status
- Visual feedback: ghost card while dragging, drop zone highlight
- Fallback: mobile touch support via Sortable.js touch module
- Reorder within column (optional sort)

**Out:**
- Multi-select drag (Sprint 6)
- Custom column order or column creation
- Animations beyond basic drag feedback

## Acceptance criteria

- [ ] Cards are draggable between all 5 columns
- [ ] Dropping a card in a new column calls PATCH /api/stories/{id}/status
- [ ] Status in the .md file is updated after drop
- [ ] Visual ghost shows card being dragged
- [ ] Drop zone highlights on hover (subtle border/background)
- [ ] If PATCH fails, card snaps back to original column
- [ ] Works on desktop (mouse) and tablet (touch)
- [ ] Column story count updates after move

## Tech requirements

- **Sortable.js:** CDN include (~10kb), no npm needed
- **HTMX integration:** `hx-trigger="sortable:end"` or vanilla JS event → fetch PATCH
- **Endpoint:** `PATCH /api/stories/{id}/status` body: `{"status": "done"}`
- **Optimistic UI:** move card immediately, revert on error
- **Event:** trigger `storiesChanged` for other components listening

## Designer requirements

- Ghost card: 80% opacity, slight rotation (2deg), elevated shadow
- Drop zone: column background shifts to light blue/purple on dragover
- Transition: card animates into place (200ms ease-out)
- Cursor: grab on hover, grabbing while dragging
- Disabled state: "done" cards slightly dimmed, still draggable (to reopen)
- Card spacing: 8px gap between cards in column

## TDD

```python
# tests/dashboard/test_drag_drop.py (Playwright)

def test_card_is_draggable():
    """Card element has draggable behavior (cursor: grab)"""

def test_drag_card_to_new_column_updates_status():
    """Drag from 'todo' to 'in_progress' → file status changes"""

def test_failed_patch_reverts_card_position():
    """Mock 500 on PATCH → card returns to original column"""

def test_column_count_updates_after_move():
    """Move card → source column count -1, target +1"""

def test_touch_drag_works():
    """Simulate touch events → same behavior as mouse drag"""
```
