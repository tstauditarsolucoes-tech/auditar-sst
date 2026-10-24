#!/usr/bin/env python3
from pathlib import Path
import sys
r=Path(sys.argv[1])
h=(r/'lib/screens/home_screen.dart').read_text(encoding='utf8')
a=(r/'lib/screens/technician_agenda_screen.dart').read_text(encoding='utf8')
assert h.count("title: 'Minha agenda'")==1
assert h.count("const TechnicianAgendaScreen()")==1
for key in ["'operation':'list'","'operation':'status'","'operation':'create'","AuthService.isAdmin"]:
 assert key in a,key
assert 'version: 3.29.195+337' in (r/'pubspec.yaml').read_text(encoding='utf8')
print('ANDROID_AGENDA_329195_REGRESSION_OK')
