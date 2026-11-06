#!/usr/bin/env python3
"""Aplicar patch da área admin sobre a fonte CIPA real preservada no repo."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import shutil

repo=Path(__file__).resolve().parents[1]
screen=repo/"feature_sources/cipa_management_screen_v329168.dart"
script=repo/"tools/patch_cipa_member_admin_ui_v1.py"
assert screen.exists()
with tempfile.TemporaryDirectory(prefix="cipa-admin-real-screen-") as tmp:
    app=Path(tmp)
    target=app/"lib/screens/cipa_management_screen.dart"
    target.parent.mkdir(parents=True)
    shutil.copyfile(screen,target)
    service=app/"lib/services/cipa_member_identity.dart"
    service.parent.mkdir(parents=True)
    service.write_text("class CipaMemberIdentityLabel {}")
    auth=app/"lib/services/auth_service.dart"
    auth.write_text("AUTH_SERVICE_PROTECTED")
    gs=app/"painel_web_google_apps_script/MultiUser.gs"
    gs.parent.mkdir(parents=True)
    gs.write_text("GS_PROTECTED")
    prev={p:hashlib.sha256(p.read_bytes()).hexdigest()
      for p in [auth,gs,service]}
    result=subprocess.run([sys.executable,str(script),str(app)],
      capture_output=True,text=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    installed=target.read_text()
    assert "CipaAdminDocumentOption" in installed
    assert installed.count("CipaMemberAdminScreen(")==1
    assert installed.count("import 'cipa_member_admin_screen.dart';")==1
    assert installed.index("CipaMemberAdminScreen(")>installed.index("Widget build")
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==v
      for p,v in prev.items())
    print("CIPA_ADMIN_PATCH_REAL_SCREEN_SOURCE_OK")
