#!/usr/bin/env python3
"""Instalar código isolado de portal CIPA (NÃO habilita login individual).

Acesso real permanece bloqueado até backend com validação de sessão e
escopo por empresa/mandato/membro, sem reutilizar sync/DB de técnico.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_cipa_member_portal_v1.py <APP_DIR>")
app=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
existing=app/"lib/services/cipa_member_identity.dart"
header=app/"lib/widgets/cipa_member_access_header.dart"
assert existing.is_file() and header.is_file(), (
    "Execute primeiro patch_cipa_member_label_v1.py")
targets={
    "feature_sources/cipa_member_portal_policy_v1.dart":
        app/"lib/services/cipa_member_portal_policy.dart",
    "feature_sources/cipa_member_portal_screen_v1.dart":
        app/"lib/screens/cipa_member_portal_screen.dart",
    "feature_sources/cipa_member_portal_policy_test_v1.dart":
        app/"test/cipa_member_portal_policy_test.dart",
    "feature_sources/cipa_member_portal_screen_test_v1.dart":
        app/"test/cipa_member_portal_screen_test.dart",
}
assert not any(p.exists() for p in targets.values()), (
    "Portal já instalado ou nome em uso: não duplicar")

# Nenhuma mutação no núcleo, arquivos CIPA existentes, sync ou Central Online.
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in (app/"lib",app/"painel_web_google_apps_script")
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file()
}
for path,target in targets.items():
    source=repo/path
    if not source.is_file():raise RuntimeError("Falta "+str(source))
    target.parent.mkdir(parents=True,exist_ok=True)
    text=source.read_text(encoding="utf-8")
    if target.name=="cipa_member_portal_policy_test.dart":
        text=text.replace("import 'cipa_member_identity_v1.dart';",
            "import '../lib/services/cipa_member_identity.dart';")
        text=text.replace("import 'cipa_member_portal_policy_v1.dart';",
            "import '../lib/services/cipa_member_portal_policy.dart';")
    if target.name=="cipa_member_portal_policy.dart":
        text=text.replace("import 'cipa_member_identity.dart';",
            "import 'cipa_member_identity.dart';")
    target.write_text(text,encoding="utf-8",newline="\n")

assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest
    for p,digest in protected.items()), "Arquivo protegido mudou"
assert "if(!widget.sessionVerified || view==null)" in (
    app/"lib/screens/cipa_member_portal_screen.dart").read_text()
assert "syncFullDatabase" in (
    app/"lib/services/cipa_member_portal_policy.dart").read_text()
print("CIPA_MEMBER_PORTAL_SOURCE_READY: LOGIN_DISABLED_BY_DEFAULT")
