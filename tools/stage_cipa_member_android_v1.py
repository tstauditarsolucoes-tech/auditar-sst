#!/usr/bin/env python3
"""Montar aplicativo EXCLUSIVO do integrante, sem a chave operacional Auditar.

Uso: stage_cipa_member_android_v1.py <flutter-project-dir>
A origem precisa ser um projeto limpo gerado por flutter create com nome
auditar_cipa_membro. Nenhuma fonte do app de técnico é copiada.
"""
from pathlib import Path
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: stage_cipa_member_android_v1.py <APP_DIR>")
repo=Path(__file__).resolve().parents[1]
app=Path(sys.argv[1])
pubspec=app/"pubspec.yaml"
manifest=app/"android/app/src/main/AndroidManifest.xml"
assert pubspec.is_file() and manifest.is_file(), "Execute flutter create antes."
yaml=pubspec.read_text(encoding="utf-8")
assert "name: auditar_cipa_membro" in yaml, (
    "Projeto de membros não pode substituir o app técnico.")
assert "  http:" not in yaml
anchor="\ndependencies:\n"
assert yaml.count(anchor)==1
yaml=yaml.replace(anchor,anchor+"  http: ^1.3.0\n"
    "  image_picker: ^1.2.2\n"
    "  image: ^4.3.0\n"
    "  cryptography: ^2.7.0\n"
    "  flutter_secure_storage: ^11.2.0\n"
    "  path_provider: ^2.1.6\n"
    "  flutter_tts: ^4.2.3\n",1)
pubspec.write_text(yaml,encoding="utf-8")

pairs={
    "feature_sources/cipa_member_app_main_v1.dart":
      "lib/main.dart",
    "feature_sources/cipa_member_identity_v1.dart":
      "lib/services/cipa_member_identity.dart",
    "feature_sources/cipa_member_portal_policy_v1.dart":
      "lib/services/cipa_member_portal_policy.dart",
    "feature_sources/cipa_member_home_alerts_v1.dart":
      "lib/services/cipa_member_home_alerts.dart",
    "feature_sources/cipa_member_api_v1.dart":
      "lib/services/cipa_member_api.dart",
    "feature_sources/cipa_member_draft_store_v1.dart":
      "lib/services/cipa_member_draft_store.dart",
    "feature_sources/cipa_member_offline_cache_v1.dart":
      "lib/services/cipa_member_offline_cache.dart",
    "feature_sources/cipa_member_pending_sync_v1.dart":
      "lib/services/cipa_member_pending_sync.dart",
    "feature_sources/cipa_member_access_header_v1.dart":
      "lib/widgets/cipa_member_access_header.dart",
    "feature_sources/cipa_member_portal_screen_v1.dart":
      "lib/screens/cipa_member_portal_screen.dart",
    "feature_sources/cipa_member_guided_inspection_v1.dart":
      "lib/widgets/cipa_member_guided_inspection.dart",
    "feature_sources/cipa_member_portal_screen_test_v1.dart":
      "test/cipa_member_portal_screen_test.dart",
    "feature_sources/cipa_member_api_test_v1.dart":
      "test/cipa_member_api_test.dart",
    "feature_sources/cipa_member_draft_store_test_v1.dart":
      "test/cipa_member_draft_store_test.dart",
    "feature_sources/cipa_member_offline_cache_test_v1.dart":
      "test/cipa_member_offline_cache_test.dart",
    "feature_sources/cipa_member_pending_sync_test_v1.dart":
      "test/cipa_member_pending_sync_test.dart",
}
for source,target in pairs.items():
    path=app/target
    path.parent.mkdir(parents=True,exist_ok=True)
    text=(repo/source).read_text(encoding="utf-8")
    if target.endswith("_test.dart"):
        text=text.replace(
            "package:auditar_sst/",
            "package:auditar_cipa_membro/")
    path.write_text(text,encoding="utf-8",newline="\n")
# Teste padrão do flutter create referencia o widget antigo; não misturar.
template=app/"test/widget_test.dart"
if template.exists():template.unlink()

xml=manifest.read_text(encoding="utf-8")
assert xml.count("<application")==1
if 'android.permission.INTERNET' not in xml:
    xml=xml.replace("<application",
        '<uses-permission android:name="android.permission.INTERNET"/>\n'
        '    <application',1)
xml=xml.replace('android:label="auditar_cipa_membro"',
                'android:label="Minha CIPA - Auditar"')
manifest.write_text(xml,encoding="utf-8")

# Nenhum código operacional, banco, autenticação técnica ou chave de sync.
all_code="\n".join(p.read_text(encoding="utf-8")
    for p in (app/"lib").rglob("*.dart"))
for forbidden in [
  "String.fromEnvironment('AUDITAR_SYNC_KEY'",
  'import "../database.dart"',
  "import '../database.dart'",
  "device_sync_service.dart",
  "AuthService.login(",
  "management_panel_sync_key",
]:
    assert forbidden not in all_code, "Caminho operacional proibido: "+forbidden
assert "AUDITAR_MEMBER_ENDPOINT" in all_code
assert (app/"lib/screens/cipa_member_portal_screen.dart").is_file()
print("CIPA_MEMBER_ANDROID_SEPARATE_APP_READY_NO_MASTER_KEY")
