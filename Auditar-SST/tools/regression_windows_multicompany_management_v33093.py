#!/usr/bin/env python3
"""Regressão Gestão Multempresa Windows v3.30.93."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: regression_windows_multicompany_management_v33093.py <APP_DIR>")

root = Path(sys.argv[1])
home = (root / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
screen = (root / "lib/screens/company_portfolio_management_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

checks = {
    "version": "version: 3.30.93+280" in pub,
    "screen": "class CompanyPortfolioManagementScreen" in screen,
    "all_companies": "getCompanies()" in screen,
    "company_nc": "getNonConformityRows" in screen,
    "company_actions": "getPendingActions" in screen,
    "company_training": "getTrainingSummary" in screen,
    "company_inspections": "getInspectionHistory" in screen,
    "priority_sort": "Prioridade alta" in screen and "statusRank" in screen,
    "table": "Empresas por prioridade de acompanhamento" in screen,
    "company_route": "FieldOperationalControlScreen" in screen,
    "home_entry": "CompanyPortfolioManagementScreen" in home and "Gestão Multempresa" in home,
    "home_cta": "Ver todas as empresas" in home,
    "mobile_preserved": "Widget _mobileBody()" in home,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise AssertionError("regressões Gestão Multempresa: " + repr(failed))

for forbidden in [
    "insert(",
    "update(",
    "delete(",
    "CREATE TABLE",
    "ALTER TABLE",
]:
    if forbidden in screen:
        raise AssertionError("Gestão Multempresa deixou de ser somente leitura: " + forbidden)

print("WINDOWS_MULTICOMPANY_MANAGEMENT_REGRESSION_OK")
print("READ_ONLY_PORTFOLIO_OK")
print("MOBILE_LAYOUT_PATH_STILL_PRESENT_OK")
