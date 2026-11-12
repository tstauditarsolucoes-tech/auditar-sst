#!/usr/bin/env python3
"""Android: um painel autoexplicativo, sem substituir os formulários da CIPA.

Pré-requisitos: run_cipa_validation_v1.py e patch_cipa_triage_v1.py.
Altera somente o painel da CIPA e acrescenta fontes CIPA, sem banco,
autenticação, sincronização, fotos, PDF, IA ou Apps Script.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_cipa_guided_home_v1.py <APP_DIR>")
app=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
screen=app/"lib/screens/cipa_management_screen.dart"
guided=app/"lib/screens/cipa_guided_home.dart"
rules=app/"lib/services/cipa_guide_rules.dart"
test=app/"test/cipa_guide_rules_test.dart"
triage=app/"lib/screens/cipa_triage_extension.dart"
assert screen.is_file() and triage.is_file(), (
    "Módulo CIPA/triagem precisa estar montado")
assert not guided.exists() and not rules.exists() and not test.exists(), (
    "Guia já instalado: nenhuma cópia duplicada será feita")
allowed={screen,guided,rules,test}
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in (app/"lib",app/"painel_web_google_apps_script")
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in allowed
}

def once(source,old,new,why):
    count=source.count(old)
    if count!=1:
        raise RuntimeError(f"{why}: encontrado {count} vez(es), esperado uma")
    return source.replace(old,new,1)

content=screen.read_text(encoding="utf-8")
content=once(content,
    "import '../services/cipa_followup_queue.dart';",
    "import '../services/cipa_followup_queue.dart';\n"
    "import '../services/cipa_guide_rules.dart';",
    "import de regras de orientação")
content=once(content,
    "part 'cipa_triage_extension.dart';",
    "part 'cipa_triage_extension.dart';\n"
    "part 'cipa_guided_home.dart';",
    "parte da interface CIPA")
start=content.find("  Widget _panelTab() {")
end=content.find("  Widget _mandateTab()",start)
assert start>=0 and end>start, "Painel atual não identificado"
panel=content[start:end]
anchor="          const SizedBox(height: 10),\n          LayoutBuilder("
panel=once(panel,anchor,
    "          const SizedBox(height: 10),\n"
    "          _cipaGuidedHome(),\n"
    "          const SizedBox(height: 10),\n"
    "          LayoutBuilder(",
    "posicionamento do guia antes dos indicadores")
content=content[:start]+panel+content[end:]
screen.write_text(content,encoding="utf-8",newline="\n")
shutil.copyfile(repo/"feature_sources/cipa_guided_home_v1.dart",guided)
shutil.copyfile(repo/"feature_sources/cipa_guide_rules_v1.dart",rules)
t=(repo/"feature_sources/cipa_guide_rules_test_v1.dart").read_text(
    encoding="utf-8")
t=t.replace("import 'cipa_guide_rules_v1.dart';",
    "import '../lib/services/cipa_guide_rules.dart';")
test.write_text(t,encoding="utf-8",newline="\n")
for path,digest in protected.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,str(path)
assert content.count("_cipaGuidedHome(),")==1
assert "part 'cipa_guided_home.dart';" in content
assert "CipaGuideRules.recommended" in guided.read_text(encoding="utf-8")
print("CIPA_GUIDED_HOME_READY: sem modificações no núcleo ou nos formulários")
