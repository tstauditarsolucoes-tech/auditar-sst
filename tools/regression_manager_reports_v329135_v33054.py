#!/usr/bin/env python3
"""Static and structural regression for existing, company-scoped report engine."""
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1])
s=(root/'lib/screens/manager_reports_screen.dart').read_text(encoding='utf-8')
ui=(root/'lib/screens/company_detail_screen.dart').read_text(encoding='utf-8')
test=(root/'test/manager_reports_module_test.dart').read_text(encoding='utf-8')
for token in ('ManagerReportKind.pending','ManagerReportKind.activities',
    'ManagerReportKind.resolved','ManagerReportKind.monthly',
    'getNonConformityRows(', 'getPendingActions(', 'getInspectionHistory(',
    'getSstRecords(', 'companyId: company.id', 'verified_at',
    'completion_date','getPhotosForAnswer(', 'getCompletionPhotos(',
    'PdfPreview(', 'LinearProgressIndicator()', 'allowSharing: true',
    'includePhotos','Ações na seleção','Atividades no período',
    'DocumentDeliveryService.send(', 'ReportRecipients.parse(',
    'Enviar relatório gerencial?', 'bytes.length > 7500000',
    'specificSearch', 'String search =', 'Busca específica (opcional)'):
    if token not in s:raise SystemExit('MANAGER_REPORTS missing '+token)
for token in ('manager_reports_screen.dart','ManagerReportsScreen(company: widget.company)',
    'Relatórios gerenciais'):
    if token not in ui:raise SystemExit('MANAGER_REPORTS menu missing '+token)
for token in ('open backlog','actual verified date','recorded completion date',
              'does not include NC or action'):
    if token not in test:raise SystemExit('MANAGER_REPORTS missing test '+token)
for forbidden in ('DeviceSyncService.', 'MediaSyncService.', 'AppsScriptHttp.',
    'AuthService.saveUser(', 'CREATE TABLE', 'ALTER TABLE'):
    if forbidden in s:raise SystemExit('MANAGER_REPORTS forbidden operation '+forbidden)
if ui.count("import 'manager_reports_screen.dart';")!=1:
    raise SystemExit('MANAGER_REPORTS duplicated import')
print('MANAGER_REPORTS_REGRESSION_OK')
