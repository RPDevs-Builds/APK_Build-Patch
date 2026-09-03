#!/usr/bin/env bash
# ==============================================================================
# Local Open-Source Repository Build Runner
# Usage: ./scripts/run_local_build.sh [Repo-Name-or-URL]
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${ROOT_DIR}/.venv/bin/activate" ]; then
    source "${ROOT_DIR}/.venv/bin/activate"
fi

REPO="${1:-}"

if [ -n "$REPO" ]; then
    echo "[+] Running local source builder for: $REPO"
    python -m src.cli build --repo "$REPO"
else
    echo "[+] Running local source builder for all enabled repositories..."
    python -m src.cli build
fi
