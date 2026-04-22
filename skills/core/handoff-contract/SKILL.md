---
name: core/handoff-contract
description: Every agent must produce the artifact the next agent requires — no partial deliveries
version: 1
used_by: [fe-dev, be-dev, lead-dev, architect, pm, sm, verifier, tea, devops, quick-flow, tech-writer, ux-designer, orchestrator]
---

## Rule

Every agent in a pipeline produces **one concrete artifact** that the next
agent can consume. If the artifact is not produced, the pipeline stops
there — no implicit "the next agent will figure it out."

This is enforced by orchestrator Step 3.6 (verifier's handoff gate).

## Artifact requirements per agent

| Agent | Required artifact |
|-------|-------------------|
| pm | `_bmad-output/implementation-artifacts/stories/STU-XXX.md` with complete Acceptance Criteria |
| architect | ADR or tech notes in the story's `## Technical notes` section |
| ux-designer | Wireframe or UI spec referenced in the story |
| sm | Story with `status: todo` + `assignee:` set |
| fe-dev / be-dev | Code change + passing tests + `## Evidence` block citing files |
| tea | Test file(s) passing in CI |
| verifier | PASS or FAIL with concrete reasons |
| tech-writer | Docs change with `## Evidence` |
| devops | Deploy script or CI config with verification step |
| orchestrator | Updated `memory/_session/handoff.md` describing next agent |

## Handoff block

At the end of a `## Run Summary`, the agent writes:

```markdown
Next agent should: <concrete instruction>
Artifact produced: <path to file or PR URL>
Blockers: <list anything that stops the next agent>
```

## Verifier's handoff gate

Before marking a story done, verifier checks:

1. The required artifact for the last agent exists.
2. The artifact matches the story's Acceptance Criteria.
3. No blocker from the run summary is unresolved.

If any fails → verifier returns FAIL with the missing item.

## Why this matters

Without a handoff contract, agents emit plausible-sounding summaries but
leave no concrete trail. The next agent has to reverse-engineer what was
done. This is where multi-agent pipelines silently degrade — each agent
shaves 20% off the expected deliverable, and by the end of the pipeline
the story is 60% done but reported 100%.

Binary: artifact produced, or pipeline stops.
