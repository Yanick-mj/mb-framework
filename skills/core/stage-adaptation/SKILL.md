---
name: core/stage-adaptation
description: Per-stage gate behavior — which disciplines are active at discovery/mvp/pmf/scale
version: 1
used_by: [fe-dev, be-dev, lead-dev, architect, pm, sm, verifier, tea, devops, quick-flow, tech-writer, ux-designer, orchestrator]
---

## Stages

mb projects pass through 4 stages. Each stage relaxes or enforces a
different set of engineering disciplines. The current stage lives in
`mb-stage.yaml` at the project root.

| Stage | Behavior |
|-------|----------|
| **discovery** | Engineering OFF. Ideas, research, user interviews. `wedge-builder` handles any throwaway UI. |
| **mvp** | Janky shipping allowed. TDD / Atomic Design / DS gates relaxed. Inline styles OK, single-file components OK. Goal: deploy in < 4h. |
| **pmf** | Full v1. Component Audit + Atomic Design + TDD. DS UPDATE GATE light. |
| **scale** | Full v1 strict. Step 0 mandatory + Atomic Design + TDD + DS UPDATE GATE strict + architecture review for new subsystems. |

## Overrides

Per-project override via `mb-stage.yaml.overrides`:

```yaml
stage: mvp
overrides:
  force_ds_gate: true          # DS UPDATE GATE active even at mvp
  force_atomic_design: true    # Atomic Design active even at mvp
  force_tdd: true              # TDD active even at mvp
```

Overrides always tighten; you cannot loosen a stage below its defaults.

## How agents read the stage

```python
# at runtime, any agent decides gate behavior like this:
from scripts.v2_1 import stage as stage_mod
stage = stage_mod.current()              # "mvp" | "pmf" | "scale" | "discovery"
gates = stage_mod.gates_for(stage)       # dict of active gates

if gates["tdd"]:
    # write failing test first
    ...
```

## Rule: agents MUST announce stage at invocation

Every agent starts its response with:

```
Stage: mvp (from mb-stage.yaml)
Active gates: evidence-rules, run-summary
Relaxed: tdd, atomic-design, ds-gate
```

This makes stage-dependent behavior auditable by the user.
