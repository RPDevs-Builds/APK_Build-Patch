#!/usr/bin/env bash
# ==============================================================================
# Local ReVanced & Morphe Patch Runner
# Usage: ./scripts/run_local_patch.sh [App-Name]
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${ROOT_DIR}/.venv/bin/activate" ]; then
    source "${ROOT_DIR}/.venv/bin/activate"
fi

APP="${1:-}"

if [ -n "$APP" ]; then
    echo "[+] Running local patcher for: $APP"
    python -m src.cli patch --app "$APP"
else
    echo "[+] Running local patcher for all enabled apps..."
    python -m src.cli patch
fi
