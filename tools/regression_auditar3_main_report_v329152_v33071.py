#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
service = (root / "lib/services/report_template_service.dart").read_text(encoding="utf-8")
pdf = (root / "lib/services/auditar_technical_inspection_pdf_service.dart").read_text(encoding="utf-8")
styled = (root / "lib/services/styled_report_pdf_service.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

for marker in (
    "name: 'Padrão Auditar 3'",
    "headerStyle: 'auditar_vistoria_tecnica'",
):
    assert marker in service, marker

for marker in (
    "ReportLogoService.forCompany(header)",
    "_logo(companyLogo, 58, 52)",
    "RELATÓRIO DE VISTORIA TÉCNICA",
    "IDENTIFICAÇÃO DA EMPRESA",
    "RAZÃO SOCIAL",
    "LOCALIDADE",
    "DATA DA VISTORIA",
    "ENDEREÇO COMPLETO",
    "_paragraph('Local', issue.location)",
    "_paragraph('Situação', issue.situation)",
    "_paragraph('Risco', issue.risk)",
    "_paragraph('Correção', issue.correction)",
    "PRIORIDADE:",
    "CONCLUSÃO",
    "Referências gerais:",
    "TÉCNICO EM SEGURANÇA DO TRABALHO",
):
    assert marker in pdf, marker

assert "assets/branding/sst_green_official.png" not in pdf
assert "AuditarTechnicalInspectionPdfService.generateInspectionPdf" in styled
assert "template.headerStyle == 'auditar_vistoria_tecnica'" in styled
assert (
    "version: 3.29.152+294" in pub
    or "version: 3.30.71+258" in pub
)

print("PADRAO_AUDITAR_3_REGRESSION_OK")
print("DEFAULT_RENDERER_ROUTE_PRESERVED_OK")
