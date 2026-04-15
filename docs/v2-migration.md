# mb-framework v1 → v2 Migration Guide

v2 introduces **stage-aware mode** without breaking v1. This guide tells you how to update (or deliberately not update) existing projects.

## TL;DR

- **Your v1 project still works unchanged.** If `mb-stage.yaml` is absent at project root, the orchestrator treats the project as `stage: scale` (strict v1 pipeline: DS UPDATE GATE, Atomic Design, TDD, RLS double-check all ON).
- **v2 only activates** when you add an `mb-stage.yaml` OR run `install.sh` on a new project and answer the interactive stage prompt.
- **New early-stage commands** (`/mb:validate`, `/mb:ship`, `/mb:stage`) are additive.

---

## 1. Do I need to migrate?

| Your situation | Action |
|---|---|
| v1 project in production, working fine (e.g. otoqi) | **Nothing.** v2 is a no-op for you. |
| v1 project you want to explicitly mark as mature | `echo "stage: scale" > mb-stage.yaml`. Documentation only; no runtime change. |
| New project, pre-code (idea stage) | Run `install.sh`, pick `discovery` at prompt. Use `/mb:validate`. |
| New project, prototyping a wedge | Run `install.sh`, pick `mvp`. Use `/mb:ship`. |
| v1 project that hit PMF, want to relax gates on experiments | Add `mb-stage.yaml` with `stage: pmf` and per-feature overrides (see §4). |

---

## 2. What v2 added (additive only)

### New files

- `mb-stage.yaml` (at YOUR project root, created by install.sh or manually)
- `mb-stage.yaml.template` (in the framework submodule)
- `agents-early/{stage-advisor,idea-validator,user-interviewer,wedge-builder}/SKILL.md`
- `commands/{stage,validate,ship}.md`
- `memory/stage-history.md` (transition log)
- `memory/wedge-log.md` (wedge tracking, written by wedge-builder)
- `docs/v2-prd.md`, `docs/v2-migration.md`

### Modified v1 files (additions only — **zero deletions**, verified)

All 13 v1 skills received an appended `## Stage Adaptation (v2)` section:

```
agents/architect/SKILL.md      +9 lines
agents/be-dev/SKILL.md        +13 lines
agents/devops/SKILL.md         +9 lines
agents/fe-dev/SKILL.md        +14 lines
agents/lead-dev/SKILL.md       +9 lines
agents/orchestrator/SKILL.md  +40 lines  (Step 0.5 + Stage Routing Table)
agents/pm/SKILL.md            +16 lines  (1-liner gate universal)
agents/quick-flow/SKILL.md     +9 lines
agents/sm/SKILL.md             +9 lines
agents/tea/SKILL.md           +17 lines  (Analytics Events Spec for pmf+)
agents/tech-writer/SKILL.md    +9 lines
agents/ux-designer/SKILL.md   +11 lines
agents/verifier/SKILL.md       +9 lines
────────────────────────────────────────
Total: +174 lines, -0 lines
```

Verify yourself:
```bash
cd .claude/mb && git diff master..v2 --numstat -- 'agents/*/SKILL.md'
```

### Modified `install.sh`

- New `--no-stage` flag (skips interactive prompt, useful for CI)
- New step: symlinks `agents-early/*` to `.claude/skills/mb-early-*`
- New step: interactive stage prompt (default `scale`)

Backward-compatible: existing projects that re-run `install.sh` get the new symlinks + keep working.

---

## 3. Step-by-step: upgrading an existing v1 project

### 3.1 Zero-action path (recommended for stable projects)

Do nothing. v2 is a no-op. You can keep pulling framework updates:

```bash
cd .claude/mb
git pull origin v2  # or stay on master
```

### 3.2 Opt-in path (for projects you want to tag)

```bash
# In your project root
echo "stage: scale" > mb-stage.yaml
echo "since: $(date -u +%Y-%m-%d)" >> mb-stage.yaml

# Commit as documentation
git add mb-stage.yaml
git commit -m "chore: mark project as mb-framework stage:scale"
```

Runtime behavior unchanged. Future `/mb:stage` invocations will now show current stage + criteria.

### 3.3 Full early-stage path (for new products / pivots inside an existing repo)

If you want to run an early-stage experiment INSIDE a mature repo (e.g. a wedge for a new feature), create a subdirectory with its own `mb-stage.yaml`:

```bash
mkdir experiments/my-wedge
cd experiments/my-wedge
cp ../../.claude/mb/mb-stage.yaml.template ./mb-stage.yaml
# edit: stage: mvp
```

**Caveat**: orchestrator reads `mb-stage.yaml` from project root by default. For nested stages, invoke `/mb:ship` from inside the subdirectory or pass stage explicitly.

---

## 4. Stage → gate activation matrix

| Gate | discovery | mvp | pmf | scale |
|---|---|---|---|---|
| TDD (be-dev/fe-dev rule 9) | OFF | OFF | ON | ON |
| Atomic Design (fe-dev rule 11) | OFF | OFF | ON | ON |
| Step 0 Component Audit (fe-dev rule 10) | OFF | OFF | ON | ON |
| DS UPDATE GATE (fe-dev rules 14-15) | OFF | OFF | ON | ON |
| RLS double-check (be-dev) | OFF | OFF | ON | ON |
| Sprint ceremony (sm) | OFF | OFF | ON | ON |
| 1-liner gate (pm rule 9, v2) | ON | ON | ON | ON |
| Analytics event spec (tea, v2) | OFF | OFF | ON | ON |

**Overrides** (in `mb-stage.yaml.overrides`): force any gate ON per-project even outside its nominal stage. Use sparingly.

---

## 5. Transition criteria (auto-suggested by stage-advisor)

| From | To | Criteria (default) |
|---|---|---|
| discovery | mvp | ≥3 user interviews, pain score ≥60/125, validated 1-liner |
| mvp | pmf | ≥1 paying user OR ≥10 active test users, wedge kill_date not hit |
| pmf | scale | ≥3 months MRR stable, ≥40% retention D30 |

Run `/mb:stage` to see your current progress. Run `/mb:stage upgrade` when criteria met (or `--force` to bypass, logged).

---

## 6. Rollback

v2 is safe to pull out of. If you installed it by accident:

```bash
# Remove stage file (reverts to v1 strict behavior)
rm mb-stage.yaml

# Remove early-stage symlinks (optional)
rm -f .claude/skills/mb-early-*
```

All v1 skill files are unchanged (additions only), so removing `mb-stage.yaml` fully reverts runtime to v1. The appended `## Stage Adaptation (v2)` sections remain in the skill files but become unreachable since Step 0.5 defaults `stage = "scale"` when yaml is absent, and scale uses the full v1 pipeline.

---

## 7. FAQ

**Q: Will v2 change how `/mb:feature` behaves on my existing project?**
No. Without `mb-stage.yaml`, orchestrator Step 0.5 sets `stage = "scale"` → v1 routing table applies unchanged.

**Q: Can I pin to v1 if I don't want v2 at all?**
Yes. `cd .claude/mb && git checkout master` (or tag `v1.x` once created).

**Q: Can I use v2 commands in a v1 project?**
Partially. `/mb:validate` and `/mb:ship` work standalone (they invoke early-stage skills directly). `/mb:stage` requires `mb-stage.yaml`.

**Q: Is wedge-builder safe in a production codebase?**
No. Wedge-builder explicitly skips TDD, Atomic Design, DS UPDATE GATE, RLS double-check. Use it only in `stage: mvp` projects or isolated experiments. Never run it against a pmf/scale repo without understanding the consequences.

**Q: What happens to wedge code at kill_date?**
Nothing automatic. `memory/wedge-log.md` tracks the date. When you run `/mb:stage upgrade mvp→pmf`, stage-advisor warns on any wedge past its kill_date and requires you to mark it as `upgraded-to-pmf` (rewrite with v1 gates) or `killed` (delete).

---

## 8. Verifying your install

```bash
# 1. Framework present
ls .claude/mb/agents-early/          # should list 4 skills
ls .claude/mb/commands/              # should include stage.md, validate.md, ship.md

# 2. Symlinks created
ls .claude/skills/ | grep mb-early-  # should list 4 mb-early-* links

# 3. Stage detection
cat mb-stage.yaml 2>/dev/null || echo "No stage file — v1 strict mode"
```

---

## 9. Known limitations (v2.0.0)

- Real E2E tests on Studio-IRIS (AC2) and a dummy wedge project (AC3) have NOT been executed — v2.0.0 ships with structural verification only. Run `/mb:validate` and `/mb:ship` on your first project and open issues if the flow breaks.
- `stage-advisor` upgrade criteria are markdown-documented but not auto-measured. You must manually confirm user counts / MRR / retention before running `/mb:stage upgrade`.
- No web UI. Stage management is yaml + git.

See `docs/v2-prd.md` §13 for the v3 roadmap.
