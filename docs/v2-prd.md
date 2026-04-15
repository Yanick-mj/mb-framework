# mb-framework v2 — Stage-Aware PRD

**Date** : 2026-04-15
**Auteur** : Yanick + Claude
**Status** : Draft for validation
**Type** : Spec — pas de code dans ce document

---

## 1. Contexte

mb-framework v1 a été conçu pour **otoqi** : un produit B2B en production avec compliance, RLS, paiements, mobile + web. Les gates actuels (TDD, DS UPDATE GATE, Decision Gates, RLS double-check) sont calibrés pour ce niveau de maturité.

**Problème** : Yanick est serial entrepreneur. Les prochains projets démarreront en **early stage** (validation d'idée, MVP janky, recherche de PMF). Imposer la rigueur "Scale" à un projet "Discovery" :

- Tue la vitesse d'apprentissage (qui est la vraie unité de valeur en early stage)
- Force du sur-engineering inutile (TDD sur du throwaway code)
- Bloque les pipelines sur des gates non pertinents (DS UPDATE GATE sur une landing page de validation)

**Inversement**, désactiver tous les gates pour aller vite réintroduit les bugs critiques que le framework v1 prévient (cf. bug SIRET, contre-offre missing, RLS leaks).

→ **Solution v2** : framework **stage-aware**. Un seul outil installable, qui s'adapte automatiquement au stade du projet.

---

## 2. Goals / Non-Goals

### Goals

| # | Goal | Mesurable par |
|---|---|---|
| G1 | Un projet en Discovery peut produire un go/no-go en < 2 jours | Pipeline `idea-validator` exécutable seul, sans dépendance |
| G2 | Un projet en MVP peut shipper un wedge fonctionnel en < 48h | `wedge-builder` skip TDD/DS gate, output déployé |
| G3 | Le passage Stage N → Stage N+1 active automatiquement les gates supérieurs | `stage-advisor` recommande, `mb-stage.yaml` enregistre, orchestrator applique |
| G4 | **Tout le contenu des skills v1 est préservé** | Aucun skill v1 supprimé ; aucune règle CRITICAL retirée ; sections existantes intactes |
| G5 | Les projets v1 (otoqi) continuent de fonctionner sans modification | Pas de breaking change sur les commandes `/mb:*` ni sur les skills existants |

### Non-Goals

- **Pas** un framework de growth/marketing (pas de pricing-advisor, pas de launch-coordinator marketing)
- **Pas** une refonte des skills v1 (uniquement des extensions stage-aware)
- **Pas** de migration forcée — otoqi reste en mode "implicit Scale" sans `mb-stage.yaml`
- **Pas** de changement de commande utilisateur (`/mb:feature`, `/mb:sprint`, etc.)

---

## 3. Modèle conceptuel : 4 stages

```
Stage 0: DISCOVERY   → idée → problem validation        (jours-semaines)
Stage 1: MVP         → janky build → first paying user  (semaines)
Stage 2: PMF         → first customers → recurring rev  (mois)
Stage 3: SCALE       → prod-grade, compliance, SLA      (continu)
```

### Critères de transition (validés par `stage-advisor`)

| De → Vers | Critères (TOUS requis) |
|---|---|
| Discovery → MVP | ≥ 3 user interviews documentés ; problème scoré douloureux/fréquent/coûteux ; 1-liner validé ; wedge plan écrit |
| MVP → PMF | ≥ 3 paying users ; rétention > 1 mois ; analytics events en place ; pricing testé |
| PMF → Scale | MRR stable ≥ 3 mois ; SLA/compliance requis ; équipe > 1 dev ; CI/CD en place |

### Stage par défaut

- Projet **sans** `mb-stage.yaml` → traité comme **Scale** (rétro-compatibilité otoqi)
- Projet **avec** `mb-stage.yaml: discovery` → mode early stage activé

---

## 4. Stratégie de préservation (contrainte forte du user)

**Règle d'or v2** : aucune modification destructive des skills v1.

### Méthode : extension par sections additionnelles

Chaque skill v1 reçoit une **section unique additionnelle** en fin de fichier :

```markdown
## Stage Adaptation (v2)

| Stage | Behavior |
|-------|----------|
| discovery | <comportement adapté ou OFF> |
| mvp       | <comportement adapté ou OFF> |
| pmf       | <comportement v1 partiel> |
| scale     | <comportement v1 complet, par défaut> |
```

**Aucune règle existante n'est supprimée.** Les rules CRITICAL des skills v1 restent applicables au stage Scale (le défaut). Pour les stages inférieurs, certaines rules sont marquées comme `relaxed` ou `off` via la table d'adaptation.

### Méthode : nouveaux skills additifs

Les comportements early-stage qui n'existent pas en v1 deviennent des **nouveaux skills**, pas des modifications de v1. Exemples : `idea-validator`, `wedge-builder`, `stage-advisor`.

### Méthode : routing conditionnel dans orchestrator

L'orchestrator ajoute une **Step 0.5 — Stage Detection** AVANT la Step 1 — Classification existante. Cette nouvelle étape lit `mb-stage.yaml` et peut court-circuiter le routing v1 vers un pipeline stage-aware.

Les routes v1 restent intactes, simplement non sélectionnées si le stage le détourne.

---

## 5. Architecture v2

### 5.1 Nouveau fichier racine : `mb-stage.yaml`

Fichier ajouté à la racine du projet (pas dans `.claude/mb/`) lors de l'install ou via `/mb:init`.

```yaml
# mb-stage.yaml
version: 1
stage: mvp                 # discovery | mvp | pmf | scale
since: 2026-04-15
target_next: pmf

# Critères pour upgrade vers target_next (lus par stage-advisor)
upgrade_criteria:
  paying_users: 0          # target: 3
  retention_months: 0      # target: 1
  analytics_in_place: false
  pricing_tested: false

# Overrides manuels (optionnel)
overrides:
  force_ds_gate: false     # forcer DS UPDATE GATE même en MVP
  force_tdd: false         # forcer TDD même en MVP
```

### 5.2 Modification minimale : `mb-config.yaml`

Ajout d'une seule section optionnelle, sans toucher à l'existant :

```yaml
# Ajout en fin de fichier
stage_aware:
  enabled: true            # false = comportement v1 strict
  default_stage: scale     # si mb-stage.yaml absent
```

### 5.3 Nouvelle structure de dossiers

```
mb-framework/
├── agents/                          ← v1 préservé intégralement
│   ├── orchestrator/SKILL.md        ← + Step 0.5 + section Stage Adaptation
│   ├── pm/SKILL.md                  ← + section Stage Adaptation
│   ├── architect/SKILL.md           ← + section Stage Adaptation
│   ├── lead-dev/SKILL.md            ← + section Stage Adaptation
│   ├── ux-designer/SKILL.md         ← + section Stage Adaptation
│   ├── be-dev/SKILL.md              ← + section Stage Adaptation
│   ├── fe-dev/SKILL.md              ← + section Stage Adaptation
│   ├── tea/SKILL.md                 ← + section Stage Adaptation
│   ├── verifier/SKILL.md            ← + section Stage Adaptation
│   ├── devops/SKILL.md              ← + section Stage Adaptation
│   ├── tech-writer/SKILL.md         ← + section Stage Adaptation
│   ├── sm/SKILL.md                  ← + section Stage Adaptation
│   └── quick-flow/SKILL.md          ← + section Stage Adaptation
│
├── agents-early/                    ← NEW : skills early-stage uniquement
│   ├── stage-advisor/SKILL.md       ← méta-skill
│   ├── idea-validator/SKILL.md      ← Discovery
│   ├── user-interviewer/SKILL.md    ← Discovery + MVP
│   └── wedge-builder/SKILL.md       ← MVP
│
├── commands/                        ← v1 préservé
│   ├── feature.md, sprint.md, fix.md, review.md, init.md
│   └── stage.md                     ← NEW : `/mb:stage` (info, upgrade, downgrade)
│   └── validate.md                  ← NEW : `/mb:validate` (Discovery flow)
│   └── ship.md                      ← NEW : `/mb:ship` (MVP wedge flow)
│
├── templates/                       ← v1 préservé
│   ├── code/                        ← actif PMF + Scale
│   ├── discovery/                   ← actif tous stages (déjà existant!)
│   ├── stacks/                      ← actif tous stages
│   ├── validation/                  ← actif PMF + Scale
│   └── stages/                      ← NEW
│       ├── discovery/
│       │   ├── interview-script.md
│       │   ├── 10q-evaluation.md
│       │   ├── anti-tarpit-check.md
│       │   └── go-no-go-report.md
│       ├── mvp/
│       │   ├── wedge-plan.md
│       │   ├── landing-page.md
│       │   ├── 1-liner-checklist.md
│       │   └── ship-note.md
│       ├── pmf/
│       │   └── analytics-event-spec.md
│       └── scale/
│           └── (pointe vers validation/ existant)
│
├── skills/                          ← v1 préservé
│   └── ux-design/
│
├── memory/                          ← v1 préservé
│   └── + stage-history.md           ← NEW : log des transitions de stage
│
├── mb-config.yaml                   ← + section stage_aware
├── mb-stage.yaml.template           ← NEW
├── install.sh                       ← + génération mb-stage.yaml interactif
└── docs/
    ├── v2-prd.md                    ← ce document
    └── v2-migration.md              ← NEW (à rédiger en phase impl)
```

### 5.4 Modifications de `install.sh`

Ajouts uniquement, pas de modification des étapes existantes :

```
[étapes 1-4 existantes inchangées]

5. NEW : Si mb-stage.yaml absent, demander interactivement :
   "Quel est le stage de ce projet ? [discovery/mvp/pmf/scale] (default: scale)"
   → Génère mb-stage.yaml.template adapté
   → Skip si flag --no-stage passé

6. NEW : Symlink agents-early/ → .claude/skills/mb-early-{name}/
```

---

## 6. Matrice stage × skill (référentiel)

🟢 = actif par défaut, 🟡 = optionnel/light, 🔴 = désactivé

| Skill | Discovery | MVP | PMF | Scale (v1) |
|---|---|---|---|---|
| `orchestrator` | 🟢 stage-aware routing | 🟢 stage-aware routing | 🟢 stage-aware routing | 🟢 v1 routing |
| `stage-advisor` (NEW) | 🟢 | 🟢 | 🟢 | 🟢 |
| `idea-validator` (NEW) | 🟢 | 🔴 | 🔴 | 🔴 |
| `user-interviewer` (NEW) | 🟢 | 🟢 | 🟡 | 🔴 |
| `wedge-builder` (NEW) | 🔴 | 🟢 | 🔴 | 🔴 |
| `pm` | 🟢 1-liner + 10Q | 🟢 1-liner + interview synth | 🟢 v1 | 🟢 v1 |
| `architect` | 🟡 1 service max | 🟢 wedge architecture | 🟢 v1 ADR light | 🟢 v1 full |
| `lead-dev` | 🔴 | 🟡 tasks only, no flows | 🟢 v1 breakdown | 🟢 v1 + decision gates |
| `ux-designer` (Discovery) | 🟢 wireframes janky | 🟢 landing-first | 🟡 light | 🟢 v1 full |
| `ux-designer` (Delivery) | 🔴 | 🟡 visual only | 🟢 v1 specs | 🟢 v1 + DS GATE |
| `be-dev` | 🔴 | 🟡 janky OK, no TDD | 🟢 v1 | 🟢 v1 + RLS double-check |
| `fe-dev` | 🔴 | 🟡 no Atomic, no DS gate | 🟢 v1 + Atomic | 🟢 v1 full |
| `tea` | 🔴 | 🟡 smoke tests only | 🟢 v1 + analytics events | 🟢 v1 full |
| `verifier` | 🔴 | 🟡 deploy check only | 🟢 v1 4 dims | 🟢 v1 + compliance |
| `devops` | 🟡 vercel quick-deploy | 🟢 CI basic | 🟢 v1 + rollback | 🟢 v1 + observability |
| `tech-writer` | 🔴 | 🟢 1-liner + ship note | 🟢 v1 | 🟢 v1 full |
| `sm` | 🔴 | 🔴 | 🟢 sprint planning | 🟢 v1 |
| `quick-flow` | 🟢 default | 🟢 default | 🟡 fallback | 🔴 exception |

---

## 7. Détail des nouveaux skills

### 7.1 `stage-advisor/SKILL.md` (méta-skill)

| Field | Value |
|---|---|
| Input | `{ action: "detect" \| "evaluate" \| "upgrade" \| "downgrade" }` |
| Output | `{ current_stage, target_stage, criteria_met: [], criteria_missing: [], recommendation }` |
| Trigger | Invoké par orchestrator au Step 0.5, ou via commande `/mb:stage` |

**Responsabilités**
- Lit `mb-stage.yaml` (ou propose sa création)
- Évalue les critères de transition (paying_users, retention, analytics, etc.)
- Recommande upgrade quand critères atteints
- Bloque downgrade sauf si user le force explicitement
- Met à jour `memory/stage-history.md` à chaque changement

**Rules CRITICAL**
1. NEVER auto-upgrade sans confirmation user
2. Toujours montrer les criteria_met / criteria_missing
3. Suggérer les actions concrètes pour passer au stage suivant
4. Si Scale détecté sans `mb-stage.yaml` → silent (rétrocompat otoqi)

### 7.2 `idea-validator/SKILL.md`

| Field | Value |
|---|---|
| Input | `{ idea: string, founder_context: string, target_market: string }` |
| Output | `{ verdict: "go" \| "no-go" \| "validate-with-interviews", report_path, suggested_pivots? }` |
| Trigger | `/mb:validate "idée"` ou stage:discovery + `/mb:feature` |

**Pipeline interne**
1. Apply 10-Question YC framework (founder-market fit, market size, problem acuteness, etc.)
2. Apply Anti-Tarpit checklist (CISP, tarpit, perfect idea, first idea)
3. Generate 1-liner + grandmother test
4. Output report dans `templates/stages/discovery/go-no-go-report.md`
5. Si "validate-with-interviews" → handoff vers `user-interviewer`

### 7.3 `user-interviewer/SKILL.md`

| Field | Value |
|---|---|
| Input | `{ problem_hypothesis, interview_transcripts: string[], interview_count: number }` |
| Output | `{ pain_score, common_patterns, vocabulary, wedge_suggestion, cold_email_templates }` |
| Trigger | Suite du `idea-validator` ou direct |

**Pipeline interne**
1. Si interview_count < 3 → status: blocked + message "need more interviews"
2. Pattern recognition sur transcripts (douleur commune, vocabulaire client)
3. Score pain acuteness = fréquence × intensité × coût
4. Génère cold email templates personnalisés (1 par segment détecté)
5. Suggère wedge product : 1 problème → 1 solution → 1 persona → 1 canal

### 7.4 `wedge-builder/SKILL.md`

| Field | Value |
|---|---|
| Input | `{ wedge_plan: from user-interviewer, deadline_hours: 48 }` |
| Output | `{ deployed_url, ttfv_hours, test_users_invited, kill_date }` |
| Trigger | `/mb:ship` ou stage:mvp + `/mb:feature` |

**Anti-skills assumés** (oppose-toi explicitement aux skills v1)
- Skip TDD
- Skip Atomic Design
- Skip DS UPDATE GATE
- Skip RLS double-check
- Accepte janky stack (Sheets + Zapier + script, Typeform + webhook, no-code)

**Gate unique bloquant**
- "Un vrai utilisateur l'a testé dans les 48h" → si non, status: blocked

**Output obligatoire**
- URL déployée
- TTFV en heures
- Date de mort prévue ("ce code disparaît au stage PMF")

---

## 8. Modifications par skill v1 (préservation stricte)

Pour chaque skill v1, **une seule modification** : ajout d'une section `## Stage Adaptation (v2)` en fin de fichier. Le reste du skill v1 reste **intact**.

### 8.1 Exemple : `pm/SKILL.md`

```markdown
[contenu v1 inchangé : interface, persona, rules, etc.]

---

## Stage Adaptation (v2)

When `mb-stage.yaml` is present, adapt behavior:

| Stage | Behavior |
|-------|----------|
| **discovery** | Skip PRD generation. Output a **1-pager** with: 1-liner, target persona, top-3 pain points (from user-interviewer), success metric. Use `templates/stages/discovery/`. Defer to `idea-validator` for go/no-go. |
| **mvp** | Generate **lean PRD** : 1-liner mandatory (10 words, no jargon), wedge product spec, 5 user testers identified, kill criteria. Skip stakeholder section. |
| **pmf** | Full v1 PRD behavior. Add analytics event spec section. |
| **scale** | Full v1 PRD behavior (default, current behavior). |

**1-liner gate (all stages)** : every PM output must include a 10-words-or-less, jargon-free, grandmother-readable description. STOP if missing.
```

### 8.2 Exemple : `fe-dev/SKILL.md`

```markdown
[contenu v1 inchangé]

---

## Stage Adaptation (v2)

| Stage | Behavior |
|-------|----------|
| **discovery** | OFF — wedge-builder handles UI in early stages |
| **mvp** | Single-file React/Next page allowed. Skip Atomic Design. Skip Component Audit. Skip DS UPDATE GATE. Inline styles OK. Goal: ship deployable in < 4h. |
| **pmf** | Full v1 behavior : Component Audit + Atomic Design + DS UPDATE GATE + TDD. |
| **scale** | Full v1 behavior (default). |

**Override** : if `mb-stage.yaml.overrides.force_ds_gate: true`, DS UPDATE GATE applies even in MVP.
```

### 8.3 Exemple : `orchestrator/SKILL.md`

Insertion d'une **Step 0.5** AVANT la Step 1 existante :

```markdown
[Step 0 v1 inchangé]

### Step 0.5 -- Stage Detection (v2)

1. Read `mb-stage.yaml` at project root
2. If absent → stage = `scale` (v1 default behavior, no change)
3. If present → load stage + overrides
4. Inject stage into context summaries for all downstream agents
5. If stage = `discovery` or `mvp` → check if early-stage routing applies (see Stage Routing Table below)

### Stage Routing Table (v2)

| Stage + task pattern                                | Pipeline                                                          |
|-----------------------------------------------------|-------------------------------------------------------------------|
| discovery + "validate idea"                         | idea-validator → user-interviewer (if needed)                     |
| discovery + any feature request                     | idea-validator (block "you're in discovery, validate first")      |
| mvp + "ship" or "build wedge"                       | wedge-builder → verifier (light)                                  |
| mvp + feature request                               | pm (lean) → wedge-builder OR architect (light) → fe-dev (light)  |
| pmf + any                                           | v1 routing table applies                                          |
| scale + any                                         | v1 routing table applies                                          |

[Step 1 v1 inchangé : Classify Task]
[Step 1.5 - 4 v1 inchangés]
```

Les 10 rules CRITICAL de v1 restent intactes. Ajout de 2 rules :

```markdown
11. (v2) NEVER override mb-stage.yaml without explicit user confirmation
12. (v2) ALWAYS pass current stage in context summary to downstream agents
```

### 8.4 Récapitulatif des modifications par skill v1

| Skill | Section ajoutée | Rules ajoutées | Risque de régression |
|---|---|---|---|
| orchestrator | Step 0.5 + Stage Routing Table + Stage Adaptation | 2 (rules 11-12) | Faible (Step 0.5 = no-op si pas de yaml) |
| pm | Stage Adaptation | 0 (1-liner gate intégré dans la section) | Nul |
| architect | Stage Adaptation | 0 | Nul |
| lead-dev | Stage Adaptation | 0 | Nul |
| ux-designer | Stage Adaptation (par mode) | 0 | Nul |
| be-dev | Stage Adaptation | 0 | Nul |
| fe-dev | Stage Adaptation | 0 | Nul |
| tea | Stage Adaptation + section "Analytics events spec" | 0 | Nul |
| verifier | Stage Adaptation | 0 | Nul |
| devops | Stage Adaptation | 0 | Nul |
| tech-writer | Stage Adaptation | 0 | Nul |
| sm | Stage Adaptation | 0 | Nul |
| quick-flow | Stage Adaptation | 0 | Nul |

**Garantie de préservation** : si `mb-stage.yaml` est absent, **AUCUN comportement v1 ne change**. Toutes les modifications sont des extensions conditionnelles.

---

## 9. Nouvelles commandes

| Commande | Description | Stage requis |
|---|---|---|
| `/mb:stage` | Affiche le stage actuel + critères de transition | tous |
| `/mb:stage upgrade` | Tente upgrade vers target_next (vérifie critères) | tous |
| `/mb:stage downgrade <stage>` | Force downgrade (avec confirmation) | tous |
| `/mb:validate "idée"` | Lance idea-validator (Discovery flow) | discovery |
| `/mb:ship "wedge"` | Lance wedge-builder (MVP flow) | mvp |
| `/mb:feature` (existant) | Comportement v1 + lecture stage si présent | tous |
| `/mb:sprint` (existant) | Inchangé | pmf, scale |
| `/mb:fix` (existant) | Inchangé | tous |
| `/mb:review` (existant) | Inchangé | tous |
| `/mb:init` (existant) | + propose création `mb-stage.yaml` | tous |

---

## 10. Migration path

### 10.1 Pour les projets v1 existants (otoqi)

1. **Aucune action requise**. Pas de `mb-stage.yaml` → traité comme Scale → comportement v1 strict.
2. Si Yanick veut explicitement marquer otoqi comme Scale : `echo "stage: scale" > mb-stage.yaml`. Aucun effet runtime, juste documentation.

### 10.2 Pour les nouveaux projets early stage

1. `git submodule add git@github.com:Yanick-mj/mb-framework.git .claude/mb`
2. `bash .claude/mb/install.sh` → **prompt interactif** demande le stage
3. `mb-stage.yaml` créé à la racine
4. `/mb:validate "mon idée"` → entrée Discovery
5. Quand critères atteints, `stage-advisor` propose upgrade

### 10.3 Versioning du framework

- mb-framework v1 → tag `v1.x` sur main
- mb-framework v2 → développé sur branche `v2`, mergé en main quand stable
- Projets peuvent pin une version : `git submodule add -b v1 ...` ou `-b v2 ...`

---

## 11. Acceptance criteria (v2 ready to ship)

| # | Critère | Vérifiable par |
|---|---|---|
| AC1 | otoqi continue de fonctionner sans modif | Exécuter `/mb:feature` sur otoqi sans `mb-stage.yaml` → pipeline v1 inchangé |
| AC2 | Nouveau projet Discovery génère un go/no-go en < 2j | Test E2E sur projet bidon : `/mb:validate "idea"` → rapport produit |
| AC3 | Nouveau projet MVP shippe un wedge en < 48h | Test E2E : `/mb:ship "wedge"` → URL déployée |
| AC4 | Aucune section v1 supprimée | `git diff v1..v2 -- agents/*/SKILL.md` → seulement des additions |
| AC5 | `stage-advisor` détecte correctement les critères | Tests unitaires markdown : 4 cas (chaque transition) |
| AC6 | `install.sh` reste idempotent | Run 2x → pas d'erreur, pas de duplication symlinks |
| AC7 | Tous les nouveaux skills suivent le format v1 (frontmatter, interface, persona, rules) | Lint manuel sur les 4 nouveaux SKILL.md |

---

## 12. Risques & mitigations

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Régression sur otoqi (skill modifié casse un workflow) | Moyenne | Élevé | Tous les ajouts sont conditionnés par `mb-stage.yaml` présent. Default = v1 strict. |
| User confond les stages (marque MVP au lieu de PMF) | Moyenne | Moyen | `stage-advisor` montre les critères, suggère upgrade auto |
| Wedge-builder produit du code que le user ne veut pas refactor | Moyenne | Moyen | `kill_date` obligatoire en output. Stage upgrade force migration. |
| Trop de stages à maintenir | Faible | Moyen | 4 stages = limite haute. Pas d'ajout sauf besoin prouvé. |
| Skills early-stage non utilisés (overhead pour rien) | Moyenne | Faible | Symlinks créés mais pas chargés sauf si stage les active |
| Confusion v1/v2 dans la doc | Élevée | Faible | README.md indique clairement quel comportement par stage |

---

## 13. Out of scope (v3 ou plus tard)

- Pricing-advisor (suggéré dans brainstorming, écarté : sujet CEO)
- Launch-coordinator marketing (suggéré, écarté : sujet growth)
- Skills `_growth/` (retention-analyst, etc.) → ouvert pour v3 si besoin réel
- Multi-projet centralisé (un seul mb-framework piloté pour N projets) → v3
- Web UI pour stage management → v3
- Analytics auto sur les transitions de stage → v3

---

## 14. Décisions à valider AVANT impl

| # | Décision | Options | Recommandation |
|---|---|---|---|
| D1 | Branche dev | `v2` ou directement `main` ? | **`v2`** : permet tag v1 stable + dev parallèle |
| D2 | Format `mb-stage.yaml` | YAML simple ou avec history embarqué ? | **YAML simple** + `memory/stage-history.md` séparé |
| D3 | Comportement Scale par défaut sans yaml | Strict v1 OR opt-in stage_aware ? | **Strict v1** : zero risk pour otoqi |
| D4 | Naming `agents-early/` | `agents-early/`, `agents-stage/`, `agents/_early/` ? | **`agents-early/`** : explicite, lisible |
| D5 | Commande `/mb:validate` | Nouvelle commande OR alias `/mb:feature` en mode discovery ? | **Nouvelle commande** : intent clair |
| D6 | Wedge-builder skill | Vraiment skip TOUS les gates v1 ou garder verifier ? | **Skip tous sauf "deployed + 1 user tested"** |

---

## 15. Plan d'implémentation (à dérouler en phase code)

Sprint v2.1 (foundation)
1. Branche `v2` créée à partir de main
2. `mb-stage.yaml.template` + `mb-config.yaml` extension
3. `install.sh` modifié (prompt interactif + symlinks `agents-early/`)
4. `stage-advisor/SKILL.md` créé
5. Commande `/mb:stage` créée

Sprint v2.2 (orchestrator + skills extension)
6. `orchestrator/SKILL.md` : ajout Step 0.5 + Stage Routing Table + Stage Adaptation
7. Tous les skills v1 reçoivent leur section `## Stage Adaptation (v2)` (préservation stricte)
8. `templates/stages/` créé avec discovery + mvp + pmf + scale

Sprint v2.3 (early-stage skills)
9. `idea-validator/SKILL.md`
10. `user-interviewer/SKILL.md`
11. `wedge-builder/SKILL.md`
12. Commandes `/mb:validate` + `/mb:ship`

Sprint v2.4 (validation + docs)
13. Test E2E sur otoqi (rétro-compat AC1)
14. Test E2E sur Studio-IRIS (Discovery flow AC2)
15. Test E2E sur projet bidon (MVP flow AC3)
16. `docs/v2-migration.md` rédigé
17. `README.md` mis à jour
18. Tag `v2.0.0` + merge en main

---

## 16. Glossaire

- **Stage** : maturité du projet (Discovery, MVP, PMF, Scale)
- **Wedge product** : plus petit livrable testable par un user réel (concept YC)
- **TTFV** (Time To First Value) : délai entre début implem et premier user qui en tire valeur
- **DS UPDATE GATE** : Design System Update Gate (mb v1)
- **1-liner gate** : test "10 mots, pas de jargon, grandmother test" (YC)
- **Anti-Tarpit** : checklist YC contre les fausses bonnes idées
- **Janky** : code minimal, brut, assumé throwaway (Sheets + Zapier + script)
- **Kill date** : date de mort programmée d'un wedge product

---

**Fin du PRD v2. À valider avant passage à l'implémentation.**
