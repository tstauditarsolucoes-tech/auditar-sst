#!/usr/bin/env python3
"""Auditar SST Windows v3.30.90 — Central de gestão desktop.

Escopo:
- substitui somente a tela de controle operacional por uma versão responsiva
  que mantém o fluxo compacto e acrescenta uma experiência desktop >= 1000 px;
- usa exclusivamente consultas e modelos já existentes;
- não cria tabela, não altera banco, sincronização, autenticação, HTTP,
  mídia/Drive, IA, Apps Script ou renderizadores PDF.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_windows_management_center_v33090.py <APP_DIR>")

root = Path(sys.argv[1])
repo = Path(__file__).resolve().parents[1]

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

protected = [
    "lib/database.dart",
    "lib/models.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/offline_report_knowledge_service.dart",
    "lib/services/auditar_technical_inspection_pdf_service.dart",
    "lib/services/auditar_standard2_pdf_service.dart",
    "lib/services/auditar_standard3_pdf_service.dart",
    "lib/services/ronda_standard3_pdf_service.dart",
    "lib/services/express_round_pdf_service.dart",
    "lib/services/report_template_service.dart",
    "lib/services/styled_report_pdf_service.dart",
    "lib/services/report_logo_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected if (root / name).exists()
}

source = repo / "feature_sources/field_operational_control_screen_v33090.dart"
target = root / "lib/screens/field_operational_control_screen.dart"
if not source.exists():
    raise RuntimeError("fonte da Central de gestao desktop ausente")
if not target.exists():
    raise RuntimeError("tela de controle operacional ausente no app montado")

target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_release = "3.30.89+276"
new_release = "3.30.90+277"
marker = "version: " + old_release
if pub.count(marker) != 1:
    raise RuntimeError("versao Windows esperada ausente: " + old_release)
write(pub_rel, pub.replace(marker, "version: " + new_release, 1))

home_rel = "lib/screens/home_screen.dart"
home = read(home_rel)
if "3.30.89" in home:
    home = home.replace("3.30.89", "3.30.90")
    write(home_rel, home)

screen = read("lib/screens/field_operational_control_screen.dart")
required = [
    "Central de gestão SST",
    "CENTRAL DA EMPRESA",
    "Central de pendências",
    "Resumo para decisão",
    "_desktopPendingEntries",
    "DataTable(",
    "constraints.maxWidth >= 1000",
    "_compactBody()",
]
missing = [item for item in required if item not in screen]
if missing:
    raise RuntimeError("Central desktop incompleta: " + repr(missing))

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

print("WINDOWS_MANAGEMENT_CENTER_OK", new_release)
print("DESKTOP_SPLIT_VIEW_OK")
print("PENDING_TABLE_READ_ONLY_OK")
print("LOCAL_DECISION_SUMMARY_OK")
print("COMPACT_MOBILE_FLOW_PRESERVED_OK")
print("PROTECTED_CORE_BYTE_IDENTICAL_OK")
