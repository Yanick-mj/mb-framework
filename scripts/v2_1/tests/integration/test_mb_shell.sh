#!/usr/bin/env bash
# Integration smoke test for the `mb` shell helper.
# Run: bash scripts/v2_1/tests/integration/test_mb_shell.sh
set -euo pipefail

export HOME=$(mktemp -d)
export MB_FRAMEWORK_PATH="$(cd "$(dirname "$0")/../../../.." && pwd)"

# Seed registry
python3 -c "
import sys; sys.path.insert(0, '$MB_FRAMEWORK_PATH/scripts')
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
rm -rf "$HOME"
