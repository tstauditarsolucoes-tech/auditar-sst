#!/usr/bin/env python3
"""Teste de instalação administrativa CIPA preservando núcleo e servidor."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
patch=repo/"tools/patch_cipa_member_admin_ui_v1.py"
with tempfile.TemporaryDirectory(prefix="auditar-cipa-admin-ui-") as tmp:
    app=Path(tmp)
    screens=app/"lib/screens";services=app/"lib/services"
    gs=app/"painel_web_google_apps_script"
    for p in [screens,services,gs]:p.mkdir(parents=True,exist_ok=True)
    cipa=screens/"cipa_management_screen.dart"
    cipa.write_text("""import '../services/cipa_management_service.dart';
import 'cipa_screen.dart';
class Test {
  Widget build() => Scaffold(appBar:AppBar(
          title: const Text('CIPA'),
          actions: [
            IconButton(icon:const Icon(Icons.refresh), onPressed:()=>{}),
          ],
  ));
}
""",encoding="utf-8")
    (services/"cipa_member_identity.dart").write_text(
      "identity unchanged",encoding="utf-8")
    auth=services/"auth_service.dart"
    auth.write_text("auth unchanged",encoding="utf-8")
    backend=gs/"MultiUser.gs";backend.write_text("GS unchanged",encoding="utf-8")
    snapshots={p:p.read_bytes() for p in [
      services/"cipa_member_identity.dart",auth,backend]}
    first=subprocess.run([sys.executable,str(patch),str(app)],
      capture_output=True,text=True)
    assert first.returncode==0,(first.stdout,first.stderr)
    content=cipa.read_text()
    assert content.count("CipaMemberAdminScreen(")==1
    assert "if (AuthService.isAdmin)" in content
    assert (screens/"cipa_member_admin_screen.dart").exists()
    assert all(p.read_bytes()==value for p,value in snapshots.items())
    modified={p:hashlib.sha256(p.read_bytes()).hexdigest()
      for p in [cipa,screens/"cipa_member_admin_screen.dart"]}
    second=subprocess.run([sys.executable,str(patch),str(app)],
      capture_output=True,text=True)
    assert second.returncode!=0
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest
      for p,digest in modified.items())
    print("CIPA_MEMBER_ADMIN_UI_PATCH_SAFE_OK")
