#!/usr/bin/env python3
"""Ronda - paridade visual com o modelo de referência.

Somente substitui o renderer isolado do Padrão Auditar 3 da Ronda
e incrementa versão. IA, sync, DB, auth, HTTP, mídia, Drive e Apps Script
permanecem byte-a-byte.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_ronda_standard3_visual_parity_v329154_v33073.py "
        "<APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")
repo = Path(__file__).resolve().parent.parent

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
    "lib/services/auditar_technical_inspection_pdf_service.dart",
    "lib/services/auditar_standard2_pdf_service.dart",
    "lib/services/auditar_standard3_pdf_service.dart",
    "lib/services/report_logo_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    p: hashlib.sha256((root / p).read_bytes()).hexdigest()
    for p in protected
}

source = repo / "feature_sources/ronda_standard3_pdf_service_v329154.dart"
if not source.exists():
    raise RuntimeError("fonte visual Ronda v329154 ausente")
shutil.copyfile(source, root / "lib/services/ronda_standard3_pdf_service.dart")

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_version, new_version = (
    ("3.29.153+295", "3.29.154+296")
    if platform == "android"
    else ("3.30.72+259", "3.30.73+260")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao base esperada ausente: " + old_version)
write(pub_rel, pub.replace(marker, "version: " + new_version, 1))

changed = [
    p for p, digest in before.items()
    if hashlib.sha256((root / p).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

renderer = read("lib/services/ronda_standard3_pdf_service.dart")
for snippet in (
    "AppDatabase.instance.getCompanies(onlyActive: false)",
    "_logo(auditarLogo, 104, 56)",
    "_logo(companyLogo, 82, 58)",
    "flex: 48",
    "flex: 52",
    "fontSize: 10.2",
    "_compactTitle",
    "_compactReferences",
    "_logo(auditarLogo, 90, 34)",
):
    assert snippet in renderer, "paridade visual ausente: " + snippet

assert "companyLogo ?? auditarLogo" not in renderer
assert "version: " + new_version in read(pub_rel)

print("RONDA_STANDARD3_VISUAL_PARITY_OK", platform, new_version)
print("AI_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_GS_BYTE_IDENTICAL_OK")
