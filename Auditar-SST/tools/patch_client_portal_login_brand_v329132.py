#!/usr/bin/env python3
"""Auditar identity on the existing ClientPortal login. HTML/CSS only.
Keep login IDs, server calls, authorization, GS, schema and sync byte-identical.
Run AFTER patch_client_portal_admin_v329131.py.
"""
from pathlib import Path
import hashlib
import re
import sys

root = Path(sys.argv[1])
html = root / 'painel_web_google_apps_script/ClientPortal.html'
protected = [
    'lib/database.dart',
    'lib/services/device_sync_service.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/drive_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/auth_service.dart',
    'lib/services/ai_assistant_service.dart',
    'painel_web_google_apps_script/Code.gs',
    'painel_web_google_apps_script/MultiUser.gs',
    'painel_web_google_apps_script/ClientPortal.gs',
    'painel_web_google_apps_script/ReportEmail.gs',
]
before = {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
          for name in protected}
original = html.read_text(encoding='utf-8')
if 'auditar-login-story' in original:
    raise SystemExit('Portal login branding already present; no changes made')
if original.count('<section class="panel login" id="login">') != 1:
    raise SystemExit('Login section marker missing or ambiguous')
if original.count('<form id="loginForm">') != 1:
    raise SystemExit('Login form marker missing or ambiguous')
if original.count('</style>') != 1:
    raise SystemExit('CSS insertion marker missing')
if original.count('<script>') != 1 or original.count('</script>') != 1:
    raise SystemExit('Login JS markers changed unexpectedly')

css = r'''
/* Auditar SST | login corporativo do Painel Gerencial.
   Escopo restrito ao login; as páginas internas mantêm sua identidade por empresa. */
:root{--auditar-navy:#11374b;--auditar-navy-deep:#102937;
 --auditar-teal:#117d70;--auditar-mint:#6ee0bc;--auditar-light:#e7f8f0}
body{background:linear-gradient(155deg,#eaf3f4 0%,#f4f7fb 50%,#edf5f1 100%)}
header{background:linear-gradient(110deg,var(--auditar-navy-deep),#16566b)}
#login.auditar-login{max-width:1010px;margin:clamp(24px,6vh,68px) auto 30px;
 padding:0;overflow:hidden;display:grid;grid-template-columns:minmax(0,1.03fr) minmax(0,0.97fr);
 border:1px solid #d9e7e6;border-radius:24px;
 box-shadow:0 20px 55px rgba(14,46,60,.12)}
#login .auditar-login-story{position:relative;isolation:isolate;
 background:linear-gradient(143deg,#102b3e 0%,#145263 65%,#126b65 100%);
 color:#fff;padding:clamp(26px,4vw,48px);display:flex;flex-direction:column;
 justify-content:space-between;gap:30px}
#login .auditar-login-story:before{content:"";position:absolute;z-index:-1;
 width:285px;height:285px;right:-130px;top:-105px;border:1px solid rgba(210,255,240,.22);
 border-radius:50%;box-shadow:0 0 0 48px rgba(207,255,236,.035),0 0 0 95px rgba(207,255,236,.025)}
#login .auditar-brand-lockup{display:flex;align-items:center;gap:12px;
 letter-spacing:.06em;font-size:17px;font-weight:800}
#login .auditar-brand-mark{display:grid;place-items:center;width:47px;height:47px;
 border:1px solid rgba(235,255,247,.45);border-radius:13px;
 color:#fff;background:linear-gradient(145deg,#218c7b,#0c5a58);font-size:26px;font-weight:900}
#login .auditar-brand-lockup small{display:block;font-size:10px;font-weight:650;
 text-transform:uppercase;letter-spacing:.18em;color:#b6e5d9}
#login .auditar-story-eyebrow{margin:0 0 11px;font-size:11px;
 letter-spacing:.17em;text-transform:uppercase;color:#93ead1;font-weight:800}
#login .auditar-story-title{font-size:clamp(26px,3vw,38px);line-height:1.13;
 font-weight:850;letter-spacing:-.035em;margin:0 0 13px;color:#fff}
#login .auditar-story-intro{color:#d5e9e9;font-size:14px;line-height:1.65;margin:0}
#login .auditar-utility{list-style:none;padding:0;margin:27px 0 0;display:grid;gap:12px}
#login .auditar-utility li{display:flex;align-items:center;gap:12px;
 font-size:13px;line-height:1.4;color:#effff9}
#login .auditar-utility li:before{content:"✓";display:grid;place-items:center;
 width:24px;height:24px;min-width:24px;border-radius:7px;
 background:rgba(110,224,188,.14);color:#98f3d4;font-weight:900}
#login .auditar-story-footer{font-size:11px;line-height:1.5;
 color:#b9d8d9;border-top:1px solid rgba(235,255,248,.18);padding-top:16px}
#login .auditar-login-form{background:#fff;padding:clamp(24px,4vw,48px);
 display:flex;flex-direction:column;justify-content:center;min-width:0}
#login .auditar-form-eyebrow{font-size:11px;color:#16816e;font-weight:850;
 letter-spacing:.12em;text-transform:uppercase;margin:0 0 10px}
#login .auditar-login-form h1{font-size:clamp(24px,2.5vw,30px);
 color:#12384a;letter-spacing:-.03em}
#login .auditar-login-form>.muted{line-height:1.5;font-size:13px}
#login .auditar-login-form form{margin-top:12px}
#login .auditar-login-form input{min-height:46px;background:#fbfdfc;
 border:1px solid #bfd4d2}
#login .auditar-login-form input:focus-visible{outline:2px solid #2da18c;
 outline-offset:2px;border-color:#2da18c}
#login .auditar-login-form #enter{display:block;width:100%;min-height:47px;
 margin-top:10px;background:linear-gradient(110deg,#0f7368,#168d76);
 box-shadow:0 5px 14px rgba(15,115,104,.19)}
#login .auditar-login-form #enter:focus-visible{outline:3px solid #59bca9;
 outline-offset:3px}
#login .auditar-login-footnote{border-top:1px solid #e6efec;margin:22px 0 0;
 padding-top:15px;font-size:11px;line-height:1.6;color:#657d84}
#login #loginError:not(:empty){background:#fff2f1;border:1px solid #f0d1cd;
 border-radius:9px;padding:9px 11px}
@media(max-width:760px){
 #login.auditar-login{max-width:540px;grid-template-columns:minmax(0,1fr);
 margin:22px auto}
 #login .auditar-login-story{gap:17px;padding:24px}
 #login .auditar-utility{grid-template-columns:1fr;gap:9px;margin-top:17px}
 #login .auditar-story-title{font-size:26px}
 #login .auditar-login-form{padding:25px}
}
@media(max-width:370px){
 #login .auditar-login-story,#login .auditar-login-form{padding:19px}
 #login .auditar-brand-lockup{font-size:16px}
}
@media(prefers-reduced-motion:reduce){#login *{scroll-behavior:auto}}
'''
story='''<aside class="auditar-login-story" aria-label="Apresentação do Painel Auditar">
  <div class="auditar-brand-lockup">
   <div class="auditar-brand-mark" aria-hidden="true">A</div>
   <div>AUDITAR <small>Soluções em SST</small></div>
  </div>
  <div>
   <p class="auditar-story-eyebrow">Painel Gerencial • Segurança e Saúde do Trabalho</p>
   <h2 class="auditar-story-title">Sua gestão de SST, em um só lugar.</h2>
   <p class="auditar-story-intro">Informações organizadas para acompanhar o que importa, com acesso por empresa.</p>
   <ul class="auditar-utility">
    <li>Acompanhe indicadores de SST.</li>
    <li>Consulte relatórios e evidências.</li>
    <li>Visualize ações e prazos.</li>
   </ul>
  </div>
  <div class="auditar-story-footer">Auditar SST • Organização, acompanhamento e rastreabilidade.</div>
 </aside>
 <div class="auditar-login-form">
  <p class="auditar-form-eyebrow">Acesso seguro ao painel</p>'''
opening='<section class="panel login" id="login">'
start=original.index(opening)
form=original.index('<form id="loginForm">',start)
end=original.index('</section>',form)
login_body=original[form:end]
if not re.search(r'</form>\s*$',login_body):
    raise SystemExit('Login section structure changed; refusing to replace')
updated=original.replace('</style>',css+'\n</style>',1)
updated=updated.replace(opening, '<section class="panel login auditar-login" id="login">\n '+story,1)
close=''' </form>
 </div>
</section>'''
# Match the actual original closing form and the first following login </section>.
m=re.search(r'</form>\s*</section>',updated[updated.index('<form id="loginForm">'):])
if m is None:
    raise SystemExit('Login closing anchors missing')
absolute=updated.index('<form id="loginForm">')+m.start()
updated=updated[:absolute]+re.sub(r'</form>\s*</section>',close,updated[absolute:],count=1)
if '<section id="dashboard" class="hidden">' not in updated:
    raise SystemExit('Dashboard root unexpectedly changed')
for marker in ('id="email"','id="password"','id="loginError"','id="loginForm"',
               'id="enter"','id="dashboard"','id="logout"','id="adminAccess"'):
    if updated.count(marker)!=1: raise SystemExit('Unexpected ID count: '+marker)
old_js=original.split('<script>',1)[1].split('</script>',1)[0]
new_js=updated.split('<script>',1)[1].split('</script>',1)[0]
if old_js!=new_js: raise SystemExit('Authentication JS changed unexpectedly')
html.write_text(updated,encoding='utf-8',newline='\n')
changed=[name for name,digest in before.items()
         if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest]
if changed: raise SystemExit('Protected core/GS changed: '+repr(changed))
print('AUDITAR_PORTAL_LOGIN_BRAND_ISOLATED_OK')
print('PORTAL_AUTH_SYNC_GS_DATABASE_BYTE_IDENTICAL_OK')
