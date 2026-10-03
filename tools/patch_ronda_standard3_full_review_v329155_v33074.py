#!/usr/bin/env python3
"""Ronda Padrão Auditar 3 - revisão visual completa do modelo.

Escopo isolado:
- renderer do PDF da Ronda;
- versão do app.

Não altera IA, sincronização, banco, autenticação, HTTP, mídia, Drive,
Apps Script ou modelos de relatório anteriores.
"""
from pathlib import Path
import hashlib
import shutil
import sys

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

source = repo / "feature_sources/ronda_standard3_pdf_service_v329155.dart"
if not source.exists():
    raise RuntimeError("renderer Ronda v329155 ausente")
shutil.copyfile(source, root / "lib/services/ronda_standard3_pdf_service.dart")

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_version, new_version = (
    ("3.29.154+296", "3.29.155+297")
    if platform == "android"
    else ("3.30.73+260", "3.30.74+261")
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
    "seenRecordIds",
    "_captionFromTitle",
    "_compactConclusion",
    "_compactReferences",
    "_auditarBrand",
    "fullAddress",
    "registeredCompany?.logoPath ?? company.logoPath",
    "_logo(companyLogo, 82, 58)",
):
    assert snippet in renderer, "revisao completa ausente: " + snippet

assert "companyLogo ?? auditarLogo" not in renderer
assert "VALE DO LEITE" not in renderer.upper()
assert "LATICÍNIOS VALE DO LEITE" not in renderer.upper()
assert "version: " + new_version in read(pub_rel)

print("RONDA_STANDARD3_FULL_REVIEW_OK", platform, new_version)
print("CLIENT_LOGO_DYNAMIC_SINGLE_HEADER_OK")
print("AI_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_GS_PREVIOUS_REPORTS_BYTE_IDENTICAL_OK")
