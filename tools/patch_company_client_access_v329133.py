#!/usr/bin/env python3
"""Admin-only company client access next to report emails. No sync/DB/GS/auth mutations."""
from pathlib import Path
import hashlib,shutil,sys
root=Path(sys.argv[1])
source=Path(__file__).resolve().parents[1]/'feature_sources/company_client_access_section_v329133.dart'
target=root/'lib/widgets/company_client_access_section.dart'
screen=root/'lib/screens/companies_screen.dart'
protected=[
'lib/database.dart','lib/services/device_sync_service.dart',
'lib/services/sync_coordinator.dart','lib/services/media_sync_service.dart',
'lib/services/drive_service.dart','lib/services/apps_script_http.dart',
'lib/services/auth_service.dart','lib/services/ai_assistant_service.dart',
'painel_web_google_apps_script/Code.gs',
'painel_web_google_apps_script/MultiUser.gs',
'painel_web_google_apps_script/ClientPortal.gs',
'painel_web_google_apps_script/ReportEmail.gs',
]
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected}
s=screen.read_text(encoding='utf-8')
def one(old,new,label):
 global s
 if s.count(old)!=1:raise SystemExit(label+' expected once: '+str(s.count(old)))
 s=s.replace(old,new,1)

one("import '../models.dart';",
"import '../models.dart';\nimport '../services/auth_service.dart';\nimport '../widgets/company_client_access_section.dart';",
'company imports')
anchor="""                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Enviar relatório mensal'),"""
insertion="""                if (AuthService.isAdmin && company != null)
                  CompanyClientAccessSection(
                    key: ValueKey('client_access_' + company.id),
                    company: company,
                    reportEmail: reportEmail,
                    reportRecipient: reportRecipient,
                  ),
                if (AuthService.isAdmin && company == null)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 10),
                    child: Text(
                      'Salve a empresa para cadastrar o acesso do cliente '
                      'ao Painel Gerencial.',
                      style: TextStyle(fontSize: 12),
                    ),
                  ),
"""
one(anchor,insertion+anchor,'company email-section insertion')
shutil.copyfile(source,target)
screen.write_text(s,encoding='utf-8',newline='\n')
changed=[p for p,h in before.items()
 if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
if changed:raise SystemExit('PROTECTED CORE FILES CHANGED: '+repr(changed))
print('COMPANY_CLIENT_ACCESS_INLINE_OK')
print('SYNC_DATABASE_GS_AUTH_BYTE_IDENTICAL_OK')
