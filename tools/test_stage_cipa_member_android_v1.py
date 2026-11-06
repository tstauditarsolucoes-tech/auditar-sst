#!/usr/bin/env python3
"""Prova que o APK de membro não herda o núcleo do Auditar SST."""
from pathlib import Path
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
script=repo/"tools/stage_cipa_member_android_v1.py"
with tempfile.TemporaryDirectory(prefix="cipa-member-android-") as tmp:
    app=Path(tmp)
    manifest=app/"android/app/src/main/AndroidManifest.xml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
      '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
      '<application android:label="auditar_cipa_membro"></application>'
      '</manifest>',encoding="utf-8")
    (app/"pubspec.yaml").write_text(
      "name: auditar_cipa_membro\n"
      "dependencies:\n  flutter:\n    sdk: flutter\n",encoding="utf-8")
    result=subprocess.run([sys.executable,str(script),str(app)],
      text=True,capture_output=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert "CIPA_MEMBER_ANDROID_SEPARATE_APP_READY_NO_MASTER_KEY" in result.stdout
    all_code="\n".join(p.read_text(encoding="utf-8")
      for p in (app/"lib").rglob("*.dart"))
    assert "WebServiceConfig" not in all_code
    assert "AuthService.login(" not in all_code
    assert "auth_service.dart" not in all_code
    assert "String.fromEnvironment('AUDITAR_SYNC_KEY'" not in all_code
    assert "String.fromEnvironment(\n    'AUDITAR_MEMBER_ENDPOINT'" in all_code
    assert "android.permission.INTERNET" in manifest.read_text()
    assert "Minha CIPA - Auditar" in manifest.read_text()
    assert "package:auditar_cipa_membro" in (
      app/"test/cipa_member_portal_screen_test.dart").read_text()
    assert "Recusa itens de empresa" in (
      app/"test/cipa_member_api_test.dart").read_text()
    assert "http: ^1.3.0" in (app/"pubspec.yaml").read_text()
    again=subprocess.run([sys.executable,str(script),str(app)],
      capture_output=True,text=True)
    assert again.returncode!=0,"Montagem duplicada bloqueada"
    print("CIPA_SEPARATE_ANDROID_NO_TECH_CORE_OK")
