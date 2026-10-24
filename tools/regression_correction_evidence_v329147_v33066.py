#!/usr/bin/env python3
"""Static regression guard for Auditar SST v3.29.147 / v3.30.66."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit(
        "uso: regression_correction_evidence_v329147_v33066.py <APP_DIR>"
    )

root = Path(sys.argv[1])


def content(rel):
    path = root / rel
    if not path.exists():
        raise SystemExit("arquivo ausente: " + rel)
    return path.read_text(encoding="utf-8")


screen = content("lib/screens/correction_evidence_center_screen.dart")
central = content("lib/screens/field_intelligence_center_screen.dart")
detector = content("lib/services/correction_recurrence_detector.dart")

required_screen = [
    "Evidências e recorrências",
    "Antes × Depois",
    "Possíveis recorrências",
    "getPhotosForAnswer",
    "getCompletionPhotos",
    "CorrectionRecurrenceDetector.detect",
    "ActionPlanScreen(companyId: widget.company.id)",
    "NonConformitiesScreen(companyId: widget.company.id)",
]
for marker in required_screen:
    if marker not in screen:
        raise SystemExit("REGRESSION_MISSING_SCREEN_MARKER: " + marker)

for marker in [
    "Antes × Depois e recorrências",
    "CorrectionEvidenceCenterScreen(company: selectedCompany!)",
    "Conferir proteção e backup das fotos",
]:
    if marker not in central:
        raise SystemExit("REGRESSION_MISSING_CENTRAL_MARKER: " + marker)

for marker in [
    "threshold = 0.66",
    "sectorOf",
    "similarity",
    "records.length < 2",
]:
    if marker not in detector:
        raise SystemExit("REGRESSION_MISSING_RECURRENCE_MARKER: " + marker)

for forbidden in [
    "CREATE TABLE",
    "ALTER TABLE",
    "DeviceSyncService",
    "MediaSyncService",
    "DriveService",
    "AiAssistantService",
]:
    if forbidden in screen or forbidden in detector:
        raise SystemExit("REGRESSION_FORBIDDEN_CHANGE: " + forbidden)

print("CORRECTION_EVIDENCE_RECURRENCE_REGRESSION_OK")
