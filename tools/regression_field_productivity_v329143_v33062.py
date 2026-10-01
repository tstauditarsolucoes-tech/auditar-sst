#!/usr/bin/env python3
"""Regression guard for v3.29.143 / v3.30.62 field productivity package."""
from pathlib import Path
import sys

root = Path(sys.argv[1])

home = (root / 'lib/screens/home_screen.dart').read_text(encoding='utf-8')
company = (root / 'lib/screens/company_detail_screen.dart').read_text(encoding='utf-8')
admin = (root / 'lib/screens/admin_center_screen.dart').read_text(encoding='utf-8')
ronda = (root / 'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
search = (root / 'lib/screens/global_search_screen.dart').read_text(encoding='utf-8')
center = (root / 'lib/screens/field_command_center_screen.dart').read_text(encoding='utf-8')

for snippet in [
    "tutorialId: 'field_center'",
    "tooltip: 'Busca global'",
    "GlobalSearchScreen()",
    "FieldCommandCenterScreen()",
]:
    assert snippet in home, 'Home missing: ' + snippet

assert "GlobalSearchScreen(company: widget.company)" in company
assert "Diagnóstico técnico" in admin
assert "DataSafetyScreen()" in admin

for snippet in [
    "Usar último setor/local",
    "express_round_last_sector_",
    "express_round_last_location_",
    "_reuseLastContext()",
]:
    assert snippet in ronda, 'Ronda missing: ' + snippet

for snippet in [
    "class GlobalSearchScreen",
    "getInspectionHistory",
    "getNonConformityRows",
    "getPendingActions",
    "TREINAMENTO_SESSAO",
    "OBSERVACAO_SEGURANCA",
]:
    assert snippet in search, 'Search missing: ' + snippet

for snippet in [
    "class FieldCommandCenterScreen",
    "getRoutineTodaySummary",
    "getPendingActions",
    "Ações vencidas",
    "Prioridades",
]:
    assert snippet in center, 'Center missing: ' + snippet

print('FIELD_PRODUCTIVITY_REGRESSION_OK')
