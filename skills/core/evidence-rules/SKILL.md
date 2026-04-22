---
name: core/evidence-rules
description: All claims must cite file paths with line numbers or be marked UNKNOWN
version: 1
used_by: [fe-dev, be-dev, lead-dev, architect, pm, sm, verifier, tea, devops, quick-flow, tech-writer, ux-designer, orchestrator]
---

## Rules

<rules CRITICAL="TRUE">
1. NEVER state facts without EVIDENCE (file paths + excerpts with line numbers)
2. If evidence missing → write UNKNOWN + clarifying question
3. Max 2 ASSUMPTIONs per response, clearly labeled
4. FORBIDDEN: inventing file names, function signatures, metrics, APIs
5. End responses with: ## Evidence / ## Unknowns / ## Assumptions
</rules>

## Why this skill exists

Without evidence discipline, agents hallucinate: plausible-but-wrong file
paths, imagined function signatures, fabricated metrics. Every invented
claim compounds into broken downstream work.

The rule is binary: a claim has a grep-able source, or it's marked UNKNOWN.
No middle ground.

## How to apply

**Before making any factual statement**, verify it in the code:

```bash
# ✅ GOOD — grep first, quote file:line
rg "processPayment" packages/api/ -l
# → packages/api/src/payments/service.ts:142
```

Then cite:

> processPayment is defined at packages/api/src/payments/service.ts:142.

**When evidence is missing**:

> UNKNOWN: I haven't verified whether the payment service uses Stripe or
> a custom gateway. Can you confirm which integration is primary?

**When you must assume** (max 2 per response):

> ASSUMPTION 1: I'm treating `user_id` as a UUID based on the schema pattern;
> if it's a bigint, the RLS policy needs a type cast.

## Required response footer

Every agent response ends with:

```markdown
## Evidence
- file.ts:42 — excerpt demonstrating claim
- file.ts:99 — excerpt demonstrating claim

## Unknowns
- Thing I didn't verify

## Assumptions
- Thing I treated as true without verifying
```
