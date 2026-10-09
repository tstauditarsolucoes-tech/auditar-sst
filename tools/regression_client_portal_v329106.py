#!/usr/bin/env python3
"""Verificações estáticas do patch, em complemento a flutter test e node --check."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
read=lambda rel:(root/rel).read_text(encoding='utf-8')
code=read('painel_web_google_apps_script/Code.gs')
multi=read('painel_web_google_apps_script/MultiUser.gs')
portal=read('painel_web_google_apps_script/ClientPortal.gs')
html=read('painel_web_google_apps_script/ClientPortal.html')
auth=read('lib/services/auth_service.dart')
users=read('lib/screens/users_screen.dart')
assert "authorization.user.role === 'cliente'" in code
assert "String(params.cliente || '') === '1'" in code
assert "if (user.role === 'cliente')" in multi
assert 'client_permissions_json' in multi
assert 'clientPortalPermissions_(user.clientPermissions)' in multi
assert 'clientPortalData(token)' in portal
assert "user.sessionPlatform !== 'client_portal'" in portal
assert "payload.company || {}" in portal
assert 'payload.accessToken' not in portal
assert 'clientPortalSubmitEvidence' in portal
assert 'PENDENTE_VALIDACAO' in portal
assert "clientPortalReviewEvidence" in portal
assert "user.role === 'cliente'" in portal
assert 'clientPortalEvidencePhoto' in portal
assert 'clientPermissions' in auth
assert "DropdownMenuItem(value: 'cliente'" in users
assert 'selectedCompanies.length != 1' in users
assert 'clientPermissions: clientPermissions' in users
assert '<script>' in html and 'google.script.run' in html
assert "sessionStorage.getItem('auditar_client_portal_session')" in html
import re, subprocess, tempfile
scripts=re.findall(r'<script[^>]*>(.*?)</script>', html, flags=re.S)
assert len(scripts)==1
with tempfile.NamedTemporaryFile(mode='w',suffix='.js',encoding='utf-8',delete=False) as f:
    f.write(scripts[0]); script_file=f.name
try:
    subprocess.run(['node','--check',script_file],check=True)
finally:
    Path(script_file).unlink(missing_ok=True)
print('CLIENT_PORTAL_STATIC_REGRESSION_OK')
