#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Adding langgraph submodule..."
git submodule add https://github.com/langchain-ai/langgraph.git src_ext/langgraph || true

echo "Adding deer-flow submodule..."
git submodule add https://github.com/bytedance/deer-flow.git src_ext/deer-flow || true

echo "Adding CopilotKit submodule..."
git submodule add https://github.com/CopilotKit/CopilotKit.git src_ext/copilotkit || true

echo "Submodules added. Run 'git submodule update --init --recursive' to fetch contents."
