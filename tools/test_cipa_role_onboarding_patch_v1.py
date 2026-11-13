#!/usr/bin/env python3
"""Teste offline do patch de cadastro sem alterar fontes existentes."""
from pathlib import Path
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
original=repo/"build_sources/v3.29.76-cipa/cipa_management_screen.dart"
script=repo/"tools/patch_cipa_role_onboarding_v1.py"
roles=repo/"feature_sources/cipa_member_role_meetings_v1.dart"
with tempfile.TemporaryDirectory(prefix="cipa-role-patch-") as temp:
    app=Path(temp)
    screen=app/"lib/screens/cipa_management_screen.dart"
    role=app/"lib/services/cipa_member_role_meetings.dart"
    screen.parent.mkdir(parents=True)
    role.parent.mkdir(parents=True)
    source=original.read_text(encoding="utf-8")
    screen.write_text(source,encoding="utf-8")
    role.write_text(roles.read_text(encoding="utf-8"),encoding="utf-8")
    result=subprocess.run([sys.executable,str(script),str(app)],
       capture_output=True,text=True,check=True)
    assert "CIPA_ROLE_ONBOARDING_GUIDED" in result.stdout
    modified=screen.read_text(encoding="utf-8")
    assert "Escolha a função na CIPA" in modified
    assert "CipaRoleGuide.summary(cipaRole)" in modified
    assert "CipaRoleGuide.consistent(cipaRole, representation)" in modified
    assert "cipaRole: cipaRole" in modified
    assert modified.count("Future<void> _editMember") == 1
    assert "CipaRoleGuide" not in source
    assert role.read_text(encoding="utf-8")==roles.read_text(encoding="utf-8")
    second=subprocess.run([sys.executable,str(script),str(app)],
       capture_output=True,text=True)
    assert second.returncode != 0, "Patch duplicado proibido"
print("CIPA_ROLE_ONBOARDING_PATCH_TEST_OK")
