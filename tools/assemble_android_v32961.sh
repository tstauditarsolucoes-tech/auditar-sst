#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${1:-app/Auditar_SST_v1_5_dashboard}"
bash tools/assemble_android_v32960.sh "$APP_DIR"
python tools/patch_ronda_history_review_v32961.py "$APP_DIR"
echo "Fonte Android v3.29.61 montada."
