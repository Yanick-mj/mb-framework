# Discovery Templates

These templates define the livrables for the Discovery phase (before sprint).

## Livrable per Agent

| Agent | Template | Output Location |
|-------|----------|----------------|
| PM | `brief.md` | `_discovery/{feature}/brief.md` |
| UX Designer | `ui-spec.md` | `_discovery/{feature}/ui-spec.md` + `wireframes/` |
| Architect | `architecture.md` | `_discovery/{feature}/architecture.md` |
| SM | Uses `templates/validation/story.md` | `_discovery/{feature}/stories/` |

## Convention

Discovery livrables live in the PROJECT (not in mb-framework):

```
{project}/
└── _discovery/
    └── {feature-name}/
        ├── brief.md              # PM output
        ├── architecture.md       # Architect output
        ├── ui-spec.md            # UX Designer output
        ├── wireframes/           # Excalidraw files
        │   ├── flow-overview.excalidraw
        │   └── screen-*.excalidraw
        └── stories/              # SM output
            └── story-*.md
```

Each agent reads the previous agent's livrable and writes its own.
The orchestrator ensures livrables are created in the right order.
