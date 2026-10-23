#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1]);a=(p/'lib/screens/admin_center_screen.dart').read_text(encoding='utf8')
u=(p/'lib/screens/admin_technician_supervision_screen.dart').read_text(encoding='utf8')
assert a.count("import 'admin_technician_supervision_screen.dart';")==1
assert a.count('const AdminTechnicianSupervisionScreen()')==1
assert a.count('const ClientTreatmentInboxScreen()')==1
for marker in ['AuthService.isSignedIn && AuthService.isAdmin',
 'technician_supervision_v1','Ativo recentemente','Timer.periodic','Copiar resumo']:
 assert marker in u,marker
assert 'version: 3.30.122+309' in (p/'pubspec.yaml').read_text(encoding='utf8')
print('WINDOWS_ADM_SUPERVISION_V330120_ACCEPTANCE_OK')
assert (p/'lib/screens/admin_operational_hub_screen.dart').is_file()
assert a.count('const AdminOperationalHubScreen()')==1
assert a.count('Criar e gerenciar contas')==1
u=(p/'lib/screens/users_screen.dart').read_text(encoding='utf8')
assert 'role = user?.role' in u
assert 'class UsersScreen extends StatefulWidget' in u
assert 'AuthService.saveUser(' in u
assert 'Novo usuário' in u
assert 'cliente' in u.lower()
