#!/usr/bin/env python3
"""Regressão do instalador do portal CIPA sem tocar nos dados reais."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
patch=repo/"tools/patch_cipa_member_portal_v1.py"
with tempfile.TemporaryDirectory(prefix="auditar-member-portal-") as tmp:
    app=Path(tmp)
    services=app/"lib/services"
    widgets=app/"lib/widgets"
    screens=app/"lib/screens"
    script=app/"painel_web_google_apps_script"
    for d in [services,widgets,screens,script]:
        d.mkdir(parents=True,exist_ok=True)
    original={
        services/"auth_service.dart":"core auth not changed",
        services/"device_sync_service.dart":"sync not changed",
        services/"cipa_member_identity.dart":"identity not changed",
        widgets/"cipa_member_access_header.dart":"header not changed",
        script/"Code.gs":"server not changed",
        script/"MultiUser.gs":"users not changed",
    }
    for path,text in original.items():path.write_text(text,encoding="utf-8")
    out=subprocess.run([sys.executable,str(patch),str(app)],
        capture_output=True,text=True)
    assert out.returncode==0,(out.stdout,out.stderr)
    assert "LOGIN_DISABLED_BY_DEFAULT" in out.stdout
    assert all(path.read_text(encoding="utf-8")==content
        for path,content in original.items())
    screen=(screens/"cipa_member_portal_screen.dart").read_text(encoding="utf-8")
    assert "if(!widget.sessionVerified || view==null)" in screen
    assert (app/"test/cipa_member_portal_policy_test.dart").is_file()
    assert (app/"test/cipa_member_portal_screen_test.dart").is_file()
    observed={
      p:hashlib.sha256(p.read_bytes()).hexdigest()
      for p in (app/"lib").rglob("*.dart")
    }
    again=subprocess.run([sys.executable,str(patch),str(app)],
        capture_output=True,text=True)
    assert again.returncode!=0,"Repetição não pode substituir arquivos"
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest
        for p,digest in observed.items())
    print("CIPA_MEMBER_PORTAL_SAFE_MOUNT_OK")
