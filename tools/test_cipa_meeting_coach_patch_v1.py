#!/usr/bin/env python3
"""Validação isolada de instalação da reunião assistida na CIPA existente."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
script=repo/"tools/patch_cipa_meeting_coach_v1.py"
with tempfile.TemporaryDirectory(prefix="cipa-meeting-coach-") as tmp:
    root=Path(tmp)
    screens=root/"lib/screens"
    services=root/"lib/services"
    tests=root/"test"
    gs=root/"painel_web_google_apps_script"
    for folder in (screens,services,tests,gs):
        folder.mkdir(parents=True,exist_ok=True)
    screen=screens/"cipa_management_screen.dart"
    screen.write_text("""import '../services/cipa_guide_rules.dart';
part 'cipa_guided_home.dart';
class _CipaManagementScreenState {
  Widget _panelTab() {
    return ListView(children: [
          _cipaGuidedHome(),
          const SizedBox(height: 10),
          LayoutBuilder(builder: (context, constraints) => Container()),
    ]);
  }
}
""",encoding="utf-8")
    guided=screens/"cipa_guided_home.dart"
    guided.write_text("part of 'cipa_management_screen.dart';\n")
    (services/"cipa_guide_rules.dart").write_text("class CipaGuideRules {}\n")
    protected=[
      guided,services/"cipa_guide_rules.dart",
      services/"auth_service.dart",gs/"Code.gs",gs/"MultiUser.gs"
    ]
    for p in protected:
        if not p.is_file():p.write_text("ARQUIVO INALTERADO\n")
    initial={p:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in protected}
    out=subprocess.run([sys.executable,str(script),str(root)],
        capture_output=True,text=True)
    assert out.returncode==0,(out.stdout,out.stderr)
    assert "CIPA_MEETING_COACH_INSTALLED" in out.stdout
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==value
        for p,value in initial.items())
    final=screen.read_text()
    assert final.count("_cipaMeetingCoachCard(),")==1
    assert final.count("part 'cipa_meeting_coach_home.dart';")==1
    assert final.count("import '../services/cipa_meeting_coach_rules.dart';")==1
    assert (services/"cipa_meeting_coach_rules.dart").is_file()
    assert (screens/"cipa_meeting_coach_home.dart").is_file()
    assert (tests/"cipa_meeting_coach_rules_test.dart").is_file()
    hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [
      screen,services/"cipa_meeting_coach_rules.dart",
      screens/"cipa_meeting_coach_home.dart"]}
    again=subprocess.run([sys.executable,str(script),str(root)],
        capture_output=True,text=True)
    assert again.returncode!=0
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==v
        for p,v in hashes.items())
    print("CIPA_MEETING_COACH_PATCH_SAFE_NO_CORE_CHANGES")
