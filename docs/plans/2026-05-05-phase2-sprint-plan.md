# Phase 2 — Sprint Plan

**Auteur** : Yanick Mingala
**Date** : 2026-05-05
**Durée** : 18 jours ouvrés (~3.5 semaines), 6 sprints de 3 jours
**User principal** : Product Builder (solo-founder qui design + build + ship)
**Friction résolue** : Les utilisateurs ne peuvent pas agir depuis l'UI — dashboard read-only

---

## Vision

Transformer le dashboard en **cockpit du product builder** : voir, décider, lancer, valider — tout au même endroit sans quitter l'UI.

## Workflows cibles

1. **Décider quoi faire** — voir inbox + choisir le ticket à plus fort impact
2. **Shipper un quick win** — créer ticket → agent résout → valider → done
3. **Piloter un feature** — créer → plan → approve → implem → review → merge
4. **Mesurer l'avancement** — roadmap % + sprints livrés vs prévus
5. **Brainstorm avec l'agent** — chat → propositions → transformer en tickets
6. **Déléguer et oublier** — batch select → lancer → revenir valider

---

## Sprint 1 — CRUD Stories (jours 1-3)

**Use-case débloqué :** Le builder peut créer, éditer, et supprimer des tickets depuis l'UI.

| Item | Description |
|---|---|
| S1.1 | Backend CRUD endpoints (POST/PUT/DELETE /api/stories) + file locking |
| S1.2 | Formulaire création story (titre, description, priorité, statut) |
| S1.3 | Édition inline depuis la story modal |
| S1.4 | Suppression / archivage avec confirmation |
| S1.5 | Tests API + Playwright smoke |

**Livrable :** Le builder crée un ticket "fix: bouton cassé" depuis le dashboard.

**Exit criteria :**
- POST/PUT/DELETE stories fonctionnels
- Fichiers .md créés/modifiés atomiquement (pas de corruption)
- File locking empêche les écritures concurrentes
- 10+ tests API passing

---

## Sprint 2 — Kanban interactif (jours 4-6)

**Use-case débloqué :** Le builder déplace les tickets entre colonnes pour valider ou rejeter.

| Item | Description |
|---|---|
| S2.1 | Drag-and-drop entre colonnes kanban (HTMX + Sortable.js) |
| S2.2 | Endpoint PATCH /api/stories/{id}/status |
| S2.3 | Validation flow : bouton "Approve" / "Request changes" sur la modal |
| S2.4 | Voir le résultat (deliverable) avant de valider |
| S2.5 | Tests drag-drop + status transitions |

**Livrable :** Le builder ouvre un ticket "in_review", lit le résultat, clique "Approve" → done.

**Exit criteria :**
- Drag-drop fonctionne sur les 5 colonnes
- Status mis à jour dans le fichier .md après drop
- Deliverables affichés dans la modal (lecture de _bmad-output/)
- 8+ tests passing

---

## Sprint 3 — Vue Sprints (jours 7-9)

**Use-case débloqué :** Le builder voit l'historique des sprints et mesure l'avancement par phase.

| Item | Description |
|---|---|
| S3.1 | Modèle sprint (sprint.yaml ou frontmatter grouping) |
| S3.2 | Page /sprints — liste des sprints avec statut + items |
| S3.3 | Drill-down sprint → tickets associés + % complétion |
| S3.4 | Lien roadmap → sprints (quelle phase, quels sprints) |
| S3.5 | Créer/clôturer un sprint depuis l'UI |

**Livrable :** Le builder voit "Sprint 4 : 5/7 done, 2 in progress" et drill-down.

**Exit criteria :**
- Sprints stockés en YAML (source of truth)
- Page liste + page détail fonctionnelles
- Lien bidirectionnel roadmap ↔ sprint
- CRUD sprint (create/close) depuis l'UI
- 8+ tests passing

---

## Sprint 4 — Chat & état des lieux (jours 10-12)

**Use-case débloqué :** Le builder pose des questions et reçoit une synthèse projet en langage naturel.

| Item | Description |
|---|---|
| S4.1 | UI chat panel (input + message list + streaming) |
| S4.2 | Backend WebSocket ou SSE pour streaming réponse |
| S4.3 | Contexte injecté : stories, sprints, métriques courantes |
| S4.4 | Réponses structurées ("3 tickets bloqués, 2 en review, sprint à 60%") |
| S4.5 | Tests chat + réponses attendues |

**Livrable :** Le builder tape "état du sprint ?" → reçoit une synthèse live.

**Exit criteria :**
- Chat panel intégré au dashboard (slide-in ou page dédiée)
- Streaming SSE fonctionnel (pas de timeout)
- Contexte projet injecté automatiquement (pas de prompt manual)
- Réponses pertinentes sur état sprint/stories/blockers
- 6+ tests passing

---

## Sprint 5 — Actions depuis le chat (jours 13-15)

**Use-case débloqué :** Le builder crée des tickets et lance des actions via le chat.

| Item | Description |
|---|---|
| S5.1 | Intent detection : "crée un ticket pour..." → appel CRUD |
| S5.2 | Confirmation avant action ("Je vais créer : [titre]. OK ?") |
| S5.3 | "Lance ce ticket" → trigger agent pipeline (subprocess) |
| S5.4 | Feedback live : progression agent streamée dans le chat |
| S5.5 | Brainstorm mode : "propose 3 quick wins" → réponse + bouton "→ créer en ticket" |

**Livrable :** Le builder tape "fix le bug d'auth" → ticket créé + agent lancé → résultat streamé.

**Exit criteria :**
- Au moins 5 intents reconnus (create, status change, launch, list, brainstorm)
- Confirmation systématique avant mutation
- Agent lancé en subprocess, output streamé en SSE
- Bouton "créer en ticket" sur les suggestions
- 8+ tests passing

---

## Sprint 6 — Batch & délégation (jours 16-18)

**Use-case débloqué :** Le builder sélectionne plusieurs tickets et les lance/valide d'un coup.

| Item | Description |
|---|---|
| S6.1 | Multi-select sur le kanban (checkboxes) |
| S6.2 | Bulk status change (valider 3 tickets d'un coup) |
| S6.3 | "Lance ces 3 tickets" → agents parallèles |
| S6.4 | Vue résultats batch (progress bar par ticket) |
| S6.5 | Tests batch + concurrence |

**Livrable :** Le builder sélectionne 3 tickets → "lance" → revient voir 3 résultats terminés.

**Exit criteria :**
- Multi-select fonctionne (shift+click ou checkboxes)
- Bulk actions : move, archive, launch
- Agents parallèles avec isolation (pas de conflit fichier)
- Progress tracking per-ticket
- 6+ tests passing

---

## Résumé

| Sprint | Jours | Use-case débloqué | Dépendances |
|---|---|---|---|
| 1 | 1-3 | Créer / éditer / supprimer des tickets | — |
| 2 | 4-6 | Valider via kanban drag-drop | Sprint 1 (CRUD) |
| 3 | 7-9 | Voir les sprints + avancement roadmap | Sprint 1 (stories exist) |
| 4 | 10-12 | Chat pour état des lieux | Sprint 3 (sprint data) |
| 5 | 13-15 | Actions IA depuis le chat | Sprint 1 + 4 (CRUD + chat) |
| 6 | 16-18 | Batch & délégation multi-tickets | Sprint 2 + 5 (kanban + agent launch) |

## Stack technique

- **Backend** : FastAPI (existant) + endpoints CRUD + WebSocket/SSE
- **Frontend** : Jinja2 + HTMX (existant) + Sortable.js (drag-drop)
- **IA** : Claude API via Anthropic SDK (chat + intent detection)
- **Tests** : pytest + Playwright (existant)
- **Fichiers** : atomic writes + file locking (fcntl)

## Risques

| Risque | Mitigation |
|---|---|
| File locking complexe sur concurrent writes | fcntl advisory locks + retry |
| Drag-drop instable cross-browser | Sortable.js bien supporté, fallback boutons |
| Coût API Claude pour le chat | Rate limiting + cache réponses métriques |
| Agent subprocess qui hang | Timeout 5 min + kill |
