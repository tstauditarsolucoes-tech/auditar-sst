#!/usr/bin/env python3
"""Auditar SST v3.29.143 / v3.30.62

Additive field productivity pack:
- Central Inteligente de Campo
- global search across existing local records
- favorite shortcuts
- operational priorities and productivity indicators
- evidence access using the existing protected media library
- read-only ADM diagnostics

The patch does not modify database schema, synchronization, auth, AI, media,
Drive or Google Apps Script implementation files.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_field_intelligence_v329143_v33062.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
repo_root = Path(__file__).resolve().parents[1]
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

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
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

feature_src = repo_root / "feature_sources/field_intelligence_center_v329143.dart"
feature_dst = root / "lib/screens/field_intelligence_center_screen.dart"
if not feature_src.exists():
    raise RuntimeError("fonte da Central Inteligente ausente")
shutil.copyfile(feature_src, feature_dst)

home_path = root / "lib/screens/home_screen.dart"
home = home_path.read_text(encoding="utf-8")

import_anchor = "import 'field_quick_screen.dart';\n"
new_import = "import 'field_intelligence_center_screen.dart';\n"
if new_import not in home:
    if import_anchor not in home:
        raise RuntimeError("ancora de importacao da Home ausente")
    home = home.replace(import_anchor, import_anchor + new_import, 1)

module_anchor = """    _ModuleData(
      title: 'Vistoria rápida',
      tutorialId: 'field_quick',"""
module_block = """    _ModuleData(
      title: 'Central inteligente',
      tutorialId: 'field_center',
      subtitle: 'Busca global, prioridades, evidências, favoritos e diagnóstico ADM',
      icon: Icons.auto_awesome_mosaic_outlined,
      color: AuditarBrand.navy,
      page: () => const FieldIntelligenceCenterScreen(),
    ),
"""
if "tutorialId: 'field_center'" not in home:
    if module_anchor not in home:
        raise RuntimeError("ancora dos modulos da Home ausente")
    home = home.replace(module_anchor, module_block + module_anchor, 1)

# Keep the module visible on Windows navigation as well.
main_ids_anchor = """      'companies',
      'non_conformities',"""
if "'field_center'," not in home:
    if main_ids_anchor not in home:
        raise RuntimeError("lista de modulos principais ausente")
    home = home.replace(
        main_ids_anchor,
        """      'companies',
      'field_center',
      'non_conformities',""",
        1,
    )

nav_ids_anchor = """      'companies',
      'history',
      'non_conformities',"""
if nav_ids_anchor in home:
    home = home.replace(
        nav_ids_anchor,
        """      'companies',
      'field_center',
      'history',
      'non_conformities',""",
        1,
    )

management_anchor = """      'companies',
      'dashboard',
      'non_conformities',"""
if management_anchor in home:
    home = home.replace(
        management_anchor,
        """      'companies',
      'field_center',
      'dashboard',
      'non_conformities',""",
        1,
    )

home_path.write_text(home, encoding="utf-8", newline="\n")

pub_path = root / "pubspec.yaml"
pub = pub_path.read_text(encoding="utf-8")
old_version, new_version = (
    ("3.29.142+284", "3.29.143+285")
    if platform == "android"
    else ("3.30.61+248", "3.30.62+249")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_version)
pub_path.write_text(
    pub.replace(marker, "version: " + new_version, 1),
    encoding="utf-8",
    newline="\n",
)

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

center = feature_dst.read_text(encoding="utf-8")
home = home_path.read_text(encoding="utf-8")
required_center = [
    "class FieldIntelligenceCenterScreen",
    "Busca global",
    "Atalhos favoritos",
    "Central de evidências",
    "Diagnóstico técnico ADM",
    "DeviceSyncService.pendingChangesCount()",
    "MediaSyncService.pendingCount()",
    "EvidenceBackupScreen(company: selectedCompany!)",
]
for snippet in required_center:
    assert snippet in center, "Central Inteligente incompleta: " + snippet
assert "tutorialId: 'field_center'" in home
assert "const FieldIntelligenceCenterScreen()" in home
assert "version: " + new_version in pub_path.read_text(encoding="utf-8")

print("FIELD_INTELLIGENCE_CENTER_OK", platform, new_version)
print("SYNC_DB_AUTH_MEDIA_AI_GS_BYTE_IDENTICAL_OK")
