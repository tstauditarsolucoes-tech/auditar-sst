#!/usr/bin/env python3
"""CI guard: isolated per-company document delivery, existing sync/AI untouched."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); expected=sys.argv[2]
read=lambda path:(root/path).read_text(encoding='utf-8')
assert f'version: {expected}' in read('pubspec.yaml')
service=read('lib/services/document_delivery_service.dart')
center=read('lib/screens/document_dispatch_center_screen.dart')
home=read('lib/screens/home_screen.dart')
email=read('lib/services/report_email_service.dart')
rounds=read('lib/screens/express_round_screen.dart')
report=read('lib/screens/report_screen.dart')
for text in ['_historyKey(String companyId)','DocumentDeliveryService','requestId: requestId',
             "'report_email_history'",'AuthService.canAccessCompany(companyId)',
             "'SENT'", "'FAILED'"]:
    assert text in service,text
for text in ['Central de documentos e envios',"getInspectionHistory(companyId: c.id)",
             "type: 'DDS'","type: 'TREINAMENTO_SESSAO'", "type:'OBSERVACAO_SEGURANCA'",
             'getNonConformityRows(companyId:c.id,includeClosed:true)',
             "'Ronda Expressa'",'Enviar PDF pronto','FilePicker.platform.pickFiles',
             'DocumentDeliveryService.history(c.id)','Documento']:
    assert text in center,text
assert "tutorialId: 'document_delivery'" in home
assert 'String? requestId,' in email
assert 'DocumentDeliveryService.send(' in report
assert 'DocumentDispatchDialog.send(context, company: widget.company' in rounds
assert 'DocumentDispatchDialog.send(context, company: widget.company' in read('lib/screens/safety_observations_screen.dart')
assert 'DocumentDispatchDialog.send(context, company: matches.first' in read('lib/screens/sst_records_screen.dart')
assert 'DocumentDispatchDialog.send(context, company: widget.company' in read('lib/screens/training_records_screen.dart')
for path in ['lib/services/device_sync_service.dart','lib/services/sync_coordinator.dart',
             'lib/services/media_sync_service.dart','lib/services/ai_assistant_service.dart',
             'lib/database.dart','painel_web_google_apps_script/Code.gs']:
    assert (root/path).is_file(),path
print('DOCUMENT_DELIVERY_PER_COMPANY_REGRESSION_OK',expected)