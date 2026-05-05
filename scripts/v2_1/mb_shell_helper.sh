# mb-framework shell helper — source this from ~/.zshrc (or ~/.bashrc)
# Usage:
#   mb list            — list registered projects
#   mb <name>          — cd into the project and launch claude
#   mb help            — show this help

mb() {
  local mb_repo="${MB_FRAMEWORK_PATH:-$HOME/code/Yanick-mj/mb-framework}"
  local py="$mb_repo/scripts/v2_1/projects.py"

  case "$1" in
    ""|help|-h|--help)
      echo "mb <name>  — cd to project and launch claude"
      echo "mb list    — list registered projects"
      echo "mb dashboard — launch browser dashboard on localhost:5111"
      echo "mb help    — this message"
      return 0
      ;;
    list)
      python3 "$py"
      return 0
      ;;
    dashboard)
      shift
      local port="${MB_DASHBOARD_PORT:-5111}"
      if [[ "$1" == "--port" && -n "$2" ]]; then
        port="$2"
        shift 2
      fi
      PYTHONPATH="$mb_repo" python3 -m scripts.dashboard --port "$port" &
      local pid=$!
      sleep 1
      python3 -m webbrowser "http://localhost:$port" 2>/dev/null
      echo "mb-dashboard running on http://localhost:$port (PID: $pid)"
      echo "Press Ctrl+C to stop."
      wait $pid
      return 0
      ;;
    *)
      local target
      target=$(PYTHONPATH="$mb_repo/scripts" python3 -c "
import sys
from v2_1 import projects
name = sys.argv[1]
for p in projects.load():
    if p['name'] == name:
        print(p['path'])
        break
" "$1")
      if [ -z "$target" ]; then
        echo "Unknown project: $1" >&2
        echo "Use 'mb list' to see registered projects." >&2
        return 1
      fi
      cd "$target" || return 1
      claude
      ;;
  esac
}
