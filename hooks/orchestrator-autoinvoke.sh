#!/usr/bin/env bash
# mb-framework v2.2.2 — UserPromptSubmit hook
#
# Purpose: When the user sends a free-form prompt that looks like an
# implementation/action task, inject a system-reminder telling Claude to
# invoke the Skill tool with `mb-orchestrator` BEFORE touching any file.
#
# This makes the orchestrator the default entry point for any meaningful
# task — without requiring the user to type /mb:feature every time.
#
# Input: JSON on stdin with a `prompt` field (Claude Code UserPromptSubmit).
# Output: plain text on stdout becomes additional context for Claude.
# Exit code 0: always (hook never blocks).
#
# Install: the install.sh script wires this into .claude/settings.json.
# Opt-out per project: delete the hook entry in settings.json, OR set
# env var MB_ORCHESTRATOR_AUTOINVOKE=off before launching Claude Code.
set -euo pipefail

# Global opt-out via env var
if [ "${MB_ORCHESTRATOR_AUTOINVOKE:-on}" = "off" ]; then
  exit 0
fi

input="$(cat)"

# Extract prompt. Prefer jq for correctness; fallback to a naive sed.
if command -v jq >/dev/null 2>&1; then
  prompt="$(printf '%s' "$input" | jq -r '.prompt // empty')"
else
  # Best-effort fallback — handles simple prompts without embedded quotes/newlines
  prompt="$(printf '%s' "$input" | sed -n 's/.*"prompt"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
fi

# Nothing to analyse
if [ -z "${prompt:-}" ]; then
  exit 0
fi

# Slash commands handle their own routing (/mb:feature etc.)
case "$prompt" in
  /*) exit 0 ;;
esac

# Very short prompts are almost always Q&A or acknowledgements
word_count=$(printf '%s' "$prompt" | wc -w | tr -d ' ')
if [ "$word_count" -lt 4 ]; then
  exit 0
fi

# v2.2.2: Action-verb filter REMOVED.
# The orchestrator itself handles Q&A / read-only classification (Step 1).
# Keeping the filter here caused false negatives for verbs not in the list
# (e.g. "connect", "lier", "pointer"). Let the orchestrator decide — it is
# strictly more intelligent than any regex and already knows how to route
# a pure Q&A prompt to a direct answer without spinning up the pipeline.

# Opt-out phrases the user can drop inline
case "$prompt" in
  *"skip orchestrator"*|*"quick answer"*|*"no orchestrator"*|*"sans orchestrator"*|*"réponse rapide"*)
    exit 0
    ;;
esac

cat <<'EOF'
<system-reminder>
mb-framework auto-invoke (v2.2.2):

This prompt looks like an implementation or action task. Before writing or
editing ANY file, invoke the Skill tool with `mb-orchestrator` so it can
classify the task and route it to the correct agent pipeline.

If the orchestrator concludes the task is pure Q&A / read-only / trivial
explanation, answer directly afterwards. Otherwise follow its pipeline
(architect → fe-dev/be-dev → verifier, etc.).

Skip the orchestrator only when:
- The task is clearly pure read/explain (no files will be edited).
- The user explicitly said "skip orchestrator", "quick answer", or
  "sans orchestrator" in their prompt.

To disable this reminder project-wide: edit .claude/settings.json or set
MB_ORCHESTRATOR_AUTOINVOKE=off in your shell.
</system-reminder>
EOF
