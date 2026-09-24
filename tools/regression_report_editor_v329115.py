#!/usr/bin/env python3
"""Regression: advanced PDF templates without changes to the existing app core."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); expected=sys.argv[2]
assert 'version: '+expected in (root/'pubspec.yaml').read_text(encoding='utf-8')
service=(root/'lib/services/report_template_service.dart').read_text(encoding='utf-8')
editor=(root/'lib/screens/report_template_library_screen.dart').read_text(encoding='utf-8')
header=(root/'lib/services/report_header_pdf_service.dart').read_text(encoding='utf-8')
assert all(marker in service for marker in [
 'advancedHeader','showHeader','headerSubtitle','headerAlignment',
 'leftLogoSource','rightLogoSource','leftLogoBase64','rightLogoBase64',
 'logoSize',"map['advancedHeader'] == true", "'leftLogoBase64': leftLogoBase64",
])
for marker in ['_pickLogo(',"allowedExtensions: const ['png','jpg','jpeg']",
 'logoSize=v.round()', "Text('Mostrar cabeçalho no relatório')",
 "'Prévia esquemática do cabeçalho'",'ReportTemplateService.newCustomId()']:
 assert marker in editor, marker
assert "if (source == 'cliente') return company;" in header
assert 'template.showHeader' in header
assert 'template.publicTitle' in header
assert "source != 'personalizada'" in header
for name in ['styled_report_pdf_service.dart','performance_report_pdf_service.dart',
 'auditar_standard2_pdf_service.dart','express_round_pdf_service.dart']:
 s=(root/'lib/services'/name).read_text(encoding='utf-8')
 assert 'ReportHeaderPdfService.header(' in s, name
 assert 'companyLogo ?? auditarLogo' not in s, name
 assert 'companyLogo ?? sstLogo' not in s, name
assert "return title.isEmpty ? 'RELATÓRIO DE VISTORIA' : title;" in service
assert (root/'test/report_template_editor_model_test.dart').exists()
print('REPORT_EDITOR_ADVANCED_REGRESSION_OK',expected)