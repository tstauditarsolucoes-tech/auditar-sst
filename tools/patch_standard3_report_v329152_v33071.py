#!/usr/bin/env python3
"""Padrão Auditar 3 — modelo principal baseado no PDF aprovado.

Escopo:
- adiciona renderer independente;
- torna Padrão Auditar 3 o modelo principal;
- preserva Padrão Auditar e Padrão Auditar 2 como opções;
- não altera banco, sync, autenticação, HTTP, mídia, Drive, IA ou Apps Script.
"""
from pathlib import Path
import hashlib
import re
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_standard3_report_v329152_v33071.py <APP_DIR> <android|windows>"
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
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
    "lib/services/auditar_technical_inspection_pdf_service.dart",
    "lib/services/auditar_standard2_pdf_service.dart",
    "lib/services/report_logo_service.dart",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

shutil.copyfile(
    repo / "feature_sources/auditar_standard3_pdf_service_v329152.dart",
    root / "lib/services/auditar_standard3_pdf_service.dart",
)

rel = "lib/services/report_template_service.dart"
source = read(rel)

if "static const standard1TemplateId = 'auditar_padrao_1';" not in source:
    anchor = "  static const standard2TemplateId = 'auditar_padrao_2';"
    if anchor not in source:
        raise RuntimeError("standard2TemplateId ausente")
    source = source.replace(
        anchor,
        "  static const standard1TemplateId = 'auditar_padrao_1';\n" + anchor,
        1,
    )

pattern = re.compile(
    r"  static const ReportTemplateDefinition\s+"
    r"currentTemplate\s*=\s*ReportTemplateDefinition\(.*?\n  \);",
    re.S,
)
match = pattern.search(source)
if not match:
    raise RuntimeError("currentTemplate ausente")

new_current = """  static const ReportTemplateDefinition currentTemplate = ReportTemplateDefinition(
    id: currentTemplateId,
    name: 'Padrão Auditar 3',
    description: 'Modelo principal de vistoria técnica: Auditar à esquerda, logo cadastrada da empresa à direita, evidência fotográfica e texto técnico em duas colunas.',
    primaryColor: '#1A3456',
    secondaryColor: '#16834A',
    headerTitle: 'RELATÓRIO DE VISTORIA TÉCNICA',
    headerStyle: 'auditar_padrao_3',
    logoMode: 'ambas',
    footerText: 'Auditar Soluções • Medicina Ocupacional e Segurança do Trabalho',
    photoColumns: 1,
    signatureStyle: 'app',
    showCover: false,
    showSummary: false,
    showChecklistDetails: false,
    isBuiltIn: true,
    useLegacyRenderer: false,
  );"""
source = source[:match.start()] + new_current + source[match.end():]

if "id: standard1TemplateId," not in source:
    anchor = "  static const List<ReportTemplateDefinition> builtIns = [\n    currentTemplate,\n"
    if anchor not in source:
        raise RuntimeError("lista builtIns ausente")
    old_model = """    ReportTemplateDefinition(
      id: standard1TemplateId,
      name: 'Padrão Auditar',
      description: 'Modelo anterior de vistoria técnica preservado como alternativa.',
      primaryColor: '#14334A',
      secondaryColor: '#16834A',
      headerTitle: 'RELATÓRIO DE VISTORIA TÉCNICA',
      headerStyle: 'auditar_vistoria_tecnica',
      logoMode: 'ambas',
      footerText: 'Auditar Soluções • Medicina Ocupacional e Segurança do Trabalho',
      photoColumns: 3,
      signatureStyle: 'app',
      showCover: false,
      showSummary: false,
      showChecklistDetails: false,
      isBuiltIn: true,
      useLegacyRenderer: false,
    ),
"""
    source = source.replace(anchor, anchor + old_model, 1)

write(rel, source)

rel = "lib/services/styled_report_pdf_service.dart"
styled = read(rel)

new_import = "import 'auditar_standard3_pdf_service.dart';\n"
if new_import not in styled:
    anchor = "import 'auditar_technical_inspection_pdf_service.dart';\n"
    if anchor not in styled:
        raise RuntimeError("import renderer tecnico anterior ausente")
    styled = styled.replace(anchor, anchor + new_import, 1)

old_route = """    if (template.id == ReportTemplateService.currentTemplateId &&
        template.headerStyle == 'auditar_vistoria_tecnica') {
      return AuditarTechnicalInspectionPdfService.generateInspectionPdf(
        inspectionId,
        header: header,
        template: template,
        executive: executive,
        includeActionPlan: includeActionPlan,
      );
    }

"""
if old_route not in styled:
    raise RuntimeError("rota atual do modelo principal ausente")

new_routes = """    if (template.id == ReportTemplateService.currentTemplateId &&
        template.headerStyle == 'auditar_padrao_3') {
      return AuditarStandard3PdfService.generateInspectionPdf(
        inspectionId,
        header: header,
        template: template,
        executive: executive,
        includeActionPlan: includeActionPlan,
      );
    }

    if (template.id == ReportTemplateService.standard1TemplateId ||
        template.headerStyle == 'auditar_vistoria_tecnica') {
      return AuditarTechnicalInspectionPdfService.generateInspectionPdf(
        inspectionId,
        header: header,
        template: template,
        executive: executive,
        includeActionPlan: includeActionPlan,
      );
    }

"""
styled = styled.replace(old_route, new_routes, 1)
write(rel, styled)

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
    raise SystemExit("PROTECTED_OR_PREVIOUS_REPORTS_MODIFIED: " + repr(changed))

final_template = read("lib/services/report_template_service.dart")
final_styled = read("lib/services/styled_report_pdf_service.dart")
final_service = read("lib/services/auditar_standard3_pdf_service.dart")

assert "name: 'Padrão Auditar 3'" in final_template
assert "name: 'Padrão Auditar'" in final_template
assert "name: 'Padrão Auditar 2'" in final_template
assert "AuditarStandard3PdfService.generateInspectionPdf" in final_styled
assert "_logo(companyLogo, 70, 50)" in final_service
assert "companyLogo ?? auditarLogo" not in final_service
assert "Vale do Leite" not in final_service
assert "version: " + new_version in read("pubspec.yaml")

print("PADRAO_AUDITAR_3_PATCH_OK", platform, new_version)
print("PREVIOUS_REPORT_MODELS_BYTE_IDENTICAL_OK")
print("SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_AI_GS_BYTE_IDENTICAL_OK")
