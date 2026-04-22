#!/usr/bin/env bash
# Tests for hooks/orchestrator-autoinvoke.sh (v2.2.1).
# Feeds JSON stdin to the hook and asserts stdout either injects the
# system-reminder ("INJECT") or stays silent ("SILENT").
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
expect INJECT "implémente une fonction de login avec OAuth" "FR:implémente"
expect INJECT "add a rate limiter to the api endpoints"    "EN:add"
expect INJECT "fix the bug in the payment flow"            "EN:fix"
expect INJECT "refactore le hook useAuth pour supporter le multi-tenant" "FR:refactore"
expect INJECT "create a new dashboard for admin users"     "EN:create"

# --- Cases that should stay SILENT ---
expect SILENT "/mb:feature add a thing"         "slash:/mb:feature"  # slash = own routing
expect SILENT "/mb:fix bug in login"            "slash:/mb:fix"
expect SILENT "hello"                           "short:greeting"
expect SILENT "ok"                              "short:ack"
expect SILENT "what does this function do?"     "Q&A:no action verb"
expect SILENT "explique moi ce code"            "FR:Q&A no verb"
expect SILENT "quick answer: implement X"       "optout:quick answer"
expect SILENT "implement X skip orchestrator"   "optout:skip orchestrator"

# Env var opt-out
expect SILENT "implement a new feature" "env:MB_ORCHESTRATOR_AUTOINVOKE=off" "MB_ORCHESTRATOR_AUTOINVOKE=off"

# Report
if [ ${#failures[@]} -gt 0 ]; then
  echo "FAIL: ${#failures[@]} orchestrator-autoinvoke scenario(s) failed:" >&2
  for f in "${failures[@]}"; do echo "  - $f" >&2; done
  exit 1
fi

echo "OK: orchestrator-autoinvoke — all scenarios passed"
