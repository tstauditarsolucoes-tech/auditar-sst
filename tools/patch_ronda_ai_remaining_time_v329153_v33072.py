#!/usr/bin/env python3
"""Auditar SST v3.29.153 / v3.30.72

Mudanca visual isolada na IA por foto da Ronda:
- preserva exatamente o fluxo de analise atual;
- troca o contador de tempo decorrido por uma estimativa de tempo restante;
- ao atingir a estimativa, exibe "IA finalizando análise..." em vez de contar para cima.

Nao altera IA, sincronizacao, banco, autenticacao, HTTP, midia, Drive ou Apps Script.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_ronda_ai_remaining_time_v329153_v33072.py "
        "<APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

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
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

rel = "lib/screens/express_round_screen.dart"
screen = read(rel)

old_fields = """  Timer? _aiPhotoTimer;
  int _aiPhotoElapsedSeconds = 0;
"""
new_fields = """  Timer? _aiPhotoTimer;
  int _aiPhotoElapsedSeconds = 0;
  static const int _aiPhotoEstimatedSeconds = 50;

  String get _aiPhotoStatusLabel {
    final remaining = _aiPhotoEstimatedSeconds - _aiPhotoElapsedSeconds;
    if (remaining > 0) {
      return 'IA analisando foto • ~${remaining}s restantes';
    }
    return 'IA finalizando análise...';
  }
"""
if new_fields not in screen:
    if screen.count(old_fields) != 1:
        raise RuntimeError(
            "campos atuais do timer da IA nao localizados: "
            + str(screen.count(old_fields))
        )
    screen = screen.replace(old_fields, new_fields, 1)

old_label = """                  analyzingWithAi
                      ? 'IA analisando foto • ${_aiPhotoElapsedSeconds}s'
                      : 'IA foto · analisar evidência',"""
new_label = """                  analyzingWithAi
                      ? _aiPhotoStatusLabel
                      : 'IA foto · analisar evidência',"""
if new_label not in screen:
    if screen.count(old_label) != 1:
        raise RuntimeError(
            "rotulo atual do tempo decorrido nao localizado: "
            + str(screen.count(old_label))
        )
    screen = screen.replace(old_label, new_label, 1)

write(rel, screen)

rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.152+294", "3.29.153+295")
    if platform == "android"
    else ("3.30.71+258", "3.30.72+259")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_version)
write(rel, pub.replace(marker, "version: " + new_version, 1))

changed = [
    name
    for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

final_round = read("lib/screens/express_round_screen.dart")
assert "static const int _aiPhotoEstimatedSeconds = 50;" in final_round
assert "final remaining = _aiPhotoEstimatedSeconds - _aiPhotoElapsedSeconds;" in final_round
assert "IA analisando foto • ~${remaining}s restantes" in final_round
assert "IA finalizando análise..." in final_round
assert "IA analisando foto • ${_aiPhotoElapsedSeconds}s" not in final_round
assert "Timer.periodic(const Duration(seconds: 1)" in final_round
assert "version: " + new_version in read("pubspec.yaml")

print("RONDA_AI_REMAINING_TIME_OK", platform, new_version)
print("AI_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_GS_BYTE_IDENTICAL_OK")
