#!/usr/bin/env python3
"""Static regressions for selectable institutional and Performance reports."""
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]);version=sys.argv[2]
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
templates=(root/'lib/services/report_template_service.dart').read_text(encoding='utf-8')
styled=(root/'lib/services/styled_report_pdf_service.dart').read_text(encoding='utf-8')
performance=(root/'lib/services/performance_report_pdf_service.dart').read_text(encoding='utf-8')
standard=(root/'lib/services/auditar_standard2_pdf_service.dart').read_text(encoding='utf-8')
legacy=(root/'lib/services/pdf_service.dart').read_text(encoding='utf-8')
ronda=(root/'lib/services/express_round_pdf_service.dart').read_text(encoding='utf-8')
resolver=(root/'lib/services/report_logo_service.dart').read_text(encoding='utf-8')
logo=root/'assets/branding/sst_green_official.png'
assert logo.is_file()
assert hashlib.sha256(logo.read_bytes()).hexdigest()=='0d068782c48f34996fe4251bd60c869930f21805b62ab3d8178b0e8b247eb106'
assert 'version: '+version in pub
assert 'assets/branding/sst_green_official.png' in pub
assert "standard2TemplateId = 'auditar_padrao_2'" in templates
assert "name: 'Padrão Auditar 2'" in templates
assert 'AuditarStandard2PdfService.generateInspectionPdf' in styled
assert 'companyLogo ?? auditarLogo' in styled
assert 'companyLogo ?? sstLogo' in performance
assert 'final body = <pw.Widget>[];' in performance
assert "'Risco'" not in performance[performance.index('static pw.Widget _issueRow'):performance.index('static pw.Widget _technicalLine')]
assert 'final body = <pw.Widget>[];' in performance
assert 'companyLogo ?? auditarLogo' in legacy
assert 'companyLogo ?? auditarIcon' in legacy
assert 'ReportLogoService.forCompany' in styled
assert 'ReportLogoService.forCompany' in performance
assert 'ReportLogoService.forCompany' in standard
assert 'ReportLogoService.forCompany' in legacy
assert 'ReportLogoService.forCompany' in ronda
assert "assets/branding/sst_green_official.png" in ronda
assert '_pdfLogo(companyLogo ?? auditarLogo' in ronda
assert 'restoreCompanyLogos(' in resolver and 'Duration(seconds: 6)' in resolver
assert 'RELATÓRIO DE INSPEÇÃO DE SEGURANÇA DO TRABALHO' in standard
assert 'CONFORMIDADES / NÃO CONFORMIDADES' in standard
assert '31.576.433/0001-13' in standard
assert 'RESPONSÁVEL PELA EMPRESA' in standard
assert 'MEDIDAS DE CORREÇÃO NECESSÁRIAS' in standard
assert 'pw.MultiPage' in standard
assert '_gallery(' in standard
for banned in ['_fineForReport(', 'reportFineValues', 'Multa (referência)']:
    assert banned not in standard
print('REPORT_MODELS_SST_GREEN_AND_AUDITAR2_OK',version)
