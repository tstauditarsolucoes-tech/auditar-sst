#!/usr/bin/env python3
"""Install company-scoped managerial reports using existing read paths and PDF.

No GS, schema, synchronization, media, auth or AI code changes.
"""
from pathlib import Path
import hashlib, shutil, sys
root=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
source=repo/'feature_sources/manager_reports_module_v329135.dart'
test_source=repo/'feature_sources/manager_reports_module_test_v329135.dart'
target=root/'lib/screens/manager_reports_screen.dart'
test_target=root/'test/manager_reports_module_test.dart'
company=root/'lib/screens/company_detail_screen.dart'
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
if target.exists():raise SystemExit('Existing management report screen: review before replacing')
s=company.read_text(encoding='utf-8')
def once(old,new,label):
 global s
 if s.count(old)!=1:raise SystemExit(label+' must occur once: '+str(s.count(old)))
 s=s.replace(old,new,1)
once("import 'management_panel_screen.dart';",
     "import 'management_panel_screen.dart';\nimport 'manager_reports_screen.dart';",
     'manager report import')
once("""        _shortcut(
          icon: Icons.description_outlined,
          title: 'PGR + IA',""",
     """        _shortcut(
          icon: Icons.summarize_outlined,
          title: 'Relatórios gerenciais',
          subtitle: 'Pendências, ações, atividades e correções da empresa',
          onTap: () => _open(ManagerReportsScreen(company: widget.company)),
        ),
        _shortcut(
          icon: Icons.description_outlined,
          title: 'PGR + IA',""",
     'company quick action')
shutil.copyfile(source,target)
shutil.copyfile(test_source,test_target)
company.write_text(s,encoding='utf-8',newline='\n')
changed=[p for p,h in before.items()
         if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
if changed:raise SystemExit('PROTECTED SYNC_DB_MEDIA_AUTH_GS_AI MODIFIED '+repr(changed))
print('MANAGER_REPORTS_ANDROID_WINDOWS_ISOLATED_OK')
print('MANAGER_REPORTS_CORE_FILES_BYTE_IDENTICAL_OK')
