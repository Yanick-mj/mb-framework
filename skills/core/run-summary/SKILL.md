---
name: core/run-summary
description: Mandatory output format — every agent ends with a structured Run Summary block and appends to memory/runs.jsonl
version: 1
used_by: [fe-dev, be-dev, lead-dev, architect, pm, sm, verifier, tea, devops, quick-flow, tech-writer, ux-designer, orchestrator]
---

## Rule

At the end of every agent invocation, do TWO things:

1. Write a `## Run Summary` markdown block to the chat response AND append
   it to `memory/_session/handoff.md` (so the next agent sees it).
2. Append a structured JSONL entry to `memory/runs.jsonl` via the helper.

## Structured append (mandatory)

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -c "
from scripts.v2_1 import runs
runs.append(
    agent='AGENT_NAME',
    story='STORY_ID',
    action='short-verb-phrase',
    tokens_in=N,
    tokens_out=N,
    summary='One sentence describing what was done.',
)
"
```

This enables `/mb:runs` to reconstruct cost/handoff history.

## Markdown block template

```markdown
## Run Summary — AGENT_NAME on STORY_ID

Done. Here is what I did:
- action 1
- action 2
- action 3

Next agent should: <concrete instruction for the next step>
Unknowns: <list things you didn't verify>
```

## Example

```markdown
## Run Summary — fe-dev on STU-042

Done. Here is what I did:
- Added `<ProfitCalculator>` molecule at packages/ui/src/molecules/profit-calculator.tsx
- Wired it into the driver bidding flow at apps/mobile/src/screens/bid.tsx:87
- Updated i18n keys in packages/i18n/src/en/bidding.json

Next agent should: verifier runs `turbo test --filter=mobile` to confirm
the 3 new unit tests pass in CI.
Unknowns: whether the profitability formula for long-haul trips needs
adjustment for fuel-cost variants (out of scope for this story).
```

## Why this matters

Without run summaries the orchestrator has no way to:
- Resume after a failure
- Hand off context to the next agent
- Compute cost per story (`/mb:runs`)
- Detect agent drift from assigned story

A missing run summary is a hard failure in verifier's pipeline.
