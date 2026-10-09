#!/usr/bin/env python3
"""Auditar SST v3.29.170 / v3.30.89 — ajuste responsivo 360–412 px.

Escopo estritamente visual:
- histórico anual da inspeção mensal de extintores usa 3 colunas em telas
  de até 412 px e preserva 4 colunas acima disso;
- não altera banco, sincronização, autenticação, HTTP, mídia/Drive, IA,
  Apps Script ou renderizadores PDF.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_mobile_360_412_v329170_v33089.py <APP_DIR> <android|windows>")

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

rel = "lib/screens/extinguisher_monthly_inspection_screen.dart"
text = read(rel)
old = """            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 4,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
              childAspectRatio: 1.35,
            ),"""
new = """            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount:
                  MediaQuery.sizeOf(context).width <= 412 ? 3 : 4,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
              childAspectRatio: 1.35,
            ),"""
if new not in text:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            "historico anual de extintores: esperado 1 grid fixo, encontrado " + str(count)
        )
    text = text.replace(old, new, 1)
write(rel, text)

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_release, new_release = (
    ("3.29.169+311", "3.29.170+312")
    if platform == "android"
    else ("3.30.88+275", "3.30.89+276")
)
marker = "version: " + old_release
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_release)
write(pub_rel, pub.replace(marker, "version: " + new_release, 1))

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

print("MOBILE_360_412_RESPONSIVE_OK", platform, new_release)
print("EXTINGUISHER_YEAR_GRID_3_COLUMNS_UP_TO_412_OK")
print("PROTECTED_CORE_BYTE_IDENTICAL_OK")
