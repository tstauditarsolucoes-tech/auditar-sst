#!/usr/bin/env python3
"""Auditar SST v3.29.143 / v3.30.62 - Central Inteligente SST."""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_smart_sst_center_v329143_v33062.py <APP_DIR> <android|windows>")

root=Path(sys.argv[1])
platform=sys.argv[2].strip().lower()
if platform not in ("android","windows"):
    raise SystemExit("plataforma invalida")

protected=[
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/screens/report_screen.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
]
before={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in protected}

feature=Path(__file__).resolve().parents[1]/"feature_sources"/"smart_sst_center_v329143.dart"
target=root/"lib/screens/smart_sst_center_screen.dart"
if not feature.exists():
    raise RuntimeError("feature source da Central Inteligente ausente")
shutil.copyfile(feature,target)

home_path=root/"lib/screens/home_screen.dart"
home=home_path.read_text(encoding="utf-8")
anchor="import 'settings_screen.dart';\n"
if anchor not in home:
    raise RuntimeError("import anchor do Home nao localizado")
if "import 'smart_sst_center_screen.dart';" not in home:
    home=home.replace(anchor,anchor+"import 'smart_sst_center_screen.dart';\n",1)

module_anchor="""    _ModuleData(
      title: 'Melhorias',
      tutorialId: 'improvements',"""
module="""    _ModuleData(
      title: 'Central inteligente',
      tutorialId: 'smart_center',
      subtitle: 'Busca global, evidências, recorrências, linha do tempo e diagnóstico',
      icon: Icons.hub_outlined,
      color: const Color(0xFF176B5E),
      page: () => const SmartSstCenterScreen(),
    ),
"""
if module_anchor not in home:
    raise RuntimeError("ponto do modulo Melhorias nao localizado")
if "tutorialId: 'smart_center'" not in home:
    home=home.replace(module_anchor,module+module_anchor,1)

home=home.replace(
"""      'routine',
      'improvements',""",
"""      'routine',
      'smart_center',
      'improvements',"""
)
home_path.write_text(home,encoding="utf-8",newline="\n")

pub_path=root/"pubspec.yaml"
pub=pub_path.read_text(encoding="utf-8")
old_version,new_version=(("3.29.142+284","3.29.143+285") if platform=="android" else ("3.30.61+248","3.30.62+249"))
marker="version: "+old_version
if pub.count(marker)!=1:
    raise RuntimeError("versao esperada ausente: "+old_version)
pub_path.write_text(pub.replace(marker,"version: "+new_version,1),encoding="utf-8",newline="\n")

changed=[name for name,digest in before.items() if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: "+repr(changed))

home=home_path.read_text(encoding="utf-8")
center=target.read_text(encoding="utf-8")
assert "tutorialId: 'smart_center'" in home
assert "SmartSstCenterScreen()" in home
assert "class SmartSstCenterScreen" in center
assert "Buscar em todo o app" in center
assert "Recorrências" in center
assert "ACAO_AUDITAR" in center
assert "Diagnóstico técnico • ADM" in center
assert "version: "+new_version in pub_path.read_text(encoding="utf-8")
print("SMART_SST_CENTER_OK",platform,new_version)
print("SYNC_DB_AUTH_MEDIA_AI_REPORT_GS_BYTE_IDENTICAL_OK")
