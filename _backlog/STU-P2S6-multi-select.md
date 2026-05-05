---
story_id: STU-P2S6.1
title: Multi-select on kanban
priority: critical
status: todo
created: 2026-05-05
assignee: fe-dev
sprint: phase2-sprint6
---

# Multi-select on kanban

## Why

The builder often needs to act on multiple tickets at once (validate a batch, launch several, archive old ones). Multi-select enables this.

## Scope

**In:**
- Checkbox on each kanban card (visible on hover or selection mode)
- Shift+click for range selection
- Selection counter: "3 selected" in a floating action bar
- Clear selection button
- Selection persists across columns

**Out:**
- Drag-drop multiple cards at once (too complex, use action bar)
- Selection across pages

## Acceptance criteria

- [ ] Checkbox appears on card hover (or always in selection mode)
- [ ] Click checkbox selects card (blue highlight)
- [ ] Shift+click selects range within column
- [ ] Floating action bar appears when ≥1 card selected
- [ ] Action bar shows count: "3 stories selected"
- [ ] "Clear" button deselects all
- [ ] Selection works across multiple columns

## Tech requirements

- **State:** JS Set() tracking selected story IDs
- **UI:** checkbox as absolute-positioned element on card
- **Action bar:** fixed-position bottom bar, shown/hidden based on selection count
- **HTMX compatibility:** selection state lives in JS (not server), actions POST to API
- **Shift+click:** track lastClicked index per column for range select

## Designer requirements

- Checkbox: small (16px), top-left of card, subtle border
- Selected card: light blue background + left blue border
- Action bar: full-width bottom bar, dark background, white text
- Action bar content: count + action buttons (right-aligned)
- Animation: bar slides up on first selection, slides down on clear
- Clear button: "×" icon + "Clear" text

## TDD

```python
# tests/dashboard/test_multi_select.py (Playwright)

def test_checkbox_visible_on_hover(page):
    """Hover card → checkbox appears"""

def test_click_checkbox_selects(page):
    """Click checkbox → card highlighted, count shows '1 selected'"""

def test_shift_click_range(page):
    """Click card 1 + shift+click card 3 → cards 1,2,3 selected"""

def test_action_bar_shows_on_selection(page):
    """Select 1 card → action bar slides up"""

def test_clear_deselects_all(page):
    """Click Clear → all deselected, action bar hidden"""
```
