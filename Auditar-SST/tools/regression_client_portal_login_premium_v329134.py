#!/usr/bin/env python3
"""Verify new client login style while keeping admin, auth JS, and panel nodes."""
from pathlib import Path
from html.parser import HTMLParser
import sys
h=(Path(sys.argv[1])/'painel_web_google_apps_script/ClientPortal.html').read_text(encoding='utf-8')
for x in ('auditar-login-premium-v329134','auditar-login-story','auditar-mobile-brand',
          'Sua empresa. Seus indicadores. Uma gestão mais clara.',
          'Bem-vindo ao seu painel.','Acessar meu painel','inputmode="email"',
          'autocomplete="current-password"','@media(max-width:760px)',
          'Acesso individual vinculado à empresa autorizada pela Auditar.',
          'clientPortalLogin','google.script.run'):
    if x not in h:raise SystemExit('Missing professional login feature: '+x)
for item in ('login','loginForm','email','password','enter','loginError',
             'dashboard','adminAccess','logout','clientForm'):
    if h.count('id="'+item+'"')!=1:raise SystemExit('Duplicate/missing ID: '+item)
if h.count('<script>')!=1 or h.count('</script>')!=1:raise SystemExit('Script structure altered')
class Audit(HTMLParser):
    def __init__(self):
        super().__init__();self.stack=[];self.bad=[];self.form=False;self.admin=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);inside='login' in self.stack or a.get('id')=='login'
        if a.get('id')=='loginForm':self.form=inside
        if a.get('id')=='adminAccess':self.admin=not inside
        if a.get('id')=='login':self.stack.append('login')
        elif tag not in ('meta','link','input','br','hr','img','wbr','source','area','base','embed','param'):self.stack.append(tag)
    def handle_endtag(self,tag):
        if tag in ('meta','link','input','br','hr','img','wbr','source','area','base','embed','param'):return
        if not self.stack:self.bad.append('extra '+tag);return
        last=self.stack.pop()
        if last!=tag and not(last=='login' and tag=='section'):self.bad.append(last+'/'+tag)
a=Audit();a.feed(h)
if not a.form or not a.admin or a.bad or a.stack:raise SystemExit('Login/admin HTML hierarchy changed: '+str(a.bad[:6]))
print('AUDITAR_CLIENT_LOGIN_PREMIUM_REGRESSION_OK')
