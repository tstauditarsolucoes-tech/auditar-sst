#!/usr/bin/env python3
"""Worksite progress scoped by existing company ID; no database or sync edits."""
from pathlib import Path
import hashlib, shutil, sys
root=Path(sys.argv[1])
platform=sys.argv[2]
assert platform in ('android','windows')
repo=Path(__file__).resolve().parents[1]
quick=root/'lib/screens/quick_visit_screen.dart'
dest=root/'lib/screens/worksite_followup_screen.dart'
assert quick.exists() and not dest.exists()
protected=[p for folder in ('lib','painel_web_google_apps_script')
           for p in (root/folder).rglob('*') if p.is_file() and p!=quick]
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
shutil.copyfile(repo/'feature_sources/worksite_followup_screen_v329178.dart',dest)
shutil.copyfile(repo/'feature_sources/worksite_followup_test_v329178.dart',
  root/'test/worksite_followup_test.dart')
s=quick.read_text(encoding='utf-8')
anchor="import 'safety_observations_screen.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport 'worksite_followup_screen.dart';",1)
anchor="          _action(\n            'Pendências da empresa',"
assert s.count(anchor)==1
addition="""          if (_organization.type(c.id) == 'Obra' ||
              RegExp(r'\\\\bobra\\\\b', caseSensitive: false).hasMatch(c.name) ||
              _organization.group(c.id).toLowerCase().contains('construtora'))
            _action(
              'Acompanhamento desta obra',
              'Etapa, situação, diário de campo e registros SST',
              Icons.construction_outlined,
              WorksiteFollowupScreen(
                company: c, groupName: _organization.group(c.id)),
            ),
"""
# Raw Dart regex uses a single backslash for word boundaries.
addition=addition.replace(r'\\b',r'\b')
s=s.replace(anchor,addition+anchor,1)
quick.write_text(s,encoding='utf-8',newline='\n')
pub=root/'pubspec.yaml'
v=pub.read_text(encoding='utf-8')
old,new=('3.29.177+319','3.29.178+320') if platform=='android' else ('3.30.100+287','3.30.101+288')
assert v.count('version: '+old)==1, ('Version not matched',old)
pub.write_text(v.replace('version: '+old,'version: '+new),encoding='utf-8',newline='\n')
for path,digest in before.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,str(path)
print('WORKSITE_FOLLOWUP_READY: protected lib and Central unchanged',platform)
