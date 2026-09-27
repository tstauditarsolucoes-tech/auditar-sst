#!/usr/bin/env python3
"""Refine individual client logins for multiple contacts on ONE company panel.

Presentation-only patch. Existing auth list/save endpoints and data model are reused.
Never change synchronization, media, GS, authentication core or database.
"""
from pathlib import Path
import hashlib
import shutil
import sys

root = Path(sys.argv[1])
repo = Path(__file__).resolve().parents[1]
widget = root / 'lib/widgets/company_client_access_section.dart'
test_target = root / 'test/company_multi_client_access_test.dart'
source = repo / 'feature_sources/company_multi_client_access_v329136.dart'
test_source = repo / 'feature_sources/company_multi_client_access_test_v329136.dart'
protected = [
    'lib/database.dart',
    'lib/services/device_sync_service.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/drive_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/auth_service.dart',
    'lib/services/ai_assistant_service.dart',
    'lib/screens/companies_screen.dart',
    'painel_web_google_apps_script/Code.gs',
    'painel_web_google_apps_script/MultiUser.gs',
    'painel_web_google_apps_script/ClientPortal.gs',
    'painel_web_google_apps_script/ClientPortal.html',
    'painel_web_google_apps_script/ReportEmail.gs',
]
before = {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
          for p in protected}
old = widget.read_text(encoding='utf-8')
new = source.read_text(encoding='utf-8')
if 'class ClientCompanyAccessRules' in old:
    raise SystemExit('Multiple client login patch already applied.')
for marker in ('class CompanyClientAccessSection',
               'AuthService.listUsers()', 'AuthService.saveUser(',
               'companyIds:[widget.company.id]'):
    if marker not in old or marker not in new:
        raise SystemExit('Existing client account implementation mismatch: ' + marker)
for marker in ('ClientCompanyAccessRules.belongsTo',
               'ClientCompanyAccessRules.duplicates',
               "email.text=user?.email??'';",
               'Adicionar outro e-mail de acesso',
               'Os demais acessos e os e-mails de envio dos relatórios permanecem iguais.'):
    if marker not in new:
        raise SystemExit('Incomplete multi-client UI: ' + marker)
shutil.copyfile(source, widget)
shutil.copyfile(test_source, test_target)
changed = [p for p, digest in before.items()
           if hashlib.sha256((root / p).read_bytes()).hexdigest() != digest]
if changed:
    raise SystemExit('Protected auth/sync/GS/DB/media/source changed: ' + repr(changed))
print('MULTI_CLIENT_SAME_COMPANY_UI_OK')
print('AUTH_SYNC_GS_DATABASE_MEDIA_IDENTICAL_OK')
