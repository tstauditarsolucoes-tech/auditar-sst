#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-app/Auditar_SST_v1_5_dashboard}"

bash tools/assemble_android_v32961.sh "$APP_DIR"
python tools/apply_report_templates_v32962_v3305.py "$APP_DIR" android

echo "Fonte Android v3.29.62 com modelos de relatório montada."
