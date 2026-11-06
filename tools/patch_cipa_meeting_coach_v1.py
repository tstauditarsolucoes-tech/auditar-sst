#!/usr/bin/env python3
"""Acrescenta reunião assistida ao guia original, sem trocar formulários/DB.

Aplicar DEPOIS de patch_cipa_guided_home_v1.py.
Não altera autenticação, Apps Script, sync, atas, presença, regras CIPA ou NCs.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_cipa_meeting_coach_v1.py <APP_DIR>")
root=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
screen=root/"lib/screens/cipa_management_screen.dart"
home=root/"lib/screens/cipa_meeting_coach_home.dart"
rules=root/"lib/services/cipa_meeting_coach_rules.dart"
test=root/"test/cipa_meeting_coach_rules_test.dart"
guide=root/"lib/screens/cipa_guided_home.dart"
if not screen.is_file() or not guide.is_file():
    raise SystemExit("Instale primeiro o painel de orientação CIPA existente.")
if any(p.exists() for p in (home,rules,test)):
    raise SystemExit("Reunião assistida já instalada; não sobrescrever.")
allowed={screen,home,rules,test}
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in (root/"lib",root/"test",root/"painel_web_google_apps_script")
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in allowed
}
content=screen.read_text(encoding="utf-8")
def once(old,new,reason):
    global content
    count=content.count(old)
    if count!=1:raise RuntimeError(
        f"{reason}: {count} ocorrências; cancelado sem mudar arquivos")
    content=content.replace(old,new,1)

once("import '../services/cipa_guide_rules.dart';",
    "import '../services/cipa_guide_rules.dart';\n"
    "import '../services/cipa_meeting_coach_rules.dart';",
    "importar regras puras de conferência")
once("part 'cipa_guided_home.dart';",
    "part 'cipa_guided_home.dart';\n"
    "part 'cipa_meeting_coach_home.dart';",
    "ligar extensão à tela existente")
once("          _cipaGuidedHome(),\n          const SizedBox(height: 10),",
    "          _cipaGuidedHome(),\n          const SizedBox(height: 10),\n"
    "          _cipaMeetingCoachCard(),\n          const SizedBox(height: 10),",
    "exibir cartão após guia original")

files={
    home:repo/"feature_sources/cipa_meeting_coach_home_v1.dart",
    rules:repo/"feature_sources/cipa_meeting_coach_rules_v1.dart",
}
for target,origin in files.items():
    shutil.copyfile(origin,target)
test_content=(repo/"feature_sources/cipa_meeting_coach_rules_test_v1.dart"
    ).read_text(encoding="utf-8")
assert test_content.count("import 'cipa_meeting_coach_rules_v1.dart';")==1
test.write_text(test_content.replace(
    "import 'cipa_meeting_coach_rules_v1.dart';",
    "import '../lib/services/cipa_meeting_coach_rules.dart';"),
    encoding="utf-8",newline="\n")
screen.write_text(content,encoding="utf-8",newline="\n")
for p,digest in protected.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,(
        "Arquivo fora do escopo foi alterado: "+str(p))
assert content.count("_cipaMeetingCoachCard(),")==1
assert "part 'cipa_meeting_coach_home.dart';" in content
print("CIPA_MEETING_COACH_INSTALLED_NO_AUTH_SYNC_OR_DATA_CHANGE")
