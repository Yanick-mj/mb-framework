---
name: 'ship'
description: 'Ship a janky wedge product in < 48h (mb-framework v2, mvp stage) — opposes v1 engineering gates by design'
allowed-tools: ['Read', 'Edit', 'Write', 'Bash', 'WebFetch', 'Agent']
---

# /mb:ship

Ship a **janky, deployable wedge** in under 48h. Deliberately skips v1 engineering discipline (no TDD, no Atomic Design, no DS UPDATE GATE, no Component Audit). This is assumed-throwaway code with a mandatory `kill_date`.

Designed for `stage: mvp`. Warns if used outside mvp.

## Usage

```
/mb:ship <wedge-name>              → ship with wedge plan from _discovery/<slug>/interview-synthesis.md
/mb:ship                           → prompt for wedge plan
```

## Input

- `wedge_plan` (required): `{ problem, solution, persona, channel }` — typically from user-interviewer output
- `deadline_hours` (optional, default 48): target TTFV
- `stack_preference` (optional): `vercel` | `no-code` | `sheets-zapier`

## Process

### Step 1 — Stage check

1. Invoke `mb-early-stage-advisor` with `action: "detect"`
2. If stage ≠ `mvp` → warn ("wedge-builder skips v1 gates — are you sure you want this in stage:<X>?"), allow override

### Step 2 — Delegate to wedge-builder

Invoke `mb-early-wedge-builder` with the wedge plan.

The skill will:
1. Validate wedge plan (problem / solution / persona / channel)
2. Compute `kill_date` (today + 30 days default)
3. Write entry to `memory/wedge-log.md`
4. Pick janky stack (default: Vercel + Next.js single page + Resend)
5. **Skip ALL v1 gates** (no TDD, no Component Audit, no DS gate, no Atomic, no RLS double-check)
6. Build single-file code (inline styles OK, hardcoded copy OK)
7. Deploy via `devops` skill (mvp/discovery mode)
8. Identify 5 test users from `wedge_plan.channel` + send cold emails
9. Run SINGLE verifier gate: "real user tested in < 48h"

### Step 3 — Handoff

- `status: success` + deployed_url → log to `memory/wedge-log.md`, schedule 48h verifier check
- `status: blocked` → display blocker (missing wedge plan, deploy failure, etc.)
- After 48h with 0 users → mark wedge `blocked-no-users` → suggest kill or pivot

## Output

```markdown
## Wedge Shipped

- **URL**: https://<slug>.vercel.app
- **Stack**: <stack>
- **TTFV**: <hours>h
- **Kill date**: <YYYY-MM-DD>
- **Test users invited**: N (see memory/wedge-log.md)
- **Files**: <list>
- **Next gate**: 48h → verify ≥ 1 real user interaction
```

## Opposition to v1 (by design)

This command deliberately opposes:
- ❌ TDD (be-dev rule 9, fe-dev rule 9)
- ❌ Atomic Design (fe-dev rule 11)
- ❌ Step 0 Component Audit (fe-dev rule 10)
- ❌ DS UPDATE GATE (fe-dev rules 14-15)
- ❌ RLS double-check (be-dev rule)
- ❌ Sprint ceremony (sm skill)

If you need any of these → upgrade stage (`/mb:stage upgrade`) or use `/mb:feature` instead.

$ARGUMENTS
