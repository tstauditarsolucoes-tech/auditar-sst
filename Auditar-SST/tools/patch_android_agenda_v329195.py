#!/usr/bin/env python3
"""Android 3.29.195: somente atalho Minha agenda, sem banco/auth/sync/fotos/GS."""
from pathlib import Path
import hashlib,shutil,sys
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1]
home=root/'lib/screens/home_screen.dart'
pub=root/'pubspec.yaml'
dst=root/'lib/screens/technician_agenda_screen.dart'
protected=['lib/database.dart','lib/models.dart','lib/services/auth_service.dart',
'lib/services/device_sync_service.dart','lib/services/sync_coordinator.dart',
'lib/services/media_sync_service.dart','lib/services/apps_script_http.dart',
'painel_web_google_apps_script/Code.gs','painel_web_google_apps_script/MultiUser.gs']
digest={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected if (root/p).is_file()}
assert not dst.exists(), 'Agenda already present; do not install twice'
shutil.copyfile(repo/'feature_sources/technician_agenda_screen_v330123.dart',dst)
s=home.read_text(encoding='utf8')
marker="  List<_ModuleData> get _modules => ["
assert s.count(marker)==1
assert s.count("import 'admin_center_screen.dart';")==1
s=s.replace("import 'admin_center_screen.dart';",
"import 'admin_center_screen.dart';\nimport 'technician_agenda_screen.dart';",1)
s=s.replace(marker,"""  List<_ModuleData> get _modules => [
        if (AuthService.isSignedIn &&
            (AuthService.isAdmin || AuthService.currentUser?.role == 'tecnico'))
          _ModuleData(
            title: 'Minha agenda',
            tutorialId: 'agenda',
            subtitle: 'Visitas e tarefas da equipe Auditar',
            icon: Icons.event_note_outlined,
            color: AuditarBrand.navy,
            page: () => const TechnicianAgendaScreen(),
          ),
""",1)
home.write_text(s,encoding='utf8')
text=pub.read_text(encoding='utf8')
assert text.count('version: 3.29.194+336')==1
pub.write_text(text.replace('version: 3.29.194+336','version: 3.29.195+337',1),encoding='utf8')
for path,original in digest.items():
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==original,path
print('AGENDA_ANDROID_329195_UI_ONLY_NO_CORE_CHANGED')
