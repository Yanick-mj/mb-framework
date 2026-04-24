#!/usr/bin/env bash
# Tests for hooks/orchestrator-autoinvoke.sh (v2.2.2).
# Feeds JSON stdin to the hook and asserts stdout either injects the
# system-reminder ("INJECT") or stays silent ("SILENT").
#
# v2.2.2 contract: the hook is SILENT only for the 4 hard guards —
#   (1) empty prompt, (2) slash command, (3) word_count < 4,
#   (4) explicit opt-out phrase or env var.
# Everything else injects. The orchestrator itself decides whether the
# task is Q&A (direct answer) or an action (full pipeline).
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
HOOK="$repo_root/hooks/orchestrator-autoinvoke.sh"

if [ ! -x "$HOOK" ]; then
  echo "FAIL: hook not executable at $HOOK" >&2
  exit 1
fi

failures=()

# $1 = expected (INJECT|SILENT)  $2 = prompt  $3 = label  $4 = optional env
expect() {
  local expected="$1"
  local prompt="$2"
  local label="$3"
  local env_prefix="${4:-}"

  local payload
  payload="$(printf '{"prompt":"%s","session_id":"test","transcript_path":""}' "$prompt")"

  local out
  if [ -n "$env_prefix" ]; then
    out="$(printf '%s' "$payload" | env $env_prefix bash "$HOOK" || true)"
  else
    out="$(printf '%s' "$payload" | bash "$HOOK" || true)"
  fi

  local actual
  if printf '%s' "$out" | grep -q "mb-framework auto-invoke"; then
    actual="INJECT"
  else
    actual="SILENT"
  fi

  if [ "$actual" != "$expected" ]; then
    failures+=("$label: expected $expected, got $actual (prompt='$prompt')")
  fi
}

# --- Cases that SHOULD inject the orchestrator reminder ---
# Action prompts (FR + EN) — the common case.
expect INJECT "implémente une fonction de login avec OAuth" "FR:implémente"
expect INJECT "add a rate limiter to the api endpoints"    "EN:add"
expect INJECT "fix the bug in the payment flow"            "EN:fix"
expect INJECT "refactore le hook useAuth pour supporter le multi-tenant" "FR:refactore"
expect INJECT "create a new dashboard for admin users"     "EN:create"

# v2.2.2 regression cases — verbs NOT in the old action_pattern.
# These failed silently in v2.2.1; now they must INJECT.
expect INJECT "connect le ce repo a vercel à la place du old repo" "FR:connect (v2.2.1 regression)"
expect INJECT "lier ce projet à Supabase"                          "FR:lier (v2.2.1 regression)"
expect INJECT "point studioiris.io vers le nouveau deployment"     "EN:point (v2.2.1 regression)"
expect INJECT "switch the production database to staging"          "EN:switch (v2.2.1 regression)"

# Q&A cases — v2.2.2 lets these through and relies on the orchestrator
# to answer directly without spinning up a pipeline. This trades a small
# overhead for zero false negatives on action prompts.
expect INJECT "what does this function do?" "Q&A:what"
expect INJECT "explique moi ce code"        "Q&A:FR explique"

# --- Cases that MUST stay SILENT — the 4 hard guards ---
expect SILENT "/mb:feature add a thing"         "guard1:slash /mb:feature"
expect SILENT "/mb:fix bug in login"            "guard1:slash /mb:fix"
expect SILENT "hello"                           "guard2:short greeting"
expect SILENT "ok"                              "guard2:short ack"
expect SILENT "quick answer: implement X"       "guard3:optout quick answer"
expect SILENT "implement X skip orchestrator"   "guard3:optout skip orchestrator"
expect SILENT "no orchestrator please add X"    "guard3:optout no orchestrator"
expect SILENT "sans orchestrator corrige ça"    "guard3:optout sans orchestrator"

# Env var opt-out (guard 4)
expect SILENT "implement a new feature" "guard4:env MB_ORCHESTRATOR_AUTOINVOKE=off" "MB_ORCHESTRATOR_AUTOINVOKE=off"

# Report
if [ ${#failures[@]} -gt 0 ]; then
  echo "FAIL: ${#failures[@]} orchestrator-autoinvoke scenario(s) failed:" >&2
  for f in "${failures[@]}"; do echo "  - $f" >&2; done
  exit 1
fi

echo "OK: orchestrator-autoinvoke — all scenarios passed"
