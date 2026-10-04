#!/usr/bin/env python3
"""Oculta risco e prioridade apenas no card-resumo gerencial do relatório.

Não remove os dados do registro e não altera IA, sincronização, banco,
autenticação, mídia, Drive, Ronda ou Padrão Auditar 3.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_checklist_summary_clean_v329159_v33078.py <APP_DIR> <android|windows>")

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
    "lib/screens/checklist_screen.dart",
    "lib/screens/express_round_screen.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/offline_report_knowledge_service.dart",
    "lib/widgets/offline_report_inline_suggestions.dart",
    "lib/widgets/offline_report_template_picker.dart",
    "lib/services/express_round_pdf_service.dart",
    "lib/services/ronda_standard3_pdf_service.dart",
    "lib/services/auditar_standard3_pdf_service.dart",
    "lib/services/auditar_standard2_pdf_service.dart",
    "lib/services/report_template_service.dart",
    "lib/services/report_logo_service.dart",
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

rel = "lib/services/styled_report_pdf_service.dart"
source = read(rel)
start = source.find("  static pw.Widget _issueBlock(")
end = source.find("  static pw.Widget _photos(", start)
if start < 0 or end < 0:
    raise RuntimeError("card-resumo gerencial nao localizado")

block = source[start:end]

priority_line = "    final priority = _priorityForIssue(data);\n"
risk_block = """    final risk = a.riskIdentified.trim().isNotEmpty
        ? a.riskIdentified.trim()
        : (data.nc?.riskIdentified.trim().isNotEmpty == true
            ? data.nc!.riskIdentified.trim()
            : 'Risco associado à condição identificada deve ser confirmado no local.');
"""
priority_ui = """              pw.SizedBox(width: 6),
              _priorityChip(priority),
"""
risk_ui = "          _labelValue('Risco', risk),\n"

# Os dois elementos visuais solicitados devem existir uma única vez no card.
for needle, label in [
    (priority_ui, "chip prioridade do card"),
    (risk_ui, "linha risco do card"),
]:
    count = block.count(needle)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1, encontrado {count}")
    block = block.replace(needle, "", 1)

# As variáveis internas podem mudar entre versões do renderer. Quando ainda
# estiverem presentes, removemos apenas para evitar warning; sua ausência não
# é erro porque os dados continuam no registro/modelo.
if priority_line in block:
    block = block.replace(priority_line, "", 1)
if risk_block in block:
    block = block.replace(risk_block, "", 1)

for required in (
    "_labelValue('Situação encontrada', problem)",
    "_labelValue('Correção recomendada', recommendation)",
    "_labelValue('Referência', reference)",
):
    if required not in block:
        raise RuntimeError("campo essencial do card ausente: " + required)

source = source[:start] + block + source[end:]
write(rel, source)

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_version, new_version = (
    ("3.29.158+300", "3.29.159+301")
    if platform == "android"
    else ("3.30.77+264", "3.30.78+265")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao base esperada ausente: " + old_version)
write(pub_rel, pub.replace(marker, "version: " + new_version, 1))

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_FUNCTIONALITY_MODIFIED: " + repr(changed))

final_source = read(rel)
final_start = final_source.find("  static pw.Widget _issueBlock(")
final_end = final_source.find("  static pw.Widget _photos(", final_start)
final_block = final_source[final_start:final_end]

assert "_labelValue('Risco', risk)" not in final_block
assert "_priorityChip(priority)" not in final_block
assert "_labelValue('Situação encontrada', problem)" in final_block
assert "_labelValue('Correção recomendada', recommendation)" in final_block
assert "_labelValue('Referência', reference)" in final_block
assert "version: " + new_version in read(pub_rel)

print("CHECKLIST_SUMMARY_CLEAN_PATCH_OK", platform, new_version)
print("RISK_HIDDEN_ONLY_FROM_SUMMARY_CARD_OK")
print("PRIORITY_CLASSIFICATION_HIDDEN_ONLY_FROM_SUMMARY_CARD_OK")
print("SITUATION_CORRECTION_REFERENCE_PRESERVED_OK")
print("DATA_FIELDS_AND_CHECKLIST_UI_BYTE_IDENTICAL_OK")
print("AI_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_RONDA_GS_STANDARD3_BYTE_IDENTICAL_OK")
