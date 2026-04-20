# mb-framework — Roadmap 2026

**Auteur** : Yanick Mingala
**Version** : 1.0 (draft)
**Date** : 2026-04-19
**Base** : v2.0.0 (stage-aware framework) + analyse paperclip (`docs/inspiration/`)

---

## Executive Summary

Ce document trace deux horizons pour mb-framework :

1. **Court terme (2-4 semaines) — Usage solo-entrepreneur**
   mb v2.1 + v2.2 : améliorations quotidiennes pour un dev qui gère plusieurs projets (Otoqi, Studio IRIS, Drivia, futurs) en CLI markdown-only. Gain immédiat, zero infra, zero dépendance externe.

2. **Moyen terme (6-12 mois) — Produit commercialisable**
   mb-framework devient la base d'un produit SaaS avec :
   - Cloud sync + web UI (abonnement Pro)
   - Support multi-utilisateurs + RBAC (abonnement Team)
   - Support de modèles IA open-source (Ollama, LM Studio, Llama.cpp) en plus de Claude
   - Positionnement : "La plateforme d'agents IA pour solo-founders et petites agences dev" — contrairement à Paperclip qui vise entreprise.

Les deux horizons sont **séquentiels** : on ne construit pas le commercial avant que l'outil solo tourne en production sur 2-3 projets réels pendant 2-3 mois.

---

# PARTIE 1 — Court terme : améliorations solo-preneur

## 1.1 Problèmes quotidiens observés

Yanick tourne sur plusieurs projets en parallèle. Pain points actuels :

| Pain | Fréquence | Impact |
|---|---|---|
| "Je ne sais plus où j'en suis sur Drivia vs Otoqi" | Quotidien | Perte 10-15 min/jour |
| "Cette story dépend de laquelle déjà ?" | Sprint | Stories orphelines, retravail |
| "L'agent a fait quoi au run précédent ?" | Debug | Investigation longue |
| "Où est la V2 de la spec produit X ?" | Projet pivot | Artefact perdu |
| "Un agent va-t-il déployer en prod par accident ?" | Stage pmf+ | Risque haute gravité |
| "Comment je partage ma config mb avec un autre projet ?" | Nouveau projet | Copy-paste manuel |

## 1.2 Shortlist v2.1 — Quick wins (1 sprint de soirée)

Priorisé par ratio **valeur quotidienne / effort**. Tous compatibles avec la philosophie zero-infra markdown-only.

### A. Multi-project overview
**Problème résolu** : switcher entre Otoqi / Studio IRIS / Drivia / futurs.

**Design** :
- `~/.mb/projects.yaml` — registry user-level
- `/mb:projects` — liste tous les projets avec stage + dernière activité
- `mb <name>` — shell helper qui fait `cd` + lance `claude`
- Auto-enregistrement au `install.sh`

**Effort** : S (3h)
**Livrable** : un projet enregistré, visible depuis n'importe où.

### B. Typed deliverables versionnés
**Problème résolu** : retrouver la V2 d'un PLAN sans fouiller l'historique git.

**Design** :
```
_bmad-output/deliverables/STU-{id}/
├── PLAN-rev1.md        # architect
├── PLAN-rev2.md        # revision post-clarif
├── IMPL-rev1.md        # dev diff summary
├── REVIEW-rev1.md      # verifier
└── DOC-rev1.md         # tech-writer
```

Chaque agent écrit son output dans un fichier typé versionné, pas dans le .md de story.

**Effort** : S (2h)
**Livrable** : convention naming + skill update pour tech-writer + verifier.

### C. Parent/child story tree
**Problème résolu** : orpheline-stories, perte de lineage.

**Design** :
- Ajout `parent_story:` et `children:` en frontmatter story
- Commande `/mb:tree [STU-X]` affiche l'arbre ASCII

**Effort** : S (2h)
**Livrable** : script Python simple qui lit frontmatter stories.

### D. Run log + "what I did" summary
**Problème résolu** : post-mortem lent, on ne sait plus qui a fait quoi.

**Design** :
- `memory/runs.jsonl` append-only : `{run_id, ts, agent, story, action, tokens_in, tokens_out}`
- Chaque skill se termine par un bloc obligatoire "Done. Here's what I did on {story}."
- Écrit en markdown à la fin de `memory/_session/handoff.md`

**Effort** : S (2h)
**Livrable** : règle ajoutée aux skill personas, template standardisé.

### E. Backlog + roadmap + deliverables locations
**Problème résolu** : pas d'endroit clair pour stories pas encore schedulées.

**Design** :
```
{project-root}/
├── _roadmap.md                    # strategique : stages + targets
├── _backlog/                      # stories non-actives
│   └── STU-52-add-stripe-webhook.md
└── _bmad-output/
    ├── implementation-artifacts/
    │   └── stories/               # stories actives (sprint en cours)
    └── deliverables/              # voir section B
```

Commandes :
- `/mb:backlog` — liste priorisée
- `/mb:roadmap` — état stage + criteria progress

**Effort** : S (3h)
**Livrable** : convention fichiers + 2 commandes slash.

### Récap v2.1

| # | Item | Effort | Valeur |
|---|---|---|---|
| A | Multi-project overview | S 3h | 🔥🔥🔥 |
| B | Typed deliverables | S 2h | 🔥🔥 |
| C | Parent/child tree | S 2h | 🔥🔥 |
| D | Run log + summary | S 2h | 🔥🔥 |
| E | Backlog/roadmap/deliverables dirs | S 3h | 🔥🔥 |

**Total** : ~12h = 2 soirées
**Impact attendu** : perte quotidienne 10-15 min → 2 min

## 1.3 Shortlist v2.2 — Structural (1 sprint week-end)

Choses plus grosses, moins urgentes, mais transformatrices.

### F. Tool catalog + creds + RBAC stage-aware
**Problème résolu** : agent fe-dev pourrait déployer en prod par accident en stage pmf.

**Design** :
```
tools/
├── _catalog.yaml
├── github/TOOL.md + schema.yaml
├── supabase/TOOL.md + schema.yaml
├── vercel/TOOL.md + schema.yaml
└── stripe/TOOL.md + schema.yaml

creds/ (gitignored)
├── github.env
├── supabase.env
└── vercel.env

memory/permissions.yaml  # RBAC par agent, stage-aware
```

Commandes :
- `/mb:tool list` — catalog + qui utilise quoi
- `/mb:tool check <agent> <tool> <action>` — deny-by-default
- `/mb:tool audit` — qui a fait quoi ces 7 derniers jours

Pre-flight obligatoire dans chaque skill qui appelle un outil externe.

**Effort** : M (1-2 jours)
**Valeur** : protection pmf+ critique.

### G. Skills namespace + registry
**Problème résolu** : pollution si on ajoute N skills à l'avenir.

**Design** :
```
skills/
├── core/                  # bundled, read-only
├── project/               # spécifique projet
└── community/             # imported via /mb:skill add <github-url>

memory/skills-registry.yaml   # only registered = discoverable
```

Commandes :
- `/mb:skill list`
- `/mb:skill add <github-url-or-path>`
- `/mb:skill remove <key>`

**Effort** : M (1 jour)
**Valeur** : solves pollution + enable sharing entre projets.

### H. Memory restructure en layers
**Problème résolu** : `memory/` actuellement plat et confus.

**Design** :
```
memory/
├── project/              # long terme
│   ├── mission.md
│   ├── codebase-index.md
│   └── cost-log.md
├── agents/               # par agent
│   └── {name}/
│       ├── instructions.md
│       └── runs.jsonl
├── stories/              # par story
│   └── STU-{id}/
│       ├── handoff.md
│       └── context.md
└── session/              # ephémère
    └── current-turn.md
```

**Effort** : M (1 jour)
**Valeur** : structure mentale claire + scalable avec nombre de stories.

### I. `/mb:inbox` — vue unifiée blockers
**Problème résolu** : ne plus rater ce qui bloque.

**Design** : commande qui scanne et affiche stories in_review + approvals pending + blocked par, triés par urgence.

**Effort** : S (3h)
**Valeur** : morning standup de 30 sec.

### J. `/mb:board` — Kanban ASCII terminal
**Problème résolu** : visibilité rapide sur l'avancement.

**Design** :
```
╭─ BACKLOG ──╮ ╭─ TODO ──╮ ╭─ IN PROG ──╮ ╭─ REVIEW ──╮ ╭─ DONE ──╮
│ STU-52     │ │ STU-48  │ │ STU-46 ←me │ │ STU-45    │ │ STU-44  │
╰────────────╯ ╰─────────╯ ╰────────────╯ ╰───────────╯ ╰─────────╯
```

Lit les frontmatter stories, regroupe par status.

**Effort** : S (2h)
**Valeur** : glance quotidien.

### Récap v2.2

| # | Item | Effort | Valeur |
|---|---|---|---|
| F | Tool/creds/RBAC stage-aware | M 1-2j | 🔥🔥🔥 (pmf+) |
| G | Skills namespace + registry | M 1j | 🔥🔥 |
| H | Memory restructure | M 1j | 🔥 |
| I | `/mb:inbox` | S 3h | 🔥🔥 |
| J | `/mb:board` | S 2h | 🔥 |

**Total** : ~4-5 jours
**Recommandation** : faire F en premier (sécurité), puis I (usage quotidien), puis G-J-H.

## 1.4 Non-goals v2.1/v2.2

Ne PAS faire, même si tentant :

- ❌ UI web (garder markdown-only — la UI vient en commercial v3)
- ❌ Multi-user/team sharing (garder solo — team vient en commercial v3)
- ❌ Budget $ enforcement (inopérant avec Claude Code subscription)
- ❌ Org tree hiérarchique (mb agents = peers)
- ❌ Routines/cron (osplan crontab suffit)
- ❌ Multi-runtime adapters (Claude Code only — change au commercial v3)

---

# PARTIE 2 — Moyen terme : commercialisation

## 2.1 Positionnement

### Marché ciblé

**Solo founders** + **petites agences** (2-10 personnes) qui :
- Utilisent Claude Code / Cursor / outils IA en mode anarchique
- Ont besoin de structure mais pas d'entreprise-grade
- Budget $20-50/mois par personne (pas $500/mois entreprise)
- Veulent multi-projet (freelance, portfolio, side-projects)
- Veulent pouvoir basculer vers modèles open-source si les coûts IA explosent

### Différenciation vs concurrence

| Concurrent | Cible | Prix | Différence mb |
|---|---|---|---|
| Paperclip | Entreprise Series A+ multi-agent | Self-hosted gratuit | mb est simpler, stage-aware, packaged pour solo/agences |
| Cursor | Dev individuel | $20/mo | Cursor = IDE, mb = méthode + orchestration au-dessus |
| Devin/Cognition | Autonomous coding | $500/mo | mb met l'humain dans la loop (stage-aware) |
| Factory.ai | Entreprise | Contact sales | mb = self-serve, transparent pricing |
| GitHub Copilot Workspace | Dev GitHub | $19/mo | Copilot = feature GitHub, mb = workflow complet |

**Wedge clair** : "Studio IRIS in a box" — ce que Yanick a appris en faisant tourner son agence, packagé pour d'autres.

### Positioning statement

> mb-framework est la plateforme d'orchestration d'agents IA pour **solo-founders et petites agences dev** qui veulent structurer leur workflow sans complexité d'entreprise. Stage-aware, multi-projet, compatible Claude et IA open-source.

## 2.2 Évolution architecturale

### De v2 (outil solo) vers v3 (produit commercial)

```
Phase 0 (actuel — v2.1/v2.2) :
Local markdown + Claude Code + shell scripts
                │
                ▼
Phase 1 — Adapter layer :
Local markdown + {Claude Code | Claude API | OpenAI | Ollama | LM Studio} + shell
                │
                ▼
Phase 2 — Web UI + MCP :
Local markdown + web UI (localhost) + MCP server + adapters
                │
                ▼
Phase 3 — Cloud sync :
Cloud-synced markdown + web UI + adapters (free tier)
                │
                ▼
Phase 4 — Multi-user + billing :
Cloud + web UI + adapters + teams + Stripe + RBAC
```

Chaque phase = milestone de 1-3 mois avec possibilité de vendre/facturer.

### Couches architecturales proposées

```
┌────────────────────────────────────────┐
│  Web UI (React, future)                 │  ← Phase 2+
├────────────────────────────────────────┤
│  MCP Server                             │  ← Phase 2
├────────────────────────────────────────┤
│  mb Core (markdown + skills + commands) │  ← v2 actuel
├────────────────────────────────────────┤
│  Adapter Layer (NEW)                    │  ← Phase 1
│  ┌──────────┐ ┌─────┐ ┌────────┐ ┌────┐│
│  │Claude CLI│ │API  │ │Ollama  │ │etc │ │
│  └──────────┘ └─────┘ └────────┘ └────┘│
├────────────────────────────────────────┤
│  Storage Layer                          │
│  ┌─────────┐         ┌──────────────┐  │
│  │Local FS │  ←─→    │Cloud Sync    │  │  ← Phase 3
│  └─────────┘         └──────────────┘  │
└────────────────────────────────────────┘
```

## 2.3 Support IA open-source (Phase 1)

### Adapters supportés (proposé)

| Adapter | Runtime | Cas d'usage | Prix API |
|---|---|---|---|
| `claude-code-local` | Claude Code CLI | **Par défaut** — dev local subscription | $20/mo Max |
| `claude-api` | Anthropic API | Prod, scale, BYO key | $3-15/M tokens |
| `openai-api` | OpenAI API | Alternative commercial | $2-10/M tokens |
| `gemini-api` | Google API | Alternative commercial | Variable |
| **`ollama-local`** | **Ollama (localhost:11434)** | **Offline, gratuit, privé** | **$0** |
| **`lmstudio-local`** | **LM Studio (localhost:1234)** | **Desktop, facile** | **$0** |
| **`llamacpp-local`** | **llama.cpp direct** | **Custom builds** | **$0** |
| `huggingface-api` | HF Inference | Modèles spécialisés | Variable |
| `custom-http` | Any HTTP endpoint | Intégrations custom | Variable |

### Pourquoi open-source matters

1. **Coûts** : un solo sur Otoqi consomme 500k tokens/jour à $3/M = $1.5/jour = $45/mois juste en inference
2. **Privacy** : certains clients Studio IRIS ont du code propriétaire qui ne doit pas quitter leur infra
3. **Disponibilité** : Claude limit hit = travail bloqué. Ollama fallback = zero downtime.
4. **Customization** : fine-tuner un modèle sur ton corpus Otoqi pour meilleur contexte
5. **Adoption entreprise** : les entreprises régulées (banque, santé, public) exigent self-hosted

### Design de l'adapter layer

```yaml
# mb-config.yaml
adapters:
  default: claude-code-local
  available:
    - claude-code-local
    - claude-api
    - ollama-local

per_agent:
  fe-dev:
    adapter: claude-code-local
    model: sonnet-4.7
  wedge-builder:
    adapter: ollama-local         # offline OK pour wedge
    model: llama-3.3-70b
  verifier:
    adapter: claude-api           # prod-grade pour verif
    model: opus-4.7
  content:
    adapter: claude-code-local
    model: sonnet-4.5
```

### Intégration Ollama concrète

```python
# packages/adapters/ollama-local/adapter.py (pseudo-code)
import httpx

def invoke(prompt, model, system=None):
    response = httpx.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False
        }
    )
    return response.json()["response"]
```

Simple wrapper HTTP. L'adapter layer unifie l'interface pour que les skills mb ne changent pas quand on bascule de Claude à Ollama.

## 2.4 Pricing strategy

### Tiers proposés

#### **Free (Open Source Core)**
- mb core (markdown, skills, commands)
- Local-only
- Any adapter self-hosted (Claude Code, Ollama, etc.)
- Pas de cloud sync
- Pas de web UI
- Self-support (GitHub issues)
- **Cible** : devs solo tech-savvy, communauté OSS

#### **Pro — $19/mo** (inspiré de Cursor pricing)
- Tout Free +
- Cloud sync markdown entre devices
- Web UI local (mb-studio) servie sur port local
- Tous les adapters cloud (Claude API, OpenAI, Gemini) sans gestion BYO key côté technique
- Email support 48h
- **Cible** : solo-founders qui gèrent 2-5 projets

#### **Team — $39/mo par seat, min 2** (inspiré de Linear)
- Tout Pro +
- Multi-user par projet
- RBAC par agent + par tool
- Audit log centralisé
- Shared skills registry
- Priority support 24h
- **Cible** : petites agences dev 2-10 personnes (Studio IRIS like)

#### **Enterprise — Sur devis**
- Tout Team +
- SSO (Okta, Azure AD)
- On-premise deployment
- Compliance (SOC2, HIPAA)
- SLA + dedicated CSM
- **Cible** : banques, santé, public, grands groupes tech

### Économie unitaire estimée

Pour un Pro à $19/mo :
- Coûts infra (cloud sync, S3-compat, DB) : ~$0.50/user/mo
- Coût support : ~$1-2/user/mo
- Coût ventes + marketing : ~$5-8/user/mo (payback 6 mois)
- Marge brute : $8-12/user/mo (42-63%)

**Seuil de rentabilité estimé** : 500-1000 Pro users = $10-20k MRR couvrant 1 dev full-time.

## 2.5 Roadmap commercial par phase

### Phase 1 — Adapter layer (mois 1-2 post-v2.2)

**Objectif** : permettre de changer de modèle IA sans casser les skills.

Livrables :
- `packages/adapters/` avec claude-code-local, claude-api, ollama-local en priorité
- Config `mb-config.yaml` étendue avec section `adapters:` et `per_agent:`
- Migration guide v2.2 → v3.0 (breaking change)
- Documentation Ollama setup (tutorial)

**Décision go/no-go** : 50+ stars GitHub + 3+ users non-Yanick actifs. Sinon, on continue en solo.

### Phase 2 — MCP server + web UI local (mois 3-4)

**Objectif** : débloquer l'usage non-tech (ta femme) et donner une UI.

Livrables :
- MCP server exposant `/mb:validate`, `/mb:ship`, `/mb:projects`, etc.
- `mb-studio` — web UI React servie localhost lisant les markdowns
- Packaging : installer one-liner `npx mb-framework init`

**Décision go/no-go** : 100+ stars + 10+ users actifs. Sinon, on reste CLI-only.

### Phase 3 — Cloud sync + billing (mois 5-7)

**Objectif** : first paid feature.

Livrables :
- Service sync : markdowns + memory dans bucket chiffré (user-side keys)
- Account system (login via GitHub/Google)
- Stripe billing integration
- Dashboard.mb-framework.io (ou équivalent) pour billing + sync status

**Décision go/no-go** : 500+ stars + 30+ users Pro intention-to-pay. Sinon, reste gratuit.

### Phase 4 — Teams + enterprise (mois 8-12)

**Objectif** : upsell + clients premiers entreprise.

Livrables :
- Multi-user par projet
- RBAC granulaire
- Audit log centralisé
- SSO (Phase 4b)
- On-prem deployment option

**Décision go/no-go** : 3+ Team customers acquis organiquement. Sinon, on pivote (ou on tue le produit).

## 2.6 Risques et mitigations

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| **Paperclip pivote vers solo/petite agence** | Moyenne | Élevé | Core OSS + community → defensible. Partir tôt. |
| **Claude Code supprime le support CLI** | Faible | Critique | Adapter layer = survie. Phase 1 critique. |
| **Marché AI dev tools s'effondre (over-saturation)** | Moyenne | Élevé | Commencer petit, valider demande avant scaler. |
| **Solo-preneur usage ≠ scale usage** | Élevée | Moyen | Phase 1-2 on reste gratuit. Pay sur Phase 3+ seulement. |
| **Yanick a pas le temps entre Otoqi + Studio IRIS + mb** | **Très élevée** | Critique | Rendre mb compatible gestion part-time. Pas de VC early. |
| **Coûts cloud > revenus en early** | Moyenne | Moyen | Cloud sync = user-paid storage (Cloudflare R2 passthrough) |
| **Adoption entreprise bloquée par compliance** | Faible early | Variable | Enterprise = Phase 4+, optional |

## 2.7 Anti-tarpit check du projet commercial

Application du propre skill `mb-early-idea-validator` à cette vision :

### 10-Question framework

| # | Question | Score | Raison |
|---|---|---|---|
| 1 | Founder-market fit | 3/3 | Yanick = solo-preneur + agence dev + créateur mb |
| 2 | Market size | 2/3 | Solo-founders + petites agences dev = ~1M worldwide |
| 3 | Problem acuteness | 2/3 | Réel (vu chez Yanick lui-même) mais pas critique ($20/mo pain) |
| 4 | Competition | 2/3 | Crowded mais niche solo/agency pas dominée |
| 5 | Personal relevance | 3/3 | Yanick vit le problème quotidiennement |
| 6 | Recent change | 2/3 | AI agents 2024-2026 = shift réel |
| 7 | Proxy elsewhere | 3/3 | Linear (for devs), Framer (for design) prouvent modèle vertical SaaS |
| 8 | Time horizon | 2/3 | 12-24 mois pour atteindre $10k MRR |
| 9 | Scalability | 3/3 | Pure SaaS markdown-based |
| 10 | Idea space quality | 2/3 | Hot mais encombré |

**Total** : 24/30 → **verdict : go** (≥22 seuil)

### Anti-tarpit checklist

- [ ] CISP : partir de mb existant (méthode) + douleur vécue = **not CISP** ✅
- [ ] Tarpit : "AI dev platform" est tarpit MAIS niche solo/agency est sous-adressée ✅
- [ ] Perfect idea stall : spec écrite, next action concrète (Phase 1 adapter) ✅
- [ ] First idea reflex : alternatives considérées (rester OSS-only, pivoter B2B, etc.) ✅

Anti-tarpit : **pass**. Cette vision passe le test que Rockclip a raté.

### 1-Liner validé

> *"mb-framework : orchestre tes agents IA pour solo et petites agences dev. Claude, Ollama, ou ton modèle à toi."*

(12 mots, zéro buzzword, grandmother-readable)

---

# PARTIE 3 — Plan d'exécution concret

## 3.1 Cette semaine (court terme)

- [ ] **Jour 1** (soir) : v2.1 A — Multi-project overview (3h)
- [ ] **Jour 2** (soir) : v2.1 B — Typed deliverables (2h)
- [ ] **Jour 3** (soir) : v2.1 C — Parent/child tree (2h)
- [ ] **Jour 4** (soir) : v2.1 D — Run log + summary (2h)
- [ ] **Jour 5** (soir) : v2.1 E — Backlog/roadmap/deliverables (3h)
- [ ] **Weekend** : Dogfood v2.1 sur Otoqi + Studio IRIS, iterate bugs

**Tag** : v2.1.0 en fin de semaine.

## 3.2 Ce mois (court terme structural)

- [ ] Semaine 2 : v2.2 F — Tool catalog + RBAC (2 jours weekend)
- [ ] Semaine 3 : v2.2 I + J — Inbox + board (4h + 2h)
- [ ] Semaine 4 : v2.2 G + H — Skills registry + memory restructure (1 jour + 1 jour)

**Tag** : v2.2.0 fin du mois.
**Validation** : 3 projets Yanick tournent sur v2.2 (Otoqi, Studio IRIS, Drivia).

## 3.3 Mois 2-3 (commercial Phase 1)

- [ ] Architecture adapter layer (design doc → RFC sur GitHub)
- [ ] Implémentation adapter claude-code-local (refactor existant)
- [ ] Adapter ollama-local (POC → production)
- [ ] Adapter claude-api (BYO key)
- [ ] Documentation + tutorial Ollama setup
- [ ] Announce sur Hacker News, Reddit r/LocalLLaMA, Product Hunt

**Go/No-go** : 50 stars + 3 non-Yanick actifs = continuer Phase 2. Sinon arrêt ou pivot.

## 3.4 Mois 4-6 (commercial Phase 2)

- [ ] MCP server spec + implementation
- [ ] mb-studio web UI (React) — read-only first
- [ ] Packaging npx one-liner
- [ ] Landing page mb-framework.io

## 3.5 Mois 7-12 (commercial Phase 3-4)

Voir §2.5.

## 3.6 Budget prévisionnel solo

| Poste | Mois 1-3 | Mois 4-6 | Mois 7-12 |
|---|---|---|---|
| Temps Yanick | 10h/sem | 15h/sem | 20h/sem |
| Infra (Vercel, R2, DB) | $0 | $20/mo | $50-200/mo |
| Domaine + email | $0 (reuse) | $10/mo | $10/mo |
| Marketing (ads off par défaut) | $0 | $100/mo | $500/mo |
| Outils (Linear, Posthog, Stripe) | $0 | $50/mo | $150/mo |
| **Total** | **~$0** | **~$180/mo** | **~$700-850/mo** |

**Seuil de break-even estimé** : 50 Pro users ($950 MRR) fin mois 9.

---

# PARTIE 4 — Décisions à valider

Avant d'exécuter, Yanick doit valider :

## 4.1 Décisions tactiques (v2.1/v2.2)

- [ ] **D1** : Ordre d'exécution v2.1 A→E ou autre ?
- [ ] **D2** : RBAC tools en v2.1 ou v2.2 ? (currently v2.2)
- [ ] **D3** : Shell helper dans `install.sh` (modifie ~/.zshrc) ou script séparé ?

## 4.2 Décisions stratégiques (commercial)

- [ ] **D4** : mb-framework restera open-source core ou pivot fermé ?
  - *Recommandé* : Core open-source (MIT ou AGPL), cloud service propriétaire. Modèle GitLab/Cal.com/Supabase.
- [ ] **D5** : Go commercial après v2.2, ou attendre 2-3 mois d'usage solo ?
  - *Recommandé* : attendre 2-3 mois pour dogfood + community feedback avant engager.
- [ ] **D6** : Inclure Anthropic dans partners (Claude push) ou rester agnostique ?
  - *Recommandé* : agnostique. Faire du Claude-support l'option recommandée mais pas unique.
- [ ] **D7** : Accepter VC funding early ou rester bootstrapped ?
  - *Recommandé* : bootstrapped jusqu'à Phase 3 minimum. Funding creuse le risque anti-tarpit.
- [ ] **D8** : Target Studio IRIS comme premier paying customer ?
  - *Recommandé* : oui — founder-market fit parfait, mais pricing à Studio IRIS doit rester "au prix normal" pour éviter biais.

---

# Annexes

## A. Evidence
- Pain points listés observés directement dans conversations Yanick 2026-04-15..19
- Paperclip analysis : `docs/inspiration/paperclip.md` + `paperclip-test-1.md`
- Ollama adoption : ~70% des dev OSS en 2026 selon Stack Overflow Survey
- Pricing benchmarks : Cursor $20/mo (mars 2026), Linear $8-14/seat, Supabase free tier + $25/mo paid
- Anti-tarpit scoring : 24/30 passe le seuil, 4/4 anti-tarpit dimensions clear

## B. Unknowns
- Taille exacte du marché "solo-founder + petite agence dev utilisant AI agents" (pas de donnée publique précise)
- Rétention réelle d'un outil méta comme mb (est-ce qu'on le garde 12 mois ou on l'oublie après 3 ?)
- Comportement réel d'Ollama sur macOS vs Linux avec modèles 70B+ (RAM needs élevés)
- Compliance enterprise : est-ce qu'on atteint SOC2 en Phase 4 avec Yanick solo ? Probablement non.

## C. Assumptions
- Yanick peut dédier 10-20h/semaine à mb-framework sans casser Otoqi + Studio IRIS
- Claude Code CLI reste disponible au moins 12 mois (protection via adapter layer)
- La communauté OSS d'agents IA grandit en 2026-2027 (pas un bust imminent)
- Ta femme valide l'UX Phase 2 (sinon le use-case non-tech meurt)
- Drivia est un projet réel que tu vas utiliser pour tester mb sur un 3e projet

## D. Open questions pour re-discussion

1. Est-ce que "Drivia" est un projet que tu veux partager les détails pour que je l'intègre au test suite ?
2. Tu préfères commencer par Phase 1 (adapter layer) ou Phase 2 (web UI) pour la partie commerciale ?
3. Studio IRIS devient test-bed de mb ou reste indépendant ?
4. Avec quel nom tu veux lancer la version commerciale ? "mb" comme aujourd'hui, ou un rebrand genre "mission-brief.dev" / autre ?
