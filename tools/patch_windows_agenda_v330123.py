#!/usr/bin/env python3
"""Integra agenda Windows v3.30.123 na interface, sem modificar backend/sync."""
from pathlib import Path
import hashlib,shutil,sys
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1]
home=root/'lib/screens/home_screen.dart'
admin=root/'lib/screens/admin_center_screen.dart'
hub=root/'lib/screens/admin_operational_hub_screen.dart'
dst=root/'lib/screens/technician_agenda_screen.dart'
pub=root/'pubspec.yaml'
protected=['lib/database.dart','lib/models.dart','lib/services/auth_service.dart',
'lib/services/device_sync_service.dart','lib/services/sync_coordinator.dart',
'lib/services/media_sync_service.dart','lib/services/apps_script_http.dart',
'painel_web_google_apps_script/Code.gs','painel_web_google_apps_script/MultiUser.gs']
digest={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected if (root/p).exists()}
assert not dst.exists()
shutil.copyfile(repo/'feature_sources/technician_agenda_screen_v330123.dart',dst)
a=admin.read_text(encoding='utf8')
assert a.count("'Central Operacional ADM'")==1
assert a.count("import 'admin_operational_hub_screen.dart';")==1
a=a.replace("import 'admin_operational_hub_screen.dart';",
"import 'admin_operational_hub_screen.dart';\nimport 'technician_agenda_screen.dart';",1)
key="'Central Operacional ADM'"
pos=a.index(key);anchor=a.rfind("_action(",0,pos)
start=a.rfind("\n",0,anchor)+1;indent=a[start:anchor]
assert anchor>=0 and not indent.strip()
extra="""_action(
  'Agenda e distribuição de serviços',
  'ADM atribui serviços; técnicos atualizam suas atividades.',
  Icons.event_note_outlined,
  () => _open(const TechnicianAgendaScreen()),
),
"""
a=a[:start]+indent+extra.replace("\n","\n"+indent)+a[start:]
admin.write_text(a,encoding='utf8')
h=hub.read_text(encoding='utf8')
assert h.count("import 'quick_visit_screen.dart';")==1
h=h.replace("import 'quick_visit_screen.dart';",
"import 'quick_visit_screen.dart';\nimport 'technician_agenda_screen.dart';",1)
marker="'NCs e prazos'"
assert h.count(marker)==1
pos=h.index(marker)
start=h.rfind("_shortcut(",0,pos)
line=h.rfind("\n",0,start)+1
indent=h[line:start]
assert start>=0 and not indent.strip()
extra="""_shortcut(
  'Agenda de visitas',
  Icons.event_outlined,
  () => _go(const TechnicianAgendaScreen()),
),
"""
h=h[:line]+indent+extra.replace("\n","\n"+indent)+h[line:]
hub.write_text(h,encoding='utf8')
s=home.read_text(encoding='utf8')
assert s.count("import 'admin_center_screen.dart';")==1
assert s.count("  List<_ModuleData> get _modules => [")==1
s=s.replace("import 'admin_center_screen.dart';",
"import 'admin_center_screen.dart';\nimport 'technician_agenda_screen.dart';",1)
marker="  List<_ModuleData> get _modules => ["
insertion="""  List<_ModuleData> get _modules => [
        if (AuthService.isSignedIn &&
            (AuthService.isAdmin || AuthService.currentUser?.role == 'tecnico'))
          _ModuleData(
            title: 'Minha agenda',
            tutorialId: 'agenda',
            subtitle: 'Serviços e visitas atribuídos pela gestão',
            icon: Icons.event_note_outlined,
            color: AuditarBrand.navy,
            page: () => const TechnicianAgendaScreen(),
          ),
"""
s=s.replace(marker,insertion,1)
home.write_text(s,encoding='utf8')
version=pub.read_text(encoding='utf8')
assert version.count('version: 3.30.122+309')==1
pub.write_text(version.replace('version: 3.30.122+309',
'version: 3.30.123+310',1),encoding='utf8')
for path,old in digest.items():
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==old,path
print('AGENDA_WINDOWS_330123_OK_NO_BACKEND_CHANGES')
