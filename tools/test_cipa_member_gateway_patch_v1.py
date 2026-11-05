#!/usr/bin/env python3
"""Verificar montagem opt-in do backend numa Central FICTÍCIA."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
patch=repo/"tools/patch_cipa_member_gateway_experimental_v1.py"
with tempfile.TemporaryDirectory(prefix="cipa-member-gs-") as temp:
    root=Path(temp)
    backend=root/"painel_web_google_apps_script"
    services=root/"lib/services"
    backend.mkdir(parents=True)
    services.mkdir(parents=True)
    code=backend/"Code.gs"
    code.write_text("""function doPost(e) {
  try {
    const request = JSON.parse((e.postData && e.postData.contents) || '{}');
    const expectedKey = PropertiesService.getScriptProperties().getProperty('AUDITAR_SYNC_KEY');
    if (request.action === 'device_sync_pull')
      return jsonResponse_(pullDeviceChanges_(request));
  } catch (err) { return jsonResponse_({ok:false}); }
}
""",encoding="utf-8")
    multi=backend/"MultiUser.gs"
    multi.write_text("USER AUTH ORIGINAL",encoding="utf-8")
    core=services/"auth_service.dart"
    core.write_text("AUTH ORIGINAL",encoding="utf-8")
    before={p:p.read_bytes() for p in [multi,core]}
    fail=subprocess.run([sys.executable,str(patch),str(root)],
      capture_output=True,text=True)
    assert fail.returncode!=0,"Exigir parâmetro --homologacao"
    result=subprocess.run([sys.executable,str(patch),str(root),
        "--homologacao"],capture_output=True,text=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert "DEFAULT_OFF" in result.stdout
    content=code.read_text()
    assert content.count("cipaMemV1Route_(request)")==1
    assert (content.index("cipaMemV1Route_(request)") <
      content.index("const expectedKey"))
    assert "device_sync_pull" in content
    assert "CIPA_MEMBER_V1_ENABLED" in (
      backend/"CipaMemberGatewayV1.gs").read_text()
    assert all(p.read_bytes()==b for p,b in before.items())
    tracked={
      p:hashlib.sha256(p.read_bytes()).hexdigest()
      for p in [code,backend/"CipaMemberGatewayV1.gs",
        backend/"CipaMemberServerPolicy.gs"]
    }
    repeated=subprocess.run([sys.executable,str(patch),str(root),
       "--homologacao"],capture_output=True,text=True)
    assert repeated.returncode!=0
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hash_value
       for p,hash_value in tracked.items())
    print("CIPA_MEMBER_GS_EXPERIMENTAL_PATCH_SAFE_OK")
