#!/usr/bin/env python3
"""Somente apresentação: função da CIPA ao lado do nome do membro.

Usar depois do guia/triagem CIPA. Não implementa login externo nem altera
autenticação, armazenamento, sincronização, GS, dados, mídia, PDF ou Drive.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_cipa_member_label_v1.py <APP_DIR>")
app=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
screen=app/"lib/screens/cipa_management_screen.dart"
identity=app/"lib/services/cipa_member_identity.dart"
header=app/"lib/widgets/cipa_member_access_header.dart"
test=app/"test/cipa_member_identity_test.dart"
header_test=app/"test/cipa_member_access_header_test.dart"
assert screen.is_file() and (app/"lib/screens/cipa_guided_home.dart").is_file(), (
    "Instale primeiro o módulo CIPA guiado atual")
assert not any(p.exists() for p in [identity,header,test,header_test]), (
    "Identidade já adicionada: nunca sobrescrever a implementação")

allowed={screen,identity,header,test,header_test}
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in [app/"lib",app/"painel_web_google_apps_script"]
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in allowed
}
def once(source,old,new,why):
    count=source.count(old)
    if count!=1:
        raise RuntimeError(f"{why}: {count} correspondência(s), esperado 1")
    return source.replace(old,new,1)

source=screen.read_text(encoding="utf-8")
source=once(source,
    "import '../services/cipa_guide_rules.dart';",
    "import '../services/cipa_guide_rules.dart';\n"
    "import '../services/cipa_member_identity.dart';",
    "import da apresentação do nome do membro")

start=source.find("  Widget _membersTab()")
end=source.find("  Widget _meetingsTab()",start)
assert start>=0 and end>start,"Não localizar o cartão original do integrante"
section=source[start:end]
section=once(section,
    """          title: Text(
            item.title,
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),""",
    """          title: Text(
            CipaMemberIdentityLabel.displayName(
              name:item.title,
              cipaRole:(item.payload['cipaRole'] ?? '').toString(),
            ),
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),""",
    "Mostrar função da CIPA junto ao nome")
source=source[:start]+section+source[end:]
screen.write_text(source,encoding="utf-8",newline="\n")

for suffix,target in [
    ("cipa_member_identity_v1.dart",identity),
    ("cipa_member_access_header_v1.dart",header),
    ("cipa_member_identity_test_v1.dart",test),
    ("cipa_member_access_header_test_v1.dart",header_test),
]:
    content=(repo/"feature_sources"/suffix).read_text(encoding="utf-8")
    if target==test:
        content=content.replace("import 'cipa_member_identity_v1.dart';",
            "import '../lib/services/cipa_member_identity.dart';")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(content,encoding="utf-8",newline="\n")

for p,digest in protected.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,str(p)
assert "CipaMemberIdentityLabel.displayName(" in screen.read_text()
assert "CipaMemberAccessHeader" in header.read_text()
print("CIPA_MEMBER_NAME_ROLE_DISPLAY_READY: PROTECTED_FILES_IDENTICAL")
