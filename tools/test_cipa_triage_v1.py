#!/usr/bin/env python3
"""Regressão do patch de triagem sobre fonte CIPA fictícia; sem dados reais."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
script=repo/"tools/patch_cipa_triage_v1.py"
with tempfile.TemporaryDirectory(prefix="auditar-cipa-triagem-") as tmp:
    root=Path(tmp)
    screens=root/"lib/screens"
    services=root/"lib/services"
    tests=root/"test"
    gs=root/"painel_web_google_apps_script"
    for folder in (screens,services,tests,gs):
        folder.mkdir(parents=True,exist_ok=True)
    base=screens/"cipa_management_screen.dart"
    base.write_text("""import '../services/cipa_participation_rules.dart';
part 'cipa_participation_screen.dart';
class CipaManagementScreen {}
""",encoding="utf-8")
    participation=screens/"cipa_participation_screen.dart"
    participation.write_bytes(
        (repo/"feature_sources/cipa_participation_screen_v1.dart").read_bytes())
    (services/"cipa_participation_rules.dart").write_bytes(
        (repo/"feature_sources/cipa_participation_rules_v1.dart").read_bytes())
    core=services/"auth_service.dart"
    core.write_text("NÃO ALTERAR AUTENTICAÇÃO",encoding="utf-8")
    gsfile=gs/"Code.gs"
    gsfile.write_text("NÃO ALTERAR SERVER",encoding="utf-8")
    old={p:p.read_bytes() for p in [core,gsfile,services/"cipa_participation_rules.dart"]}
    result=subprocess.run([sys.executable,str(script),str(root)],
        capture_output=True,text=True)
    if result.returncode:
        raise AssertionError(result.stdout+"\n"+result.stderr)
    assert "CIPA_TRIAGE_ANDROID_READY" in result.stdout
    assert all(p.read_bytes()==data for p,data in old.items())
    assert "CipaFollowupQueue(" in (
        screens/"cipa_triage_extension.dart").read_text()
    assert "observation_review" in participation.read_text()
    assert "progress_review" in participation.read_text()
    assert "part 'cipa_triage_extension.dart';" in base.read_text()
    assert (tests/"cipa_followup_queue_test.dart").is_file()
    before={p:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [base,participation,screens/"cipa_triage_extension.dart",
                      services/"cipa_followup_queue.dart"]}
    repeated=subprocess.run([sys.executable,str(script),str(root)],
        capture_output=True,text=True)
    assert repeated.returncode!=0,"Não permitir instalação duplicada"
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hash_value
        for p,hash_value in before.items())
    print("CIPA_TRIAGE_PATCH_SAFE_OK")
