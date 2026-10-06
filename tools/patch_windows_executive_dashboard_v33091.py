#!/usr/bin/env python3
"""Auditar SST Windows v3.30.91 — Painel Executivo Auditar.

Escopo estritamente aditivo e somente leitura:
- adiciona tela executiva por empresa usando consultas já existentes;
- integra o acesso na Central de Gestão desktop;
- não cria tabelas e não altera banco, sync, autenticação, HTTP, mídia/Drive,
  IA, Apps Script ou renderizadores PDF.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_windows_executive_dashboard_v33091.py <APP_DIR>")

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

copies = [
    (
        "feature_sources/executive_dashboard_screen_v33091.dart",
        "lib/screens/executive_dashboard_screen.dart",
    ),
    (
        "feature_sources/field_operational_control_screen_v33091.dart",
        "lib/screens/field_operational_control_screen.dart",
    ),
]
for source, target in copies:
    src = repo / source
    dst = root / target
    if not src.exists():
        raise RuntimeError("fonte ausente: " + source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_release = "3.30.90+277"
new_release = "3.30.91+278"
marker = "version: " + old_release
if pub.count(marker) != 1:
    raise RuntimeError("versao Windows esperada ausente: " + old_release)
write(pub_rel, pub.replace(marker, "version: " + new_release, 1))

home_rel = "lib/screens/home_screen.dart"
home = read(home_rel)
if "3.30.90" in home:
    write(home_rel, home.replace("3.30.90", "3.30.91"))

dashboard = read("lib/screens/executive_dashboard_screen.dart")
central = read("lib/screens/field_operational_control_screen.dart")
required_dashboard = [
    "Painel Executivo Auditar",
    "ÍNDICE AUDITAR SST",
    "O que foi realizado neste mês",
    "Evolução mensal",
    "Resumo para decisão",
    "Prioridades da gestão",
    "Top prioridades abertas",
    "Reincidências",
    "Modo apresentação",
    "indicador gerencial interno",
]
missing = [item for item in required_dashboard if item not in dashboard]
if missing:
    raise RuntimeError("Painel Executivo incompleto: " + repr(missing))
if "ExecutiveDashboardScreen" not in central or "Painel executivo" not in central:
    raise RuntimeError("Central de Gestão sem acesso ao Painel Executivo")

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

print("WINDOWS_EXECUTIVE_DASHBOARD_OK", new_release)
print("EXECUTIVE_SCORE_INTERNAL_ONLY_OK")
print("MONTHLY_RESULTS_AND_EVOLUTION_OK")
print("PRESENTATION_MODE_OK")
print("MANAGEMENT_CENTER_ENTRY_OK")
print("PROTECTED_CORE_BYTE_IDENTICAL_OK")
