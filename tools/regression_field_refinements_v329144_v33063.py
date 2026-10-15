#!/usr/bin/env python3
"""Regression guard for v3.29.144 / v3.30.63 field refinements."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
home = (root / 'lib/screens/home_screen.dart').read_text(encoding='utf-8')
center = (root / 'lib/screens/field_intelligence_center_screen.dart').read_text(encoding='utf-8')
company = (root / 'lib/screens/company_detail_screen.dart').read_text(encoding='utf-8')
timeline = (root / 'lib/screens/company_timeline_screen.dart').read_text(encoding='utf-8')
ronda = (root / 'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')

for snippet in (
    "final int initialTab;",
    "final String initialCompanyId;",
    "initialIndex: initial",
):
    assert snippet in center, 'Central missing: ' + snippet

assert "tooltip: 'Busca global'" in home
assert "FieldIntelligenceCenterScreen(initialTab: 1)" in home
assert "Pesquisar nesta empresa" in company
assert "Linha do tempo da empresa" in company
assert "CompanyTimelineScreen(company: widget.company)" in company

for snippet in (
    "class CompanyTimelineScreen",
    "TREINAMENTO_SESSAO",
    "OBSERVACAO_SEGURANCA",
    "completion_date",
    "Vistorias, DDS, treinamentos",
):
    assert snippet in timeline, 'Timeline missing: ' + snippet

for snippet in (
    "Usar último setor/local",
    "express_round_last_sector_",
    "express_round_last_location_",
    "_reuseLastContext()",
):
    assert snippet in ronda, 'Ronda missing: ' + snippet

print('FIELD_REFINEMENTS_REGRESSION_OK')
