#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'app/Auditar_SST_v1_5_dashboard')
expected=sys.argv[2] if len(sys.argv)>2 else None

pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
templates=(root/'lib/services/report_template_service.dart').read_text(encoding='utf-8')
styled=(root/'lib/services/styled_report_pdf_service.dart').read_text(encoding='utf-8')
library=(root/'lib/screens/report_template_library_screen.dart').read_text(encoding='utf-8')
report=(root/'lib/screens/report_screen.dart').read_text(encoding='utf-8')
settings=(root/'lib/screens/settings_screen.dart').read_text(encoding='utf-8')
pdf=(root/'lib/services/pdf_service.dart').read_text(encoding='utf-8')

if expected:
    assert f'version: {expected}' in pub, f'versão esperada ausente: {expected}'

for name in [
    'Padrão Auditar atual',
    'Auditar Executivo',
    'Auditar Fotográfico',
    'Auditar Obra',
    'Auditar Técnico Clean',
    'Auditar NR-12',
]:
    assert name in templates, f'modelo ausente: {name}'

assert "id: currentTemplateId" in templates and 'useLegacyRenderer: true' in templates
assert "fallback: currentTemplateId" in templates
assert 'orElse: () => currentTemplate' in templates
assert "_selectionKey(String companyId)" in templates
assert "report_templates_custom_v1" in templates
assert "saveCustom" in templates and "deleteCustom" in templates

# Padrão é individual por usuário autenticado; empresa pode sobrescrever.
assert "_userDefaultPrefix = 'report_template_user_default_v1'" in templates
assert 'AuthService.currentUser?.id' in templates
assert 'selectDefaultForCurrentUser' in templates
assert 'selectedDefaultForCurrentUser' in templates
assert 'final userDefault = await selectedDefaultForCurrentUser();' in templates
assert 'fallback: userDefault.id' in templates
assert 'orElse: () => userDefault' in templates

assert 'StyledReportPdfService.generateInspectionPdf' in pdf
assert 'if (!reportTemplate.useLegacyRenderer)' in pdf
# O fluxo antigo deve continuar presente depois do roteamento.
assert 'final answers = await db.getAnswers(inspectionId);' in pdf
assert 'final reportFooter = await db.getSetting(' in pdf

assert 'Modelo visual do relatório' in report
assert '_openReportTemplateLibrary' in report
assert 'selectedReportTemplate' in report
assert '_sharePdf({required bool executive})' in report
assert 'ReportFileService.savePdfLocally' in report

assert 'Platform.isWindows' in library
assert 'Salvar como novo modelo' in library
assert 'Pré-visualizar' in library
assert 'Definir como meu padrão' in library
assert 'Usar nesta empresa' in library
assert 'Meu padrão' in library
assert 'Padrão da empresa' in library
assert "fullEditor: Platform.isWindows" in library
assert 'Biblioteca e editor de modelos de relatório' in settings
assert 'Modelos de relatório' in settings

for marker in ['Situação encontrada', 'Risco', 'Correção recomendada', 'Plano de ação', 'Checklist da vistoria', 'Conclusão']:
    assert marker in styled, f'seção do novo renderer ausente: {marker}'

# Arquivos novos de modelos não podem chamar a sincronização nem alterar o backend.
new_code='\n'.join([templates, styled, library])
for forbidden in ['DeviceSyncService', 'MediaSyncService', 'AppsScriptHttp', 'WebServiceConfig', 'syncNow(', 'device_pull', 'device_push']:
    assert forbidden not in new_code, f'acoplamento proibido detectado nos modelos: {forbidden}'

print('REPORT_TEMPLATES_REGRESSION_OK: legado preservado; 5 modelos novos; padrão individual por usuário + override por empresa; editor/seleção isolados do sync.')
