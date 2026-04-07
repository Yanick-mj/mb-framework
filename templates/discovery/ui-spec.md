# UI Spec: {Feature Name}

> Template — fill in during UX Designer Discovery phase

## User Flow

### Happy Path
1. User is on {screen} → sees {state}
2. User taps {element} → {action}
3. System responds with {result}
4. User sees {final state}

### Error Paths
| Error | Trigger | Display | Recovery |
|-------|---------|---------|----------|
| | | | |

### Edge Cases
| Case | Behavior |
|------|----------|
| Empty state | |
| Slow network | |
| Offline | |

## Screens

### Screen: {Name}
- **Wireframe**: `wireframes/{feature}/{screen}.excalidraw`
- **Entry point**: {from where}
- **Exit points**: {to where}

#### States
| State | Trigger | Display |
|-------|---------|---------|
| Default | | |
| Loading | | Skeleton |
| Error | | Message + retry |
| Empty | | Illustration + CTA |

## Component Inventory
| Component | Exists? | Location | Action |
|-----------|---------|----------|--------|
| | Yes/No | {path} | Reuse/Create/Modify |

## Accessibility
- [ ] Touch targets >= 44x44pt
- [ ] Color contrast >= 4.5:1
- [ ] Screen reader labels
- [ ] Keyboard navigation (web)
- [ ] Error announcements

## Story Enrichment
UX-specific acceptance criteria to add to stories:
- [ ] {AC}
