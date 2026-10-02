#!/usr/bin/env python3
"""Regressão estática do Padrão Auditar 3."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: regression_padrao_auditar3_v329152_v33071.py <APP_DIR>")

root = Path(sys.argv[1])
template = (root / "lib/services/report_template_service.dart").read_text(encoding="utf-8")
pdf = (root / "lib/services/auditar_technical_inspection_pdf_service.dart").read_text(encoding="utf-8")
styled = (root / "lib/services/styled_report_pdf_service.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

assert "name: 'Padrão Auditar 3'" in template
assert "headerTitle: 'RELATÓRIO DE VISTORIA TÉCNICA'" in template
assert "headerStyle: 'auditar_vistoria_tecnica'" in template
assert "AuditarTechnicalInspectionPdfService.generateInspectionPdf" in styled

required = [
    "RELATÓRIO DE VISTORIA TÉCNICA",
    "IDENTIFICAÇÃO DA EMPRESA",
    "RAZÃO SOCIAL",
    "CNPJ",
    "LOCALIDADE",
    "DATA DA VISTORIA",
    "ENDEREÇO COMPLETO",
    "ReportLogoService.forCompany(header)",
    "_logo(companyLogo, 58, 52)",
    "'Local'",
    "'Situação'",
    "'Risco'",
    "'Correção'",
    "PRIORIDADE:",
    "CONCLUSÃO",
    "Relatório elaborado com os registros fotográficos",
    "Referências gerais:",
    "TÉCNICO EM SEGURANÇA DO TRABALHO",
    "Página ${context.pageNumber}/${context.pagesCount}",
]
for marker in required:
    assert marker in pdf, "missing: " + marker

# A logo direita é dinâmica da empresa, não um asset fixo de cliente.
assert "Vale do Leite" not in pdf
assert "sstLogo" not in pdf
assert "_logo(companyLogo, 58, 52)" in pdf

assert (
    "version: 3.29.152+294" in pub
    or "version: 3.30.71+258" in pub
)

print("PADRAO_AUDITAR_3_REGRESSION_OK")
