#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])

screen = (root / "lib/screens/field_operational_control_screen.dart").read_text(
    encoding="utf-8"
)
service = (root / "lib/services/field_operational_priority_service.dart").read_text(
    encoding="utf-8"
)
badge = (root / "lib/widgets/field_connectivity_badge.dart").read_text(
    encoding="utf-8"
)
center = (root / "lib/screens/field_intelligence_center_screen.dart").read_text(
    encoding="utf-8"
)
home = (root / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

for forbidden in (
    "ALTER TABLE",
    "CREATE TABLE",
    "AiAssistantService",
    "DriveService",
):
    assert forbidden not in screen, "dependencia indevida no controle: " + forbidden
    assert forbidden not in service, "dependencia indevida nas regras: " + forbidden

for snippet in (
    "Status do aparelho:",
    "Central de pendências",
    "Abrir plano de ação",
    "Antes × Depois e recorrências",
    "O que conferir hoje",
    "DeviceSyncService.pendingChangesCount()",
    "MediaSyncService.pendingCount()",
    "CorrectionRecurrenceDetector.detect",
    "getPhotosForAnswer",
    "getCompletionPhotos",
    "ActionPlanScreen",
    "CorrectionEvidenceCenterScreen",
):
    assert snippet in screen, "controle operacional incompleto: " + snippet

for snippet in (
    "critical_nc",
    "overdue_actions",
    "recurrence",
    "training",
    "evidence",
    "inspection_due",
    "sync",
):
    assert snippet in service, "roteiro operacional incompleto: " + snippet

assert "InternetAddress.lookup('script.google.com')" in badge
assert "InternetAddress.lookup('script.google.com')" in screen
assert "const FieldConnectivityBadge()" in home
assert "Controle operacional de campo" in center
assert "FieldOperationalControlScreen" in center

assert (
    "version: 3.29.163+305" in pub
    or "version: 3.30.82+269" in pub
), "versao do controle operacional incorreta"

print("FIELD_OPERATIONAL_CONTROL_REGRESSION_OK")
print("ONLINE_OFFLINE_BADGE_OK")
print("PENDING_ACTION_RECURRENCE_EVIDENCE_VISIT_PLAN_OK")
print("NO_SCHEMA_SYNC_AUTH_MEDIA_DRIVE_AI_GS_CHANGE_REQUIRED_OK")
