#!/bin/bash
# mb-framework pre-commit hook
# Adapt the commands below to your project's tooling

set -e

echo "Running pre-commit checks..."

# TypeScript type check (uncomment and adapt)
# npx tsc --noEmit

# Lint (uncomment and adapt)
# npx eslint --quiet .
# npx biome lint .

# Tests (uncomment and adapt)
# npx jest --bail --passWithNoTests
# npx vitest run

echo "Pre-commit checks passed."
