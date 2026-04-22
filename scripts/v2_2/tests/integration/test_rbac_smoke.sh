#!/usr/bin/env bash
# F5 real-project smoke test for Feature F (Tool RBAC).
# Builds a throwaway project tree with stage=pmf + a permissions.yaml and
# verifies three canonical scenarios:
#   1. fe-dev × vercel × deploy-prod  → DENIED (fe-dev only has deploy-preview)
#   2. devops × vercel × deploy-prod  → ALLOWED
#   3. be-dev × supabase × migrate    → ALLOWED at pmf
# Also checks the audit log recorded all three with correct flags.
#
# Exit 0 on full pass, 1 on any scenario mismatch.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"

# Prefer repo-local venv (has pyyaml) over system python when running locally.
if [ -x "$repo_root/.venv/bin/python3" ]; then
  PY="$repo_root/.venv/bin/python3"
else
  PY="python3"
fi

SMOKE="$(mktemp -d)"
trap 'rm -rf "$SMOKE"' EXIT

cd "$SMOKE"
mkdir -p memory tools

cat > mb-stage.yaml <<YAML
stage: pmf
since: 2026-04-22
YAML

cat > tools/_catalog.yaml <<YAML
version: 1
tools:
  - name: supabase
    actions: [read, write, migrate]
  - name: vercel
    actions: [deploy-preview, deploy-prod]
YAML

cat > memory/permissions.yaml <<YAML
permissions:
  be-dev:
    - tool: supabase
      actions:
        discovery: []
        mvp: [read, write]
        pmf: [read, write, migrate]
        scale: [read, write, migrate]
  fe-dev:
    - tool: vercel
      actions: [deploy-preview]
  devops:
    - tool: vercel
      actions: [deploy-preview, deploy-prod]
YAML

errors=()

# Scenario 1 — expect DENIED (exit 1)
if PYTHONPATH="$repo_root" $PY -m scripts.v2_2.rbac check fe-dev vercel deploy-prod >/dev/null 2>&1; then
  errors+=("fe-dev vercel deploy-prod: expected DENIED, got ALLOWED")
fi

# Scenario 2 — expect ALLOWED (exit 0)
if ! PYTHONPATH="$repo_root" $PY -m scripts.v2_2.rbac check devops vercel deploy-prod >/dev/null 2>&1; then
  errors+=("devops vercel deploy-prod: expected ALLOWED, got DENIED")
fi

# Scenario 3 — expect ALLOWED at pmf
if ! PYTHONPATH="$repo_root" $PY -m scripts.v2_2.rbac check be-dev supabase migrate >/dev/null 2>&1; then
  errors+=("be-dev supabase migrate @pmf: expected ALLOWED, got DENIED")
fi

# Audit log should contain all three events (1 DENIED + 2 ALLOWED)
audit_out=$(PYTHONPATH="$repo_root" $PY -m scripts.v2_2.rbac)
allowed_count=$(echo "$audit_out" | grep -c "✅" || true)
denied_count=$(echo "$audit_out" | grep -c "🔴" || true)
if [ "$allowed_count" -lt 2 ]; then
  errors+=("audit log shows $allowed_count ALLOWED, expected ≥ 2")
fi
if [ "$denied_count" -lt 1 ]; then
  errors+=("audit log shows $denied_count DENIED, expected ≥ 1")
fi

if [ ${#errors[@]} -gt 0 ]; then
  echo "FAIL: ${#errors[@]} RBAC smoke scenario(s) failed:" >&2
  for e in "${errors[@]}"; do echo "  - $e" >&2; done
  exit 1
fi

echo "OK: Feature F RBAC smoke test passed (3/3 scenarios + audit log)"
