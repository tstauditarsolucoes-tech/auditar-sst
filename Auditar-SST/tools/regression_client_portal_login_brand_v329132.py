#!/usr/bin/env python3
"""Static test of Auditar login style and existing panel functionality."""
from pathlib import Path
from html.parser import HTMLParser
import sys

root=Path(sys.argv[1])
html=(root/'painel_web_google_apps_script/ClientPortal.html').read_text(encoding='utf-8')
for marker in (
    'auditar-login-story',
    'auditar-login-form',
    'auditar-brand-lockup',
    'AUDITAR',
    'Sua gestão de SST, em um só lugar.',
    'Acompanhe indicadores de SST.',
    'Consulte relatórios e evidências.',
    'Visualize ações e prazos.',
    '@media(max-width:760px)',
    'Acesso seguro ao painel',
    'id="loginForm"',
    'id="email"',
    'id="password"',
    'id="loginError"',
    'id="enter"',
    'id="dashboard"',
    'id="adminAccess"',
    'id="logout"',
    "google.script.run",
    "clientPortalLogin",
    "sessionStorage",
):
    if marker not in html: raise SystemExit('PORTAL_BRAND missing '+marker)
for identity in ('login','loginForm','email','password','loginError',
                 'enter','dashboard','adminAccess','logout'):
    if html.count('id="'+identity+'"') != 1:
        raise SystemExit('PORTAL_BRAND duplicate/missing id '+identity)
if html.count('<script>') != 1 or html.count('</script>') != 1:
    raise SystemExit('PORTAL_BRAND unexpected script block')
if html.count('id="clientForm"') != 1:
    raise SystemExit('PORTAL_BRAND admin access changed')

class AuditTree(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack=[]
        self.login_form=False
        self.admin_outside=False
        self.login_benefits=0
        self.errors=[]
    def handle_starttag(self,tag,attrs):
        properties=dict(attrs)
        is_login=properties.get('id')=='login'
        inside_login=any(entry[1] for entry in self.stack) or is_login
        if properties.get('id')=='loginForm':
            self.login_form=inside_login
        if properties.get('id')=='adminAccess':
            self.admin_outside=not inside_login
        if tag=='li' and inside_login: self.login_benefits+=1
        if tag not in ('meta','link','input','br','hr','img','wbr','source','area','base','embed','param'):
            self.stack.append((tag,is_login))
    def handle_endtag(self,tag):
        if tag in ('meta','link','input','br','hr','img','wbr','source','area','base','embed','param'): return
        if not self.stack:return
        # This audit concerns the document structure around the login only.
        if self.stack[-1][0]==tag:self.stack.pop()
        else:
            self.errors.append((tag,self.stack[-1][0]))
tree=AuditTree()
tree.feed(html)
if not tree.login_form or not tree.admin_outside or tree.login_benefits!=3:
    raise SystemExit('PORTAL_BRAND login/admin structure not preserved')
print('AUDITAR_PORTAL_LOGIN_BRAND_REGRESSION_OK')
