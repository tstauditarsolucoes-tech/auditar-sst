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

print("FIELD_INTELLIGENCE_REGRESSION_OK")
