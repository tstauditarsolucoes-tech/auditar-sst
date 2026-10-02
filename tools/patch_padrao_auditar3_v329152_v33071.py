#!/usr/bin/env python3
"""Auditar SST v3.29.152 / v3.30.71

Promove o relatório técnico fornecido pelo usuário para o modelo principal:
- nome interno no app: Padrão Auditar 3;
- renderer principal já é auditar_vistoria_tecnica;
- não altera sincronização, banco, autenticação, transporte, mídia, IA ou GS.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_padrao_auditar3_v329152_v33071.py <APP_DIR> <android|windows>"
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

# O ID do template principal permanece o mesmo para preservar preferências e
# compatibilidade; só mudam nome/descrição pública dentro da biblioteca.
rel = "lib/services/report_template_service.dart"
service = read(rel)
old = """    name: 'Padrão Auditar',
    description: 'Relatório de vistoria técnica com identificação da empresa, evidências à esquerda e descrição/correção à direita.',"""
new = """    name: 'Padrão Auditar 3',
    description: 'Modelo principal da Auditar: relatório de vistoria técnica com logo da empresa cadastrada, evidência à esquerda e Local/Situação/Risco/Correção/Prioridade à direita.',"""
if new not in service:
    if old not in service:
        raise RuntimeError("template principal esperado nao localizado")
    service = service.replace(old, new, 1)
write(rel, service)

# Versão isolada, sem migração.
rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.151+293", "3.29.152+294")
    if platform == "android"
    else ("3.30.70+257", "3.30.71+258")
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

template = read("lib/services/report_template_service.dart")
pdf = read("lib/services/auditar_technical_inspection_pdf_service.dart")
styled = read("lib/services/styled_report_pdf_service.dart")

assert "name: 'Padrão Auditar 3'" in template
assert "headerStyle: 'auditar_vistoria_tecnica'" in template
assert "AuditarTechnicalInspectionPdfService.generateInspectionPdf" in styled
assert "template.headerStyle == 'auditar_vistoria_tecnica'" in styled

for marker in (
    "RELATÓRIO DE VISTORIA TÉCNICA",
    "IDENTIFICAÇÃO DA EMPRESA",
    "RAZÃO SOCIAL",
    "LOCALIDADE",
    "DATA DA VISTORIA",
    "ENDEREÇO COMPLETO",
    "ReportLogoService.forCompany(header)",
    "_logo(companyLogo",
    "_paragraph('Situação'",
    "_paragraph('Risco'",
    "_paragraph('Correção'",
    "PRIORIDADE:",
    "CONCLUSÃO",
    "Referências gerais:",
    "TÉCNICO EM SEGURANÇA DO TRABALHO",
):
    assert marker in pdf, "marcador ausente: " + marker

assert "sstLogo" not in pdf
assert "version: " + new_version in read("pubspec.yaml")

print("PADRAO_AUDITAR_3_OK", platform, new_version)
print("SYNC_DB_AUTH_HTTP_MEDIA_AI_DRIVE_GS_BYTE_IDENTICAL_OK")
