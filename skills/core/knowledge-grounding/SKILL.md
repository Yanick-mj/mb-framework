---
name: core/knowledge-grounding
description: All recommendations cite verifiable sources following a strict tier hierarchy. Foundational work allowed when still canonical. Never invent citations.
version: 1
used_by: [fe-dev, be-dev, lead-dev, architect, pm, sm, verifier, tea, devops, quick-flow, tech-writer, ux-designer, orchestrator]
---

## Why this exists

Without a source hierarchy, agents drift to "common practice" — a noisy mix of
Medium articles, Substack newsletters, conference takes, and opinionated blog
posts. The output looks competent but fails on rigor.

The user's contract is explicit:
- The agent applies rigorous, citable knowledge from established sources.
- The user supplies judgment, taste, project context, and real-world feel.

This skill is consumed by an LLM at composition time. Rules are pattern-match
friendly, not prose-heavy.

## Source hierarchy (priority order)

For every recommendation, principle, or "how things should be done" claim,
pick the highest available tier.

### Tier 1 — Academic / Standards

- Peer-reviewed papers — cite: author + year + venue + DOI / arXiv ID
- Established academic textbooks — cite: author + title + year + edition
- Official standards bodies: W3C, IETF (RFCs), ISO, IEEE, NIST, ACM, ETSI
- Government / public research: NIST publications, INRIA, NSF-funded papers,
  EU H2020 / Horizon outputs
- University course material from canonical authors at top-tier programs
  (CMU, MIT, Stanford, Berkeley, ETH, Oxford, Cambridge)

### Tier 2 — World-class industry leaders (published)

- Engineering documentation from Tier-1 engineering organizations:
  Meta Engineering, Google Research, AWS Architecture Center,
  Stripe Engineering, GitHub Engineering, Cloudflare Blog,
  Netflix TechBlog, Microsoft Research, Shopify Engineering
- Books by recognized senior practitioners with sustained influence:
  Beck, Martin, Fowler, Norman, Nielsen, Krug, Hickey, Kleppmann,
  Skelton & Pais, Reinertsen, Humble & Farley
- Engineering RFCs from major OSS projects: Rust RFCs, React RFCs,
  Python PEPs, IETF drafts, Linux kernel mailing list discussions
- Named-author research firm reports: ThoughtWorks Tech Radar,
  DORA / Forsgren reports, JetBrains State of Developer Ecosystem,
  Stack Overflow Developer Survey (raw data only, not editorial)

### Tier 3 — GAFAM repos + tools (empirical, production code)

- Source code of major OSS projects from Google / Apple / Meta / Amazon /
  Microsoft and adjacent orgs at equivalent scale:
  Kubernetes, TensorFlow, PyTorch, React, TypeScript, Bazel, Swift, WebKit,
  VS Code, .NET runtime, Folly, Abseil, gRPC, Protobuf, etc.
- Cite by: repo URL + release tag OR commit SHA + relevant file path
  Example: `github.com/facebook/react @ v19.1.0, packages/react-reconciler/src/ReactFiberWorkLoop.js`
- Use Tier 3 for "what they actually run in production", which is stronger
  evidence than blog posts about what they say they run.
- Verify the repo is actively maintained (last commit < 6 months) before
  citing; abandoned forks lose Tier 3 status.

### NEVER cite

- Anonymous Medium / Substack / dev.to / Hashnode posts
- LinkedIn posts
- Reddit / HackerNews / Stack Overflow comments
- Personal blogs without academic or recognized-practitioner authorship
- Conference talks without an accompanying published paper or
  open-source artifact
- AI-generated content (including this assistant's prior outputs)
- Vendor marketing material from companies selling the recommended solution

## Stay-current principle

The goal is to apply the field's CURRENT understanding, not to artificially
exclude foundational work. For each citation, apply this test:

> "Would a senior staff engineer or principal designer cite this source
> in 2026?"

- If yes → cite it, regardless of age.
- If no → look for a more recent canonical source.
- If you are unsure → mark UNKNOWN about the current state of the field.

When citing foundational work, acknowledge significant evolution if you
know of it:

- Brewer 2000 (CAP theorem) → note Abadi 2012 PACELC extension
- Norman 1988 (Design of Everyday Things) → note Norman 2013 revised ed
- Beck 2002 (TDD by Example) → note recent meta-analyses if you know any
- Fitts 1954 (Fitts's Law) → note touch-screen extensions (MacKenzie & Buxton)

When the field moves fast (frontend tooling, AI/LLMs, cloud infra), prefer
recent sources:

- Frontend / AI: prefer last 2-3 years
- Cloud infra / DevOps: prefer last 5 years
- Foundational CS / theory: age does not matter if still canonical

State publication year explicitly. If only old sources are available,
flag this and mark UNKNOWN about whether the finding is still considered
current.

## Citation format (examples for pattern matching)

### Tier 1

> Use eventual consistency for this multi-region write path. (Source:
> Brewer 2000, "Towards Robust Distributed Systems", PODC keynote;
> Gilbert & Lynch 2002 formalization, ACM SIGACT News 33(2),
> DOI 10.1145/564585.564601. Refinement: Abadi 2012, "Consistency
> Tradeoffs in Modern Distributed Database System Design",
> IEEE Computer 45(2).)

### Tier 2

> Apply progressive disclosure to reduce cognitive load on the form.
> (Source: Nielsen 2006, "Progressive Disclosure", NN/g article;
> foundational basis: Sweller 1988, "Cognitive Load During Problem
> Solving", Cognitive Science 12(2), DOI 10.1207/s15516709cog1202_4.)

### Tier 3

> Use this concurrency primitive for futures composition. (Source:
> github.com/facebook/folly @ release v2024.10.07, file
> folly/futures/Future.h — production-grade implementation in
> widespread internal use at Meta, last commit <6 months ago.)

## Anti-hallucination clause (CRITICAL)

LLMs invent plausible-sounding citations. This is the most common failure
mode of this skill. Hard rule:

If you cannot recall a source's identifying details (title, author, year,
venue, DOI, or repo URL with commit/tag) with HIGH confidence:

→ write UNKNOWN
→ do NOT approximate
→ do NOT guess at author names or paper years
→ do NOT invent DOIs

An honest UNKNOWN beats an invented "Smith et al. 2019".

### Correct behavior

> "I recall research on the working memory limit around 7±2 chunks
> (Miller 1956, 'The Magical Number Seven, Plus or Minus Two',
> Psychological Review 63(2)), later refined toward ~4 chunks. I do not
> remember the exact citation for the 4-chunk refinement with high
> confidence. Tier 1 partial: Miller 1956. UNKNOWN: contemporary update
> — please verify with Cowan's work if needed."

### Forbidden behavior

> "Cowan (2017) showed that working memory holds 4 ± 1 items..."
> (when you are not certain this exact citation exists)

> "Smith et al. 2019 demonstrated..." (when you cannot identify Smith
> or the paper title)

## When no source exists at any tier

State the recommendation as ASSUMPTION (max 2 per response per the
evidence-rules skill) and explicitly label it as opinion / heuristic, not
grounded in literature. Let the user decide whether to proceed.

> ASSUMPTION (heuristic, not grounded): For a 5-person solo studio, I
> would suggest skipping formal A/B testing in favor of qualitative
> feedback from 3-5 users. No Tier 1/2/3 source addresses this exact
> scale. Treat as opinion.

## Limits to surface to the user

When relevant, state explicitly:

1. **LLM training cutoff** — your knowledge has a cutoff date. For
   "what's current in 2025-2026", you may miss recent publications. Mark
   UNKNOWN when uncertain about the current state of fast-moving fields.

2. **Replication crisis** — pre-2015 psychology / UX findings often failed
   to replicate (ego depletion, power posing, Stanford prison
   interpretation, several priming effects). When citing classic
   psych/UX work, flag with "REPLICATION CONCERN: finding challenged by
   [meta-analysis if known]" if you suspect the finding has been
   contested.

3. **Field velocity** — frontend, AI/LLM, cloud infra publish faster than
   academia. Tier 1 sources lag 2-3 years on these. Tier 2/3 may
   dominate. State this when it applies.

## Interaction with evidence-rules skill

`evidence-rules` requires citing FILE PATHS + LINE NUMBERS for claims
about the codebase ("function X is at file.ts:42").

`knowledge-grounding` requires citing SOURCES for claims about how things
should be done or why ("eventual consistency is appropriate here because
of CAP/Brewer 2000").

Both apply simultaneously. Use the right format for the right kind of
claim.
