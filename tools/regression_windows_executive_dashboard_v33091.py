#!/usr/bin/env python3
"""Regressão do Painel Executivo Auditar Windows v3.30.91."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: regression_windows_executive_dashboard_v33091.py <APP_DIR>")

root = Path(sys.argv[1])
dashboard = (root / "lib/screens/executive_dashboard_screen.dart").read_text(encoding="utf-8")
central = (root / "lib/screens/field_operational_control_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

checks = {
    "version": "version: 3.30.91+278" in pub,
    "screen": "class ExecutiveDashboardScreen" in dashboard,
    "score": "ÍNDICE AUDITAR SST" in dashboard and "healthScore" in dashboard,
    "legal_guardrail": "indicador gerencial interno" in dashboard and "Não substitui avaliação técnica" in dashboard,
    "month_results": "O que foi realizado neste mês" in dashboard,
    "evolution": "Evolução mensal" in dashboard and "_comparisonRow" in dashboard,
    "resolved": "NCs resolvidas" in dashboard,
    "priorities": "Prioridades da gestão" in dashboard and "Top prioridades abertas" in dashboard,
    "recurrence": "Reincidências" in dashboard,
    "presentation": "Modo apresentação" in dashboard and "presentationMode" in dashboard,
    "readonly_sources": "getNonConformityRows" in dashboard and "getPendingActions" in dashboard and "getInspectionHistory" in dashboard,
    "central_entry": "ExecutiveDashboardScreen" in central and "Painel executivo" in central,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise AssertionError("regressoes Painel Executivo: " + repr(failed))

for forbidden in [
    "insert(",
    "update(",
    "delete(",
    "CREATE TABLE",
    "ALTER TABLE",
]:
    if forbidden in dashboard:
        raise AssertionError("Painel Executivo deixou de ser somente leitura: " + forbidden)

print("WINDOWS_EXECUTIVE_DASHBOARD_REGRESSION_OK")
print("VERSION_3_30_91_OK")
print("READ_ONLY_EXECUTIVE_VIEW_OK")
print("MANAGEMENT_CENTER_ENTRY_OK")
