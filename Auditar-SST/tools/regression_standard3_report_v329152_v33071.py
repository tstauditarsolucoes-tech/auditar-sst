#!/usr/bin/env python3
"""Regressão do Padrão Auditar 3."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: regression_standard3_report_v329152_v33071.py <APP_DIR>")

root = Path(sys.argv[1])
template = (root / "lib/services/report_template_service.dart").read_text(encoding="utf-8")
styled = (root / "lib/services/styled_report_pdf_service.dart").read_text(encoding="utf-8")
service = (root / "lib/services/auditar_standard3_pdf_service.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

for needle in (
    "name: 'Padrão Auditar 3'",
    "headerStyle: 'auditar_padrao_3'",
    "name: 'Padrão Auditar'",
    "name: 'Padrão Auditar 2'",
):
    assert needle in template, needle

for needle in (
    "AuditarStandard3PdfService.generateInspectionPdf",
    "ReportTemplateService.standard1TemplateId",
    "AuditarTechnicalInspectionPdfService.generateInspectionPdf",
):
    assert needle in styled, needle

for needle in (
    "RELATÓRIO DE VISTORIA TÉCNICA",
    "IDENTIFICAÇÃO DA EMPRESA",
    "RAZÃO SOCIAL",
    "LOCALIDADE",
    "ENDEREÇO COMPLETO",
    "_paragraph('Situação'",
    "_paragraph('Risco'",
    "_paragraph('Correção'",
    "PRIORIDADE:",
    "CONCLUSÃO",
    "TÉCNICO EM SEGURANÇA DO TRABALHO",
    "final companyLogo = await ReportLogoService.forCompany(header);",
    "_logo(companyLogo, 70, 50)",
):
    assert needle in service, needle

assert "_logo(companyLogo ?? auditarLogo" not in service
assert "companyLogo ?? auditarLogo" not in service
assert "Vale do Leite" not in service
assert "vale do leite" not in service.lower()

assert (
    "version: 3.29.152+294" in pub
    or "version: 3.29.153+295" in pub
    or "version: 3.29.154+296" in pub
    or "version: 3.29.155+297" in pub
    or "version: 3.30.71+258" in pub
    or "version: 3.30.72+259" in pub
    or "version: 3.30.73+260" in pub
    or "version: 3.30.74+261" in pub
)

print("PADRAO_AUDITAR_3_REGRESSION_OK")
print("COMPANY_LOGO_ONLY_ON_RIGHT_OK")
print("PREVIOUS_REPORT_MODELS_PRESERVED_OK")
