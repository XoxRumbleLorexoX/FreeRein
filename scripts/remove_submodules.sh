#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

remove_submodule() {
  local path="$1"
  if [ -d "$path" ] || [ -f ".gitmodules" ]; then
    git submodule deinit -f "$path" 2>/dev/null || true
    rm -rf "$path"
    git rm -f "$path" 2>/dev/null || true
    sed -i'' "/$path/d" .gitmodules 2>/dev/null || true
  fi
}

remove_submodule src_ext/langgraph
remove_submodule src_ext/deer-flow
remove_submodule src_ext/copilotkit

echo "Submodules removed. You may want to commit the changes."
