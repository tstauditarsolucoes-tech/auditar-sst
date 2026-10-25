#!/usr/bin/env python3
"""Regression guard for the additive Field Intelligence Center."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
home = (root / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
center = (root / "lib/screens/field_intelligence_center_screen.dart").read_text(encoding="utf-8")

for snippet in (
    "import 'field_intelligence_center_screen.dart';",
    "tutorialId: 'field_center'",
    "const FieldIntelligenceCenterScreen()",
):
    assert snippet in home, "Home missing: " + snippet

for snippet in (
    "Busca global",
    "Atalhos favoritos",
    "Central de evidências",
    "Diagnóstico técnico ADM",
    "getInspectionHistory",
    "getNonConformityRows",
    "getPendingActions",
    "getTrainingSummary",
    "EvidenceBackupScreen",
):
    assert snippet in center, "Center missing: " + snippet

# Regression from real Android Central Inteligente screenshot.
for token in (
    "'Central Inteligente'",
    "body: SafeArea(",
    "bottom: true",
    "LayoutBuilder(",
    "'Selecione empresa'",
    "fromLTRB(14, 14, 14, 110)",
    "AuthService.canAccessCompany(company.id)",
    "restrictedWithoutCompany",
    "userId != AuthService.currentUser?.id",
):
    assert token in center, "Field center layout/access regression: " + token

assert "width: MediaQuery.sizeOf(context).width < 600 ? 160 : 190,\n              child: Card(" not in center, (
    "Favorite labels should not be squeezed into fixed width ListTiles"
)

print("FIELD_INTELLIGENCE_REGRESSION_OK")
