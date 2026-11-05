#!/usr/bin/env python3
"""Teste offline: instala somente a interface de CIPA no painel de exemplo."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
script=repo/"tools/patch_cipa_guided_home_v1.py"
with tempfile.TemporaryDirectory(prefix="auditar-cipa-guided-") as tmp:
    app=Path(tmp)
    screens=app/"lib/screens"
    services=app/"lib/services"
    tests=app/"test"
    gs=app/"painel_web_google_apps_script"
    for folder in (screens,services,tests,gs):
        folder.mkdir(parents=True,exist_ok=True)
    base=screens/"cipa_management_screen.dart"
    base.write_text("""import '../services/cipa_followup_queue.dart';
part 'cipa_triage_extension.dart';
class _CipaManagementScreenState {
  Widget _panelTab() {
    return ListView(
      children: [
          const SizedBox(height: 10),
          LayoutBuilder(builder: (context, constraints) => Container()),
      ],
    );
  }
  Widget _mandateTab() => Container();
}
""",encoding="utf-8")
    (screens/"cipa_triage_extension.dart").write_text(
        "part of 'cipa_management_screen.dart';\n",encoding="utf-8")
    (services/"cipa_followup_queue.dart").write_text(
        "class CipaFollowupQueue {}\n",encoding="utf-8")
    auth=services/"auth_service.dart"
    auth.write_text("autenticacao intacta",encoding="utf-8")
    backend=gs/"Code.gs"
    backend.write_text("servidor intacto",encoding="utf-8")
    before={p:p.read_bytes() for p in [auth,backend,
        services/"cipa_followup_queue.dart",
        screens/"cipa_triage_extension.dart"]}
    p=subprocess.run([sys.executable,str(script),str(app)],
        capture_output=True,text=True)
    assert p.returncode==0,(p.stdout,p.stderr)
    assert "CIPA_GUIDED_HOME_READY" in p.stdout
    assert all(p.read_bytes()==s for p,s in before.items())
    code=base.read_text(encoding="utf-8")
    assert "part 'cipa_guided_home.dart';" in code
    assert code.count("_cipaGuidedHome(),")==1
    assert code.index("_cipaGuidedHome(),")<code.index("LayoutBuilder(")
    assert (screens/"cipa_guided_home.dart").is_file()
    assert (services/"cipa_guide_rules.dart").is_file()
    assert (tests/"cipa_guide_rules_test.dart").is_file()
    snapshots={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [
        base,screens/"cipa_guided_home.dart",
        services/"cipa_guide_rules.dart",
        tests/"cipa_guide_rules_test.dart"]}
    repeat=subprocess.run([sys.executable,str(script),str(app)],
        capture_output=True,text=True)
    assert repeat.returncode!=0,"Reinstalação não deve sobrescrever dados"
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest
        for p,digest in snapshots.items())
    print("CIPA_GUIDED_HOME_PATCH_SAFE_OK")
