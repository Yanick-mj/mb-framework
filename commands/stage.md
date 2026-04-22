---
description: View, evaluate, upgrade, or downgrade the project stage (mb-framework v2)
allowed-tools: ['Read', 'Edit', 'Write', 'Bash', 'Agent']
---

# /mb:stage

Manage the project's stage in mb-framework v2 (stage-aware mode).

## Usage

```
/mb:stage                    → show current stage + transition criteria status
/mb:stage upgrade            → attempt upgrade to target_next (validates criteria)
/mb:stage upgrade --force    → upgrade even if criteria not met (use with caution)
/mb:stage downgrade <stage>  → explicit downgrade with confirmation
/mb:stage init               → create mb-stage.yaml interactively (if absent)
```

## Behavior

### Default invocation (no args)

1. Invoke `mb-early-stage-advisor` with `action: "detect"` then `action: "evaluate"`
2. Display:
   - Current stage + since date + days in stage
   - Target next stage
   - Criteria met (✅)
   - Criteria missing (⏳) with concrete next actions
   - Active overrides

### `upgrade`

1. Invoke `stage-advisor` with `action: "upgrade"`
2. If criteria not met → display blockers, refuse
3. If criteria met → update `mb-stage.yaml`, log to `memory/stage-history.md`, confirm
4. Display new stage + which v1 gates are now active

### `upgrade --force`

1. Confirm user intent ("are you sure? this will activate gates X, Y, Z without meeting criteria")
2. If confirmed → proceed and log "forced: true" in history

### `downgrade <stage>`

1. Refuse if no target_stage provided
2. Confirm user intent
3. Update yaml + log to history with reason

### `init`

1. If `mb-stage.yaml` exists → refuse, suggest `/mb:stage` to view it
2. Else → interactive prompt (same as install.sh stage setup)
3. Create `mb-stage.yaml` from template

## Output format

```
## Current Stage
- stage: <stage>
- since: <date> (<days> days)
- target_next: <stage>

## Criteria Status (<current> → <target>)
✅ <criterion_1>: <value> (target: <target>)
⏳ <criterion_2>: <value> (target: <target>) — Action: <suggestion>
...

## Active Overrides
- force_ds_gate: <bool>
- force_tdd: <bool>
...

## Next Actions
- <action 1>
- <action 2>
```

$ARGUMENTS
