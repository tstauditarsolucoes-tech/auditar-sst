#!/usr/bin/env python3
"""Regression guard for the additive Field Intelligence Center."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
home = (root / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
center = (root / "lib/screens/field_intelligence_center.dart").read_text(encoding="utf-8")

for snippet in [
    "Central Inteligente de Campo",
    "FieldIntelligenceCenterScreen",
    "Busca global",
    "Central de evidências",
    "Atalhos favoritos",
    "O que precisa de atenção",
    "Diagnóstico técnico ADM",
    "pendingChangesCount",
    "MediaSyncService.pendingCount",
]:
    assert snippet in (home + center), "Missing field center feature: " + snippet

# The new screen is read-only regarding synchronization.
assert "sendPendingMediaNow" not in center
assert "syncAll" not in center
assert "enqueue" not in center

print("FIELD_INTELLIGENCE_CENTER_REGRESSION_OK")
