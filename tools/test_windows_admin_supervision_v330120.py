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
assert 'version: 3.30.121+308' in (p/'pubspec.yaml').read_text(encoding='utf8')
print('WINDOWS_ADM_SUPERVISION_V330120_ACCEPTANCE_OK')