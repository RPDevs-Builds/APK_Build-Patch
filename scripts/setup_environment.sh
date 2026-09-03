#!/usr/bin/env bash
# ==============================================================================
# Setup Local Environment for APK_Build-Patch
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[+] Setting up environment in ${ROOT_DIR}..."

# 1. Create Python Virtual Environment
if [ ! -d "${ROOT_DIR}/.venv" ]; then
    echo "[+] Creating Python 3.11 virtual environment..."
    python3 -m venv "${ROOT_DIR}/.venv"
fi

source "${ROOT_DIR}/.venv/bin/activate"

# 2. Install dependencies
echo "[+] Installing Python requirements..."
pip install --upgrade pip
pip install -r "${ROOT_DIR}/requirements.txt"
pip install -e "${ROOT_DIR}"

# 3. Ensure prebuilts executable
echo "[+] Configuring binary tools..."
chmod +x "${ROOT_DIR}/bin/aapt2/"* "${ROOT_DIR}/bin/htmlq/"* "${ROOT_DIR}/bin/toml/"* 2>/dev/null || true

# 4. Create output folders
mkdir -p "${ROOT_DIR}/temp" "${ROOT_DIR}/dist/apks" "${ROOT_DIR}/dist/fdroid" "${ROOT_DIR}/dist/web"

echo "[✓] Environment setup completed successfully!"
