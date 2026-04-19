# Paperclip test #1 — Studio IRIS (live observation)

**Date** : 2026-04-19
**URL observée** : http://127.0.0.1:3100/STU/*
**Durée test** : ~10 min
**Outil d'observation** : Playwright MCP (browser snapshots + screenshots)
**Context** : Studio IRIS = agence dev test-bed, 1 CEO agent créé, 1er task = "hire engineer + hiring plan"

---

## 1. Ce qu'on a observé en live

### 1.1 CEO agent a exécuté l'onboarding task en < 3 min

Chronologie reconstruite depuis l'Activity log + le Chat du task STU-1 :

```
T+0    Board: create company "Studio Iris" + goal (9m ago)
T+3m   Board: create CEO agent (6m ago)
T+6m   Board: create project Onboarding + STU-1 task (3m ago)
T+6m   Board: launch (CEO wake scheduled)
T+9m   CEO wake #1:
         - ran 1 command (fetch issue context + existing agents)
         - ran 2 commands (parse Studio IRIS description, list sub-tasks)
         - called 1 tool (paperclip-create-agent skill)
         - ran 5 commands (gather config docs for hire requests)
         - ran 1 command (submit LEAD-DEV hire → approval pending)
         - ran 1 command (submit CONTENT hire → approval pending)
T+10m  CEO idle, 2 approvals waiting in Inbox
```

**Token consumption** : 448.2k tokens (via Costs page). Sur Claude Max = "$0" mais = chunk non-trivial de rate limit.

### 1.2 Features observées en fonctionnement

| Feature | Confirmée par | État |
|---|---|---|
| Heartbeat execution | Status `Running` / `Idle` sur STU-1 | ✅ |
| Runtime skill discovery | CEO a utilisé `paperclip-create-agent` sans config préalable | ✅ |
| Approval gates | 2 hire requests pending en Inbox avec Approve/Reject | ✅ |
| Org chart auto | `/org` montre CEO → {LEAD-DEV, CONTENT} après 1 heartbeat | ✅ |
| Audit log | Activity page = timeline granulaire avec actor + target | ✅ |
| Company portability | "Import company" + "Export company" buttons dans Org | ✅ (pas testé run) |
| Token counter | Costs page = 448.2k tokens visibles | ✅ |
| Multi-agent sidebar | CEO, CONTENT, LEAD-DEV listés | ✅ (mais CONTENT/LEAD-DEV en "pending") |

### 1.3 Bugs / limitations observés

| # | Problème | Sévérité | Détail |
|---|---|---|---|
| L1 | CEO répond en anglais malgré description française | Moyen | Le system prompt par défaut override la langue du task. Fix : ajouter "Always respond in the user's language" au system prompt agent |
| L2 | Cost enforcement inopérant avec Claude Code local | Critique pour Claude Pro/Max users | $0.00 affiché, pas de hard stop possible. Rate limit réel invisible. |
| L3 | Agents `pending` visibles en sidebar comme actifs | Faible | Pas de badge "pending" — UX peut induire en erreur |
| L4 | Budget `Open / no cap` même si on a demandé à l'install | Faible | Le wizard ne configure pas le budget — doit être défini post-launch |
| L5 | Actor = "Board" pour toutes les actions CEO | Question ouverte | C'est voulu (CEO agit sous autorité Board) ou bug d'attribution ? À voir sur action pure CEO sans delegation |

---

## 2. Architecture runtime (ce que le test confirme)

### 2.1 Data flow

```
Human (Board) creates task STU-1 in UI
        ↓
Task persisted in PGlite: issues table, status=backlog
        ↓
Launch clicked → CEO heartbeat scheduled
        ↓
Heartbeat loop triggers claude-local adapter
        ↓
Adapter injects env: PAPERCLIP_AGENT_ID, PAPERCLIP_COMPANY_ID,
                     PAPERCLIP_TASK_ID=STU-1, PAPERCLIP_RUN_ID
        ↓
Adapter spawns claude CLI in a worktree (presumably)
        ↓
Claude loads paperclip skill via /skills/paperclip/SKILL.md
        ↓
CEO reads task, decides actions
        ↓
CEO calls /api/agent-hires with X-Paperclip-Run-Id header
        ↓
Server creates approval requests, posts to board inbox
        ↓
Heartbeat exits → status=idle
        ↓
Waits for human approval OR next scheduled heartbeat
```

### 2.2 Skills observed

Skills dans `skills/` du repo paperclip :
1. `paperclip/SKILL.md` — core API interaction (CEO used it)
2. `paperclip-create-agent/` — hire flow (CEO used it pour LEAD-DEV + CONTENT)
3. `paperclip-create-plugin/` — non utilisé ce run
4. `para-memory-files/` — non utilisé ce run

**Pattern d'injection** : skills vivent dans le FS de paperclip, pas dans la DB. Ils sont chargés côté agent au premier heartbeat (via un mécanisme non encore tracé — probablement l'adapter monte le dossier skills/ comme mount point).

### 2.3 DB schema inferred (from UI)

Tables visibles/déductibles :
- `companies` (Studio Iris)
- `agents` (CEO, LEAD-DEV pending, CONTENT pending)
- `projects` (Onboarding auto-créé)
- `issues` (STU-1) avec FK project_id, assignee_id, status enum
- `goals` (Livrer des produits web 3x plus vite...)
- `approvals` (2 rows : hire-LEAD-DEV, hire-CONTENT)
- `activity_log` (15+ rows déjà, tous les `Board *` events)
- `cost_events` (lié aux tokens 448.2k)
- `budget_policies` (1 row upserted, policy=Open)
- `heartbeat_runs` (au moins 1 row pour le run qu'on a vu)

Beaucoup de tables de support probables : `attachments`, `comments`, `documents` (CEO a "created document for STU-1").

---

## 3. Analyse : qu'est-ce qui marche BIEN ?

### 3.1 🔥 Runtime skill discovery est une tuerie

Le CEO n'a rien à configurer : il trouve `paperclip-create-agent` tout seul et l'utilise. En mb v2, chaque agent a ses skills en frontmatter `allowed-tools:`, statique. Si on veut qu'un agent apprenne un nouveau pattern, il faut éditer son SKILL.md.

**Implication mb v2.1** : ajouter un mécanisme où les skills dans `skills/` sont découvrables au runtime par n'importe quel agent, pas juste les skills déclarés dans son frontmatter.

### 3.2 🔥 Approval gates visibles dans une Inbox est l'UX parfaite

2 clics pour approuver. Pas de yaml à éditer, pas de CLI. Mobile-ready.

Pour mb : si on veut porter, faut au minimum un fichier `memory/approvals-pending.yaml` que l'utilisateur édite. Pas au niveau UX, mais fonctionnel.

### 3.3 🔥 Audit log granulaire avec actor attribution

Chaque action attribuée à un actor (Board, CEO, etc.) + subject (STU-1, LEAD-DEV, etc.) + timestamp. Pour debug et post-mortem = parfait.

**Implication mb v2.1** : déjà planifié (cf paperclip.md §2 run-id tracing). La forme `memory/runs/{run-id}.jsonl` avec {timestamp, actor, action, target} suffit.

### 3.4 🟢 Le UX du task lui-même est très soigné

- Breadcrumb `Issues > STU-1`
- Properties panel à droite (Status, Priority, Assignee, Project, Parent, Blocked by, Sub-issues, Reviewers, Approvers)
- Tabs `Chat` / `Activity`
- Chat = timeline avec "Worked · ran N commands" collapsible → tu peux déployer pour voir les tool calls
- Reply box en bas avec select de "who reply as" (CEO / Board)

C'est 1000x plus riche que le handoff.md de mb. Mais c'est du UX web qu'on ne va pas construire.

---

## 4. Analyse : qu'est-ce qui marche MAL ?

### 4.1 💥 Cost enforcement est illusoire avec Claude Code local

La feature marketing la plus vendue de Paperclip ("atomic budget enforcement") ne fonctionne PAS si tu utilises ton abonnement Claude Pro/Max. Le seul cas où ça protège réellement ton wallet c'est si tu paies l'API Anthropic directement, ce que peu d'utilisateurs solo font.

Rate limit protection serait la vraie feature. Mais paperclip ne track pas le rate limit headroom.

**Pour mb** : si on porte le budget, faut le faire au niveau **tokens par agent par heartbeat** (proxy raisonnable pour rate limit), pas $$. À noter dans la spec de la feature.

### 4.2 💥 Le CEO répond en anglais malgré input français

Symptôme du problème plus large : le system prompt est figé par l'adapter claude-local. Le `description` du task et la `mission` de la company ne suffisent pas à override.

**Pour mb** : dans v2.1, quand un projet a une `mb-stage.yaml`, forcer une section `locale:` qui override le system prompt du LLM.

### 4.3 🟡 Le wizard ne configure pas le budget

Même si on indique un budget à l'install, il n'est pas persisté avant le premier heartbeat. Bug ou feature ? À voir.

### 4.4 🟡 Pas de vue agrégée "live work"

Tu dois cliquer dans un issue pour voir ce que fait l'agent. Pas de dashboard style "voir tous les agents en train de travailler là". Probablement sur la roadmap.

---

## 5. Mise à jour du scoring pour mb-framework v2.1

Avant ce test, j'avais proposé (dans `paperclip.md`) 7 patterns à porter. Après observation live, je re-score :

| # | Pattern | Score avant | Score après test | Raison |
|---|---|---|---|---|
| 1 | Run-id tracing | Haute | **Très haute** | Activity log confirme valeur énorme. À faire en v2.1 en priorité. |
| 2 | Export/import project | Haute | Haute (idem) | Boutons Import/Export observés mais pas testés run |
| 3 | Budget hard-stop | Moyenne | **Basse** | Inopérant avec claude-local. Voir §4.1. Remplacer par rate-limit tracker. |
| 4 | Scoped-wake fast path | Moyenne | Moyenne | Observé en live (CEO fast path) mais gain marginal |
| 5 | `mb-multi.yaml` | Moyenne | Moyenne | Le multi-company de paperclip est exactement ça, confirmé |
| 6 | `mb-approval-gate` skill | Basse | **Moyenne** | L'UX Inbox est si bonne qu'elle mérite un minimum d'effort |
| 7 | MCP server | Haute | Haute (idem) | Priorité absolue pour use case non-tech |
| **NEW 8** | **Runtime skill discovery** | - | **Très haute** | Observé en live, changement de paradigme. À intégrer en v2.1. |
| **NEW 9** | **Actor-attributed audit log** | - | **Haute** | Fusionne avec #1. `memory/activity.jsonl` |
| **NEW 10** | **Dynamic agent creation** | - | **Moyenne** | `/mb:hire "role"` générateur de persona markdown on-the-fly |
| **NEW 11** | **Token-per-agent ledger** | - | **Haute** | Proxy pour rate limit, évite surprise quota. Remplace #3. |

### Nouvelle priorisation v2.1 (top 5)

1. **#8 Runtime skill discovery** — changement de paradigme, débloque #10
2. **#1+#9 Fusion : `memory/runs/{id}.jsonl` + actor attribution** — audit natif
3. **#11 Token-per-agent ledger** — cap par heartbeat, évite rate limit surprise
4. **#7 MCP server** — débloque wife use-case et Claude Desktop
5. **#2 Export/import** — portabilité mb across projets

Items 3, 4, 5, 6 descendent au second rang.

---

## 6. Décisions concrètes pour mb v2.1

Propositions à valider par Yanick :

### Must-have v2.1

- [ ] **M1** : `memory/runs/{run-id}.jsonl` append-only avec schema `{ts, actor, action, target, tokens, result}`
- [ ] **M2** : Runtime skill registry — orchestrator peut charger n'importe quel skill de `skills/` au moment du dispatch, pas juste ceux déclarés dans le frontmatter de l'agent
- [ ] **M3** : Token ledger — compteur par agent dans `memory/token-ledger.yaml`, reset mensuel, warning à 70% du cap

### Should-have v2.1

- [ ] **S1** : `/mb:export {projet}` — zip de `.claude/mb/mb-stage.yaml` + `memory/` + `project-skills/` avec scrubbing de secrets (regex sur .env.local, creds/)
- [ ] **S2** : `/mb:import {zip}` — inverse
- [ ] **S3** : `locale:` dans `mb-stage.yaml` — force la langue dans tous les agents du projet

### Nice-to-have v2.1 (gros effort)

- [ ] **N1** : MCP server exposant `/mb:validate` et `/mb:ship` comme tools MCP
- [ ] **N2** : `/mb:hire "frontend specialist"` — génère un SKILL.md ad hoc basé sur un template + description utilisateur

### NE PAS faire

- ❌ Budget enforcement en dollars (inopérant claude-local)
- ❌ Org chart hiérarchique (mb est flat, ça casse la simplicité)
- ❌ Multi-runtime adapters (Claude Code only par choix)
- ❌ UI web (philosophie markdown-only)

---

## 7. Actions suivantes à exécuter

### Côté test paperclip

- [ ] Approve les 2 hires dans l'Inbox (LEAD-DEV + CONTENT)
- [ ] Observer le 2e cycle heartbeat : CEO délègue-t-il correctement ?
- [ ] Observer la qualité du hiring plan 90 jours (jugement qualitatif)
- [ ] Laisser tourner 24h pour voir budget drift (tokens cumulés)
- [ ] Tester Export/Import company end-to-end

### Côté mb-framework

- [ ] Valider avec Yanick la priorisation v2.1 (4 must + 3 should)
- [ ] Créer branche `feat/v2.1-runtime-skills` pour M2 (le plus gros chantier)
- [ ] Créer issue GitHub #1 "v2.1 roadmap" listant M1-M3, S1-S3

---

## 8. Screenshots références

Les screenshots live du test sont dans `.playwright-mcp/` (gitignored — local only) :
- `page-*.jpeg` (snapshots full page)
- `console-*.log` (console browser output)
- `page-*.yml` (accessibility tree snapshots)

---

## 9. Evidence récapitulatif

- **STU-1 live** : `http://127.0.0.1:3100/STU/issues/STU-1` → status In Progress, CEO assigned, 5 "Worked" blocks visibles
- **Inbox** : 2 pending approvals visibles (Hire LEAD-DEV + Hire CONTENT)
- **Org** : CEO → {LEAD-DEV, CONTENT} tree auto-rendered
- **Costs** : 448.2k tokens / $0.00 (Claude Code local) / Budget Open
- **Activity** : 15+ events since company creation, full audit trail
- **Skills observées dans repo** : `skills/paperclip/`, `skills/paperclip-create-agent/`, `skills/paperclip-create-plugin/`, `skills/para-memory-files/`

## 10. Unknowns après ce test

- Comportement après approve (CEO délègue-t-il vraiment ou écrit-il tout lui-même ?)
- Mécanisme exact de chargement des skills (mount FS ? API call ? DB ?)
- Si `X-Paperclip-Run-Id` header est vraiment présent sur chaque request (pas tracé côté browser)
- Comportement concurrent : 3 agents en simultané = bottleneck claude-local ?
- Qualité du livrable final (hiring plan, sub-tasks breakdown)

## 11. Assumptions

- Le `Board approved` de fin d'activity log correspond à l'auto-approval du budget policy, pas à l'un des 2 hires (les 2 sont encore "pending" dans l'Inbox)
- Le heartbeat interval par défaut de paperclip est suffisamment court pour que la démo tienne en < 10 min (confirmé)
- L'adapter claude-local lance un nouveau process Claude Code par heartbeat, pas une session persistante (non vérifié mais cohérent avec skills/paperclip/SKILL.md)
