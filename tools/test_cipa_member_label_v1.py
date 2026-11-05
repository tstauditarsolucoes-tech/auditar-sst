#!/usr/bin/env python3
"""Testa o nome com função na CIPA sem modificar dados reais ou backend."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
patch=repo/"tools/patch_cipa_member_label_v1.py"
with tempfile.TemporaryDirectory(prefix="auditar-cipa-member-display-") as work:
    app=Path(work)
    screens=app/"lib/screens"
    services=app/"lib/services"
    widgets=app/"lib/widgets"
    tests=app/"test"
    gs=app/"painel_web_google_apps_script"
    for folder in [screens,services,widgets,tests,gs]:
        folder.mkdir(parents=True,exist_ok=True)
    screen=screens/"cipa_management_screen.dart"
    screen.write_text("""import '../services/cipa_guide_rules.dart';
class CipaManagementScreen {
  Widget _membersTab() => _standardList(
        title: 'Membros da CIPA',
        addLabel: 'Adicionar membro',
        onAdd: () => _editMember(),
        items: activeMembers,
        itemBuilder: (item) => ListTile(
          leading: const CircleAvatar(child: Icon(Icons.person_outline)),
          title: Text(
            item.title,
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),
          subtitle: Text(
            'Cargo da CIPA:',
          ),
        ),
      );

  Widget _meetingsTab() => Container();
}
""",encoding="utf-8")
    (screens/"cipa_guided_home.dart").write_text(
        "part of 'cipa_management_screen.dart';",encoding="utf-8")
    protected=services/"auth_service.dart"
    protected.write_text("intacto",encoding="utf-8")
    server=gs/"MultiUser.gs"
    server.write_text("nunca modificar",encoding="utf-8")
    snapshots={p:hashlib.sha256(p.read_bytes()).hexdigest()
      for p in [protected,server,screens/"cipa_guided_home.dart"]}
    out=subprocess.run([sys.executable,str(patch),str(app)],
      capture_output=True,text=True)
    assert out.returncode==0,out.stdout+"\n"+out.stderr
    assert "CIPA_MEMBER_NAME_ROLE_DISPLAY_READY" in out.stdout
    modified=screen.read_text(encoding="utf-8")
    assert modified.count("CipaMemberIdentityLabel.displayName(")==1
    assert "item.payload['cipaRole']" in modified
    assert (services/"cipa_member_identity.dart").is_file()
    assert (widgets/"cipa_member_access_header.dart").is_file()
    assert (tests/"cipa_member_identity_test.dart").is_file()
    assert (tests/"cipa_member_access_header_test.dart").is_file()
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest
      for p,digest in snapshots.items()),"arquivo protegido modificado"
    files=[screen,services/"cipa_member_identity.dart",
      widgets/"cipa_member_access_header.dart"]
    old={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    repeat=subprocess.run([sys.executable,str(patch),str(app)],
      capture_output=True,text=True)
    assert repeat.returncode!=0,"Não sobrescrever ou duplicar instalação"
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest
      for p,digest in old.items()),"reinstalação mudou arquivo"
    print("CIPA_MEMBER_DISPLAY_PATCH_SAFE_OK")
