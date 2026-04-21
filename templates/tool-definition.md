<!-- Template for tools/{tool-name}/TOOL.md — per-tool documentation.
     Copy to tools/<tool>/TOOL.md and fill in. -->

# <tool-name>

## Purpose

<!-- One sentence. What does this tool do for the project? -->

## Actions

| Action | Description | Used by (agents) |
|---|---|---|
| read | Read-only access to resources | be-dev, verifier |
| write | Mutating writes | be-dev only |
| migrate | Schema changes | be-dev, devops |

## Stage-gated actions

Per-stage allowed actions (tie to `memory/permissions.yaml`):

- **discovery**: none (tool likely not in use yet)
- **mvp**: read, write (permissive for wedge iterations)
- **pmf**: read, write (with RLS check), migrate (devops only)
- **scale**: read, write (audit log required), migrate (devops only)

## Credentials

Stored in `creds/<tool-name>.env` (gitignored).

Required environment variables:
- `<TOOL>_API_KEY`
- `<TOOL>_PROJECT_ID`
- …

## Rate limits / quotas

<!-- Document known rate limits and quota behavior. -->

## Gotchas

<!-- Versioning, idempotency, retry semantics, etc. -->
