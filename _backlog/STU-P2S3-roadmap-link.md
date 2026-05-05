---
story_id: STU-P2S3.4
title: Roadmap ↔ Sprint bidirectional links
priority: medium
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint3
---

# Roadmap ↔ Sprint bidirectional links

## Why

The builder thinks in roadmap phases ("Phase 2 progress?"). Sprints are execution slices within phases. The link lets them navigate: roadmap → phase → sprints → stories.

## Scope

**In:**
- Sprint YAML gets `phase` field linking to roadmap phase
- Roadmap page: each phase card shows associated sprints + aggregate %
- Click phase → shows sprint list filtered by that phase
- Sprints page: each sprint card shows phase tag

**Out:**
- Editing roadmap phases from the UI (roadmap stays in _roadmap.md)
- Auto-assigning sprints to phases

## Acceptance criteria

- [ ] Sprint YAML `phase` field parsed and displayed
- [ ] Roadmap phase card shows: "3 sprints, 67% complete"
- [ ] Click phase on roadmap → navigates to sprints filtered by phase
- [ ] Sprint card shows phase tag (e.g., "Phase 2" pill)
- [ ] Phase with no sprints shows "No sprints yet"

## Tech requirements

- **Parser update:** `get_roadmap_data()` enriched with sprint aggregation
- **Filter route:** `GET /projects/{name}/sprints?phase=Phase+2`
- **Aggregation:** per-phase % = avg of sprint completions in that phase

## Designer requirements

- Phase card: add subtle "3 sprints • 67%" line below existing content
- Phase pill on sprint card: small colored tag matching roadmap colors
- Filtered view: same layout as sprints page with "Phase 2" breadcrumb

## TDD

```python
# tests/dashboard/test_roadmap_sprint_link.py

def test_roadmap_shows_sprint_count_per_phase():
    """Phase with 2 sprints → '2 sprints' displayed"""

def test_roadmap_shows_phase_completion():
    """Phase sprints at 50% and 100% → phase shows 75%"""

def test_sprint_filter_by_phase():
    """GET /sprints?phase=Phase+2 → only Phase 2 sprints"""

def test_sprint_card_shows_phase_tag():
    """Sprint linked to Phase 2 → phase tag visible"""
```
