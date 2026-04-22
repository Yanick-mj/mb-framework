#!/usr/bin/env bash
# Guard: all 7 tool-touching agents must contain the Pre-flight RBAC block.
# Accepts either the v2.2 layout (AGENT.md) or the legacy v2.1 layout (SKILL.md).
# Part of v2.2. Invoke from scripts/v2_2/tests/integration/.
set -euo pipefail

AGENTS=(
  "be-dev"
  "fe-dev"
  "devops"
  "tea"
  "verifier"
  "lead-dev"
  "tech-writer"
)

MARKER="Pre-flight: Tool RBAC"

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

missing=()
for name in "${AGENTS[@]}"; do
  agent_md="agents/$name/AGENT.md"
  skill_md="agents/$name/SKILL.md"

  if [ -f "$agent_md" ]; then
    if ! grep -q "$MARKER" "$agent_md"; then
      missing+=("$name: '$MARKER' block missing in $agent_md")
    fi
    continue
  fi

  # Fallback: legacy agent without v2.2 split — check SKILL.md
  if [ -f "$skill_md" ]; then
    if ! grep -q "$MARKER" "$skill_md"; then
      missing+=("$name: '$MARKER' block missing in $skill_md (legacy)")
    fi
    continue
  fi

  missing+=("$name: neither AGENT.md nor SKILL.md exists in agents/$name/")
done

if [ ${#missing[@]} -gt 0 ]; then
  echo "FAIL: Pre-flight RBAC block missing from ${#missing[@]} agent(s):" >&2
  for m in "${missing[@]}"; do echo "  - $m" >&2; done
  exit 1
fi

echo "OK: Pre-flight RBAC present in all ${#AGENTS[@]} tool-touching agents"
