---
name: 'validate'
description: 'Validate a startup idea with YC-style 10Q framework + anti-tarpit + 1-liner gate (mb-framework v2, discovery stage)'
allowed-tools: ['Read', 'Write', 'WebFetch', 'Glob', 'Grep', 'Agent']
---

# /mb:validate

Validate a startup idea **before** writing any code. Forces founder to produce a valid 1-liner, score the idea on 10 dimensions, and run the anti-tarpit checklist.

Designed for `stage: discovery`. Warns but allows in other stages (useful for pivot exploration).

## Usage

```
/mb:validate <idea>                → full validation flow
/mb:validate                       → prompt for idea + founder_context
```

## Input

- `idea` (required): 1-liner or rough pitch
- `founder_context` (optional): background, relevant experience
- `target_market` (optional): who's the user
- `existing_alternatives` (optional): competitors you know of

## Process

### Step 1 — Stage check

1. Invoke `mb-early-stage-advisor` with `action: "detect"`
2. If stage ≠ `discovery` → warn, allow override

### Step 2 — Delegate to idea-validator

Invoke `mb-early-idea-validator` with the input context.

The skill will:
1. Enforce 1-liner gate (≤ 10 words, no jargon, grandmother test)
2. Run 10-Question YC framework (score /30)
3. Run anti-tarpit checklist (CISP, tarpit, perfect idea stall, first idea reflex)
4. WebFetch market research (failed startups, alternatives, enabling change)
5. Write report to `_discovery/{idea-slug}/go-no-go-report.md`

### Step 3 — Handoff

- `verdict: go` → suggest `/mb:stage upgrade` (when MVP criteria met) + next step
- `verdict: validate-with-interviews` → suggest invoking `mb-early-user-interviewer` with ≥ 3 transcripts
- `verdict: no-go` → display suggested pivots

## Output

```markdown
## Validation Result

- **Idea 1-liner**: "<validated 1-liner>"
- **Verdict**: go | no-go | validate-with-interviews
- **Score**: X/30
- **Anti-tarpit**: pass | fail (<dimension>)
- **Report**: _discovery/<slug>/go-no-go-report.md

## Next Action
<concrete suggestion>
```

$ARGUMENTS
