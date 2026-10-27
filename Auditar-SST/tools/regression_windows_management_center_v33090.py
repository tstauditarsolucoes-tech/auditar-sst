#!/usr/bin/env python3
"""Regressão da Central de gestão Windows v3.30.90."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: regression_windows_management_center_v33090.py <APP_DIR>")

root = Path(sys.argv[1])
screen = (root / "lib/screens/field_operational_control_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

checks = {
    "versao": "version: 3.30.90+277" in pub,
    "desktop_breakpoint": "constraints.maxWidth >= 1000" in screen,
    "desktop_title": "Central de gestão SST" in screen,
    "company_center": "CENTRAL DA EMPRESA" in screen,
    "pending_center": "Central de pendências" in screen,
    "pending_table": "DataTable(" in screen and "_desktopPendingEntries" in screen,
    "decision_summary": "Resumo para decisão" in screen and "_decisionSummary" in screen,
    "local_without_ai": "sem depender de IA" in screen,
    "compact_flow": "_compactBody()" in screen and "Controle operacional de campo" in screen,
    "evidence": "Correções e evidências" in screen,
    "quick_actions": "Plano de ação" in screen and "Não conformidades" in screen and "Treinamentos" in screen,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise AssertionError("regressoes da Central desktop: " + repr(failed))

print("WINDOWS_MANAGEMENT_CENTER_REGRESSION_OK")
print("VERSION_3_30_90_OK")
print("DESKTOP_AND_COMPACT_PATHS_PRESENT_OK")
