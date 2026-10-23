#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1])
home=(root/'lib/screens/home_screen.dart').read_text(encoding='utf8')
admin=(root/'lib/screens/admin_center_screen.dart').read_text(encoding='utf8')
hub=(root/'lib/screens/admin_operational_hub_screen.dart').read_text(encoding='utf8')
agenda=(root/'lib/screens/technician_agenda_screen.dart').read_text(encoding='utf8')
assert home.count("title: 'Minha agenda'")==1
assert home.count('const TechnicianAgendaScreen()')==1
assert admin.count('Agenda e distribuição de serviços')==1
assert hub.count('Agenda de visitas')==1
for marker in ["'action':'agenda_tecnicos_v1'","AuthService.isSignedIn",
 "'operation':'create'","'operation':'status'","'operation':'list'"]:
 assert marker in agenda,marker
assert 'version: 3.30.123+310' in (root/'pubspec.yaml').read_text(encoding='utf8')
print('AGENDA_WINDOWS_330123_REGRESSION_OK')
