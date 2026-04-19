# Paperclip — patterns à étudier pour mb-framework

**Source** : [github.com/paperclipai/paperclip](https://github.com/paperclipai/paperclip) (fork : `Yanick-mj/paperclip`)
**Clone local** : `/Users/yanickmingala/code/Yanick-mj/paperclip`
**Date d'analyse** : 2026-04-19
**Version analysée** : master @ `b9a80dc` (15 Apr 2026)
**License** : MIT — safe à porter/adapter

---

## Vocabulaire de correspondance

| Paperclip | mb-framework v2 |
|---|---|
| Company | Project |
| Goal | Epic / feature requirement |
| Agent (CEO/CTO/Dev…) | Persona markdown (pm / lead-dev / fe-dev…) |
| Task (issue) | Story |
| Heartbeat | Agent turn in pipeline |
| Skill (runtime-injected) | SKILL.md (static) |
| Adapter | Claude Code runtime (unique) |
| Budget | *(non-existent)* |
| Org tree | *(flat personas)* |
| Run-id trace | handoff.md + memory/_session/ |

---

## Ce que paperclip fait *mieux* que mb-framework

### 1. 🟢 Cost enforcement atomique

**Paperclip** : `packages/db/src/schema` a une table `cost_events`. `server/src/services/budgets.ts` enforce un hard-stop quand le budget mensuel est dépassé — **atomic transaction** sur le checkout de task.

**mb v2** : `memory/cost-log.md` est manuel, append-only, jamais lu pour bloquer.

**À porter** : Pattern "budget par agent par mois" avec checkout atomique.

```yaml
# Proposal pour mb-config.yaml
budgets:
  monthly_per_agent:
    fe-dev: "$20"
    architect: "$10"
    tea: "$15"
  hard_stop: true   # refuse new tasks if budget exceeded
  rollover: false   # reset at month boundary
```

Implementation mb-v2.1 possible : un fichier `memory/budget-state.yaml` lu avant chaque dispatch, mis à jour après, versionné git (audit gratuit).

---

### 2. 🟢 Run-id tracing

**Paperclip** : chaque heartbeat génère un `PAPERCLIP_RUN_ID`. Tous les writes d'API incluent `X-Paperclip-Run-Id: $PAPERCLIP_RUN_ID` → traçabilité complète "qu'est-ce que cet agent a fait pendant cette run".

**mb v2** : `handoff.md` existe mais n'est pas structuré comme un run log — c'est un message libre entre agents.

**À porter** : Chaque invocation d'agent reçoit un `mb-run-id` (timestamp + hash). Toutes les modifs écrivent à `memory/runs/{run-id}.jsonl` en append-only.

Avantage : tu peux dire "rollback run abc123" et effacer exactement ce que cet agent a touché.

---

### 3. 🟢 Scoped-wake fast path

Depuis `skills/paperclip/SKILL.md:30` :
> **Scoped-wake fast path.** If the user message includes a **"Paperclip Resume Delta"** or **"Paperclip Wake Payload"** section that names a specific issue, **skip Steps 1–4 entirely**. Go straight to Step 5.

**Insight** : un agent qui est réveillé *spécifiquement pour X* ne doit pas re-scanner tout le repo. Il reçoit le payload de réveil, traite directement, exit.

**mb v2** : Step 0.5 Stage Detection + Step 1 Classification s'exécutent TOUJOURS, même si orchestrator ré-appelle fe-dev pour un patch.

**À porter** : `orchestrator` Step 0 bis — détecte si c'est un "resume" (handoff.md mentionne cette agent + task précis) vs un cold start. En resume, skip la classification complète.

---

### 4. 🟢 Skills marketplace / portability

**Paperclip** :
- `packages/db/src/schema` → `company_skills` table
- `server/src/services/company-portability.ts` + `company-export-readme.ts` → export/import d'une "company entière" (org, agents, skills, prompts) en un zip
- ROADMAP mentionne "Clipmart" — marketplace de companies
- `ls skills/` = 4 skills pré-fabriqués (paperclip, paperclip-create-agent, paperclip-create-plugin, para-memory-files)

**mb v2** : Skills sont dans le repo, pas de marketplace, pas d'export/import.

**À porter** : `/mb:export` → zip de tout `agents/` + `agents-early/` + `mb-stage.yaml` + `memory/` (avec scrubbing des secrets) → partageable. `/mb:import` → inverse. Permet à Yanick de cloner mb-framework-otoqi vers mb-framework-studio-iris avec 1 commande.

---

### 5. 🟢 Multi-company isolation dans 1 deployment

**Paperclip** : single-tenant process, multi-company data model. Toutes les tables ont `company_id`. Un process orchestre N companies.

**mb v2** : 1 clone de mb-framework par projet. Si tu as 5 projets, 5 clones.

**À porter ? Probablement pas.** Raison : mb-framework est délibérément zero-infrastructure. Porter la multi-company nécessite un process running, un DB, etc. C'est la philosophie de paperclip, pas la nôtre.

**Alternative plus légère** : `mb-multi.yaml` à `~/.mb/` listant tous les projets mb-framework trouvés, avec un dashboard `mb status --all` qui lit les `mb-stage.yaml` de chacun. Garde zero-infra mais donne une vue d'ensemble.

---

### 6. 🟢 Heartbeat-based execution model

**Paperclip** : agents tournent en "heartbeats" scheduled (cron) ou event-driven (task assigned, comment). Ils ne runnent pas en continu. Ils wake up, check, act, exit.

**mb v2** : Agents s'invoquent via slash commands, tout est synchrone dans un flow humain-déclenché.

**À étudier** : Tu pourrais avoir un `/mb:cron` qui setup un cron OS-level lançant `claude --headless "run /mb:sprint"` tous les matins. Déjà possible en dehors du framework avec `crontab`, mais un skill `cron-advisor` qui génère la bonne config serait utile.

**Caveat** : mb est Claude Code-only. Claude Code n'est pas fait pour tourner en headless 24/7 (cf ton expérience nested session). Paperclip résout ça parce qu'il abstrait le runtime (claude-local adapter). Pour porter le pattern chez nous, il faudrait soit :
- Un mode "mb-headless" (shell qui run mb skills sans Claude Code) — gros chantier
- Accepter que mb reste synchrone et event-driven = OK pour solo dev

---

### 7. 🟢 Approval gates explicites (governance)

**Paperclip** :
- `packages/db/src/schema` → `approvals` table
- `server/src/routes/approvals.ts` + `server/src/services/approvals.ts`
- Hiring un agent, changement de stratégie, budget rollover → require board approval

**mb v2** : Les gates (DS UPDATE GATE, verifier, etc.) sont auto-enforced par skills. Pas de "demande d'approbation humaine" structurée.

**À porter** : Skill `mb-early-approval-gate` qui agrège les décisions à faire valider à un humain. `memory/approvals-pending.yaml`. Utile particulièrement pour le pipeline discovery→mvp où une upgrade de stage est une décision stratégique qui mérite validation explicite.

---

## Ce que mb-framework fait *mieux* que paperclip

### 1. 🟢 Zero infrastructure

- Paperclip : Node + Postgres + UI React + 274K LOC
- mb : markdown files + un Claude Code

→ Onboarding mb = 30 secondes. Paperclip = `pnpm install` + config DB + login.

### 2. 🟢 Stage-aware philosophy

mb a les 4 stages (discovery/mvp/pmf/scale). Paperclip est agnostic — tu peux shipper n'importe quoi, les gates ne s'adaptent pas à la maturité du produit.

mb force les bonnes pratiques au bon moment (TDD off en discovery, on en pmf).

### 3. 🟢 Markdown-only = portable

mb-framework est `git clone`able, lisible sans outil, éditable dans n'importe quel éditeur. Paperclip requiert son serveur running pour lire les skills (ils sont DB-stored).

### 4. 🟢 Opinionated method, not infra

Paperclip dit : "bring your own agents, we coordinate". mb dit : "voici COMMENT penser ton projet".

Complémentaire, pas compétitif.

---

## Patterns neutres / dépendent du contexte

### Plugin system

Paperclip a un SDK plugin (`packages/plugins/sdk/`) avec dev-server, exemples (hello-world, file-browser, kitchen-sink). Permet à des tiers d'ajouter des features.

**Pour mb** : pas sûr qu'on en ait besoin. Skills + `project-skills/` couvrent déjà l'extension. Un plugin SDK ajoute de la complexité.

**Décision suggérée** : skip pour v2.x, revoir pour v3 si demande user-driven.

### MCP server

`packages/mcp-server/` — Paperclip expose son API en MCP, donc d'autres clients MCP (Claude Desktop, Cursor) peuvent interagir avec.

**Pour mb** : pertinent si tu veux que ta femme utilise mb depuis Claude.ai sans CLI. Un `mb-mcp-server` qui expose `/mb:validate` et `/mb:ship` comme tools MCP → elle lance Claude Desktop + MCP server → fait tout en chat. **C'est peut-être la vraie "Option 3 mb-lite" que je cherchais dans la conversation précédente.**

**Décision suggérée** : sérieusement candidate pour mb v2.2 ou v3.

---

## Proposition : roadmap mb v2.1 inspirée paperclip

Priorisé par ratio valeur/coût :

| # | Feature | Origine paperclip | Effort | Valeur |
|---|---|---|---|---|
| 1 | Run-id tracing via `memory/runs/{run-id}.jsonl` | §2 | S | 🔥 Haute (debug + rollback) |
| 2 | `/mb:export` + `/mb:import` project (zip + scrubbing) | §4 | M | 🔥 Haute (portabilité) |
| 3 | `memory/budget-state.yaml` + hard-stop check | §1 | M | 🟡 Moyenne (solo dev peut tolérer) |
| 4 | Scoped-wake fast path dans orchestrator | §3 | S | 🟡 Moyenne (perf marginale) |
| 5 | `mb-multi.yaml` + `mb status --all` | §5 | M | 🟡 Moyenne (serial entrepreneur uniquement) |
| 6 | Skill `mb-approval-gate` | §7 | S | 🟢 Basse (discovery→mvp uniquement) |
| 7 | MCP server exposant `/mb:validate` et `/mb:ship` | Plugin §MCP | L | 🔥 Haute (débloque wife use-case) |

Si tu ne fais qu'**UNE** chose : **#7 (MCP server)**. Ça débloque ta femme + tout non-tech founder + rend mb-framework adressable depuis Claude Desktop sans CLI.

Si tu en fais **trois** : #7 + #1 (run-id) + #2 (export/import).

---

## Ce qu'il NE FAUT PAS porter

1. ❌ **Le serveur Node + DB** — casse la philosophie zero-infra de mb
2. ❌ **Le système de plugins complet** — ajout de complexité sans demande prouvée
3. ❌ **L'org tree strict (single manager)** — mb n'a pas besoin de hiérarchie, les agents coopèrent via handoff
4. ❌ **Les adapters multi-runtime** — mb est Claude Code-only par choix, simplicité > flexibilité
5. ❌ **La télémétrie anonyme par défaut** — mb n'a aucune télémétrie et on veut que ça reste comme ça

---

## Plan de test (à exécuter)

```bash
cd /Users/yanickmingala/code/Yanick-mj/paperclip

# 1. Démarre le server + UI (localhost:3100)
pnpm dev

# 2. Dans un autre terminal, onboard une company
npx paperclipai onboard --yes

# 3. UI à http://localhost:3100 — crée :
#    - 1 company "test-wife-product"
#    - 1 goal "validate idea X"
#    - 1 agent "CEO" avec adapter=claude-local
#    - 1 task "interview 3 users"

# 4. Observe le heartbeat :
tail -f data/pglite/*.log    # (ou via UI)

# 5. Tue tout et reset
pkill -f paperclip
rm -rf data/pglite
```

---

## Questions ouvertes pour toi

1. Est-ce que tu veux que je commence la branche `feat/v2.1-mcp-server` (priorité #7) ?
2. Est-ce que l'export/import de projet (priorité #2) couvre le use-case "ma femme veut démarrer un projet en clonant le tien" ?
3. Es-tu à l'aise avec le fait que mb reste Claude Code-only, ou tu veux un adapter layer comme paperclip ?

---

## Evidence

- README quotes vérifiés lignes 30-32, 163-167 de `paperclip/README.md`
- `skills/paperclip/SKILL.md:30` confirme le scoped-wake fast path
- `server/src/routes/` listé : 20+ routes incluant `approvals.ts`, `budgets.ts` (via services), `costs.ts`, `companies.ts`
- `server/src/services/` listé : `budgets.ts`, `company-portability.ts`, `company-export-readme.ts` confirmés
- `packages/adapters/` : 7 adapters (claude-local, codex-local, cursor-local, gemini-local, openclaw-gateway, opencode-local, pi-local)
- Licence MIT confirmée : `LICENSE` → `MIT © 2026 Paperclip`
- Fork créé : `https://github.com/Yanick-mj/paperclip` (commande `gh repo fork`)
- Clone local : `/Users/yanickmingala/code/Yanick-mj/paperclip`
- pnpm install : 22.9s, warnings plugin-dev-server non bloquants

## Unknowns

- Comportement réel en live (test `pnpm dev` pas encore lancé)
- Perf du heartbeat à volume réaliste (10+ agents simultanés)
- Ergonomie de l'UI mobile (claim du README, pas vérifié)
- Cost réel d'un run 24/7 avec 3-5 agents

## Assumptions

- Les patterns markés "à porter" sont portables sans casser la philosophie markdown-only de mb — à re-vérifier à l'implémentation
- La priorité #7 (MCP server) nécessite de comprendre comment MCP tools exposent des skills stateful — c'est **le gros inconnu technique**
