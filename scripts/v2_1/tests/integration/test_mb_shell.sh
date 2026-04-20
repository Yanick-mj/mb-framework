#!/usr/bin/env bash
# Integration smoke test for the `mb` shell helper.
# Run: bash scripts/v2_1/tests/integration/test_mb_shell.sh
set -euo pipefail

TEST_HOME=$(mktemp -d)
export HOME="$TEST_HOME"
export MB_FRAMEWORK_PATH="$(cd "$(dirname "$0")/../../../.." && pwd)"

# Activate venv for pyyaml availability
source "$MB_FRAMEWORK_PATH/scripts/v2_1/.venv/bin/activate" 2>/dev/null || true

# Seed registry
PYTHONPATH="$MB_FRAMEWORK_PATH/scripts" python3 -c "
import os
from v2_1 import projects
projects.add(name='demo', path='/tmp/demo', stage='mvp')
"

# Source the helper and test list
source "$MB_FRAMEWORK_PATH/scripts/v2_1/mb_shell_helper.sh"

output=$(mb list)
if [[ "$output" != *"demo"* ]]; then
  echo "FAIL: mb list did not show 'demo'"
  echo "output: $output"
  exit 1
fi

# Test unknown project
if mb nonexistent 2>/dev/null; then
  echo "FAIL: mb nonexistent should fail"
  exit 1
fi

echo "OK: mb shell helper smoke test passed"
rm -rf "$TEST_HOME"
