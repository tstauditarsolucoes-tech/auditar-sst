#!/usr/bin/env python3
"""NR-18 links to the *existing* company action plan, without creating/closing NCs.
Never alters SST database, sync, auth, media, AI or Apps Script.
"""
from pathlib import Path
import hashlib
import re
import sys

root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ("android","windows")
old,new=(("3.29.190+332","3.29.191+333") if platform=="android"
         else ("3.30.113+300","3.30.114+301"))
nr=root/"lib/screens/nr18_field_checklist_screen.dart"
assert nr.is_file()
pub=root/"pubspec.yaml"
v=pub.read_text(encoding="utf-8")
assert v.count("version: "+old)==1, "unexpected version"
protected=[p for folder in ("lib","painel_web_google_apps_script")
    for p in (root/folder).rglob("*") if p.is_file() and p!=nr]
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
s=nr.read_text(encoding="utf-8")
import_anchor="import 'new_inspection_screen.dart';"
assert s.count(import_anchor)==1
assert "import 'action_plan_screen.dart';" not in s
s=s.replace(import_anchor,import_anchor+"\nimport 'action_plan_screen.dart';",1)
# Aceita o Dart format com vírgulas opcionais em Text(...) e no item do Wrap.
pattern=re.compile(r"label\s*:\s*const\s+Text\s*\(\s*'Abrir Vistoria'\s*,?\s*\)\s*,?\s*\)\s*,")
hits=list(pattern.finditer(s))
assert len(hits)==1, "expected exactly one NR18 inspection quick action"
addition="""\n                  OutlinedButton.icon(
                    onPressed:authorized?()=>_open(
                      ActionPlanScreen(companyId:widget.company.id)):null,
                    icon:const Icon(Icons.assignment_turned_in_outlined),
                    label:const Text('Plano de ação da obra')),
"""
s=s[:hits[0].end()]+addition+s[hits[0].end():]
nr.write_text(s,encoding="utf-8")
pub.write_text(v.replace("version: "+old,"version: "+new),encoding="utf-8")
for p,expected in before.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,str(p)
print("NR18_ACTION_PLAN_NAVIGATION_READY",platform,new,"CORE_AND_GS_UNCHANGED")
