#!/usr/bin/env python3
"""Auditar SST v3.29.143 / v3.30.62 — Central Inteligente de Campo.

Additive UI/read-only feature. Does not modify database schema, synchronization,
auth, media, Drive, AI transport or Google Apps Script.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_field_intelligence_center_v329143_v33062.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")
repo = Path(__file__).resolve().parents[1]

protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
]
before = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in protected}

source = repo / "feature_sources/field_intelligence_center_v329143.dart"
target = root / "lib/screens/field_intelligence_center.dart"
if not source.exists():
    raise SystemExit("FIELD_CENTER source ausente")
shutil.copyfile(source, target)

home_path = root / "lib/screens/home_screen.dart"
home = home_path.read_text(encoding="utf-8")

# Import is intentionally isolated to Home.
import_anchor = "import 'settings_screen.dart';\n"
if "import 'field_intelligence_center.dart';" not in home:
    if home.count(import_anchor) != 1:
        raise SystemExit("FIELD_CENTER home import anchor mismatch")
    home = home.replace(
        import_anchor,
        import_anchor + "import 'field_intelligence_center.dart';\n",
        1,
    )

# Add one visible module without rearranging existing modules.
module_anchor = "  List<_ModuleData> get _modules => [\n"
if "title: 'Central Inteligente de Campo'" not in home:
    if home.count(module_anchor) != 1:
        raise SystemExit("FIELD_CENTER modules anchor mismatch")
    module = """  List<_ModuleData> get _modules => [
        _ModuleData(
          title: 'Central Inteligente de Campo',
          tutorialId: 'field-center',
          subtitle: 'Busca, prioridades, evidências e atalhos rápidos',
          icon: Icons.travel_explore_rounded,
          color: AuditarBrand.greenDark,
          page: () => const FieldIntelligenceCenterScreen(),
        ),
"""
    home = home.replace(module_anchor, module, 1)

home_path.write_text(home, encoding="utf-8", newline="\n")

# Version only. No schema migration.
pub_path = root / "pubspec.yaml"
pub = pub_path.read_text(encoding="utf-8")
old_version, new_version = (
    ("3.29.142+284", "3.29.143+285")
    if platform == "android"
    else ("3.30.61+248", "3.30.62+249")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise SystemExit("FIELD_CENTER version mismatch: " + old_version)
pub_path.write_text(pub.replace(marker, "version: " + new_version, 1),
                    encoding="utf-8", newline="\n")

changed = [
    p for p, digest in before.items()
    if hashlib.sha256((root / p).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

home_final = home_path.read_text(encoding="utf-8")
center = target.read_text(encoding="utf-8")
assert "Central Inteligente de Campo" in home_final
assert "FieldIntelligenceCenterScreen" in home_final
assert "Busca global" in center
assert "Central de evidências" in center
assert "Diagnóstico técnico ADM" in center
assert "Atalhos favoritos" in center
assert "O que precisa de atenção" in center
assert "pendingChangesCount" in center
assert "MediaSyncService.pendingCount" in center
assert "sendPendingMediaNow" not in center
assert "version: " + new_version in pub_path.read_text(encoding="utf-8")

print("FIELD_INTELLIGENCE_CENTER_OK", platform, new_version)
print("CORE_SYNC_DB_AUTH_MEDIA_AI_GS_BYTE_IDENTICAL_OK")
