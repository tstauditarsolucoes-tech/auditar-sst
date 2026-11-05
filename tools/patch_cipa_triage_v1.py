#!/usr/bin/env python3
"""Incremento CIPA Android; instalar após tools/run_cipa_validation_v1.py.

Não muda dados existentes, sincronização, autenticação, fotos, IA,
relatórios, assinaturas, login de membros ou backend. Falha com segurança
quando o módulo CIPA atual é diferente do esperado.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_cipa_triage_v1.py <APP_DIR>")
app=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
base=app/"lib/screens/cipa_management_screen.dart"
participation=app/"lib/screens/cipa_participation_screen.dart"
triage=app/"lib/screens/cipa_triage_extension.dart"
service=app/"lib/services/cipa_followup_queue.dart"
test=app/"test/cipa_followup_queue_test.dart"
existing=app/"lib/services/cipa_participation_rules.dart"
assert all(p.is_file() for p in [base,participation,existing]), (
    "Instale primeiro o módulo CIPA de participação atual")
assert not triage.exists() and not service.exists() and not test.exists(), (
    "Triagem já instalada ou arquivos ocupados: não duplicar")

allowed={base,participation,triage,service,test}
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in (app/"lib", app/"painel_web_google_apps_script")
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in allowed
}

def once(source,old,new,label):
    n=source.count(old)
    if n!=1:
        raise RuntimeError(f"{label}: {n} correspondência(s); esperado 1")
    return source.replace(old,new,1)

b=base.read_text(encoding="utf-8")
b=once(b,
    "import '../services/cipa_participation_rules.dart';",
    "import '../services/cipa_participation_rules.dart';\n"
    "import '../services/cipa_followup_queue.dart';",
    "import do agregador CIPA")
b=once(b,
    "part 'cipa_participation_screen.dart';",
    "part 'cipa_participation_screen.dart';\n"
    "part 'cipa_triage_extension.dart';",
    "parte exclusiva da triagem")
base.write_text(b,encoding="utf-8",newline="\n")

p=participation.read_text(encoding="utf-8")
p=once(p,
    "       if (_cipaSimpleMode) _cipaQuickStart(),",
    "       if (_cipaSimpleMode) _cipaQuickStart(),\n"
    "       _cipaTriageCard(),",
    "painel antes dos botões do módulo")
p=once(p,
    "    'observation': 'Situação observada',",
    "    'observation': 'Situação observada',\n"
    "    'observation_review': 'Situação conferida pela gestão',\n"
    "    'progress_review': 'Andamento conferido pela gestão',",
    "rótulos na linha do tempo")
participation.write_text(p,encoding="utf-8",newline="\n")
shutil.copyfile(repo/"feature_sources/cipa_triage_extension_v1.dart",triage)
shutil.copyfile(repo/"feature_sources/cipa_followup_queue_v1.dart",service)

t=(repo/"feature_sources/cipa_followup_queue_test_v1.dart").read_text(
    encoding="utf-8")
t=t.replace("import 'cipa_participation_rules_v1.dart';",
    "import '../lib/services/cipa_participation_rules.dart';")
t=t.replace("import 'cipa_followup_queue_v1.dart';",
    "import '../lib/services/cipa_followup_queue.dart';")
test.write_text(t,encoding="utf-8",newline="\n")

for path,sha in protected.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha,str(path)
assert "_cipaTriageCard()," in participation.read_text()
assert "observation_review" in triage.read_text()
assert "progress_review" in triage.read_text()
assert "part 'cipa_triage_extension.dart';" in base.read_text()
print("CIPA_TRIAGE_ANDROID_READY: OTHER_LIB_AND_GS_FILES_UNCHANGED")
