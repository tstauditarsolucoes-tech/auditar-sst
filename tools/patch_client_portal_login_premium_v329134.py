#!/usr/bin/env python3
"""Auditar SST: visual-only refinement of the existing client login.

Run after v329132 branded login, before packaging. No JS/GS/auth/sync/DB edits.
"""
from pathlib import Path
import hashlib
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
    'painel_web_google_apps_script/Index.html',
]
before = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
          for name in protected}
s = html.read_text(encoding='utf-8')
if 'auditar-login-premium-v329134' in s:
    raise SystemExit('Login premium already installed. No changes made.')
if 'auditar-login-story' not in s or s.count('</style>') != 1:
    raise SystemExit('Existing branded login not found.')
if s.count('<script>') != 1 or s.count('</script>') != 1:
    raise SystemExit('Unexpected script structure.')
old_js = s.split('<script>', 1)[1].split('</script>', 1)[0]

def once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(label + ': expected once, found ' + str(count))
    s = s.replace(old, new, 1)

once('<div>AUDITAR <small>Soluções em SST</small></div>',
     '<div class="auditar-brand-name">AUDITAR <small>Soluções em SST</small></div>',
     'brand lockup')
once('<p class="auditar-story-eyebrow">Painel Gerencial • Segurança e Saúde do Trabalho</p>',
     '<p class="auditar-story-eyebrow">AUDITAR SST <span aria-hidden="true">/</span> PAINEL DO CLIENTE</p>',
     'story eyebrow')
once('Sua gestão de SST, em um só lugar.',
     'Sua empresa. Seus indicadores. Uma gestão mais clara.', 'story title')
once('Informações organizadas para acompanhar o que importa, com acesso por empresa.',
     'Acompanhe as informações de Segurança e Saúde do Trabalho disponibilizadas para sua empresa em um ambiente organizado.',
     'story description')
once('Acompanhe indicadores de SST.', 'Acompanhe indicadores e resultados.', 'feature 1')
once('Consulte relatórios e evidências.', 'Consulte relatórios e registros autorizados.', 'feature 2')
once('Visualize ações e prazos.', 'Acompanhe ações corretivas e prazos.', 'feature 3')
once('Auditar SST • Organização, acompanhamento e rastreabilidade.',
     'Auditar Soluções <span aria-hidden="true">•</span> Segurança e Saúde do Trabalho.',
     'story footer')
once('<p class="auditar-form-eyebrow">Acesso seguro ao painel</p>',
     '''<div class="auditar-mobile-brand" aria-label="Auditar Soluções">
    <span class="auditar-brand-mark" aria-hidden="true">A</span>
    <span class="auditar-brand-name">AUDITAR <small>Soluções em SST</small></span>
   </div>
   <p class="auditar-form-eyebrow">ÁREA DO CLIENTE</p>''',
     'responsive identity')
once('<h1>Acesso individual</h1>', '<h1>Bem-vindo ao seu painel.</h1>', 'form title')
once('Utilize o e-mail e a senha fornecidos pela Auditar. Você verá somente as informações liberadas para sua empresa.',
     'Acesse com suas credenciais para consultar as informações autorizadas da sua empresa.',
     'form description')
once('<label for="email">E-mail</label><input id="email" type="email" required autocomplete="username">',
     '<label for="email">E-mail de acesso</label><input id="email" type="email" required autocomplete="username" inputmode="email" placeholder="seuemail@empresa.com.br">',
     'email appearance')
once('<label for="password">Senha</label><input id="password" type="password" required autocomplete="current-password">',
     '<label for="password">Senha</label><input id="password" type="password" required autocomplete="current-password" placeholder="Digite sua senha">',
     'password appearance')
once('<button id="enter" type="submit">Entrar</button>',
     '<button id="enter" type="submit">Acessar meu painel <span aria-hidden="true">→</span></button>',
     'CTA text')
once(' </form>\n </div>\n</section>',
     ''' </form>
   <div class="auditar-login-footnote">Acesso individual vinculado à empresa autorizada pela Auditar.</div>
 </div>
</section>''',
     'privacy footnote')

css = r'''
/* auditar-login-premium-v329134: presentation only, scoped to visible login. */
body:has(#login:not(.hidden)) {
 min-height:100vh;
 background:radial-gradient(circle at 7% 12%,#e0f3ec 0,transparent 35%),
            radial-gradient(circle at 95% 94%,#e5f0f5 0,transparent 38%),#f3f7f8;
}
body:has(#login:not(.hidden)) > header {display:none}
body:has(#login:not(.hidden)) .wrap{
 max-width:1180px;padding:clamp(18px,4vh,42px) clamp(14px,3vw,32px) 36px;
 min-height:100vh;display:flex;align-items:center;justify-content:center;
}
#login.auditar-login{
 width:100%;max-width:1080px;min-height:575px;margin:0;
 grid-template-columns:minmax(0,1.06fr) minmax(0,.94fr);
 border:1px solid #d7e5e3;border-radius:26px;
 box-shadow:0 28px 75px rgba(12,46,56,.14),0 4px 12px rgba(12,46,56,.04);
}
#login .auditar-login-story{
 padding:clamp(30px,4.5vw,58px);
 background:linear-gradient(145deg,#0e3041 0%,#124c5b 56%,#126f61 100%);
 gap:40px;
}
#login .auditar-login-story:before{
 width:340px;height:340px;right:-148px;top:-92px;
 box-shadow:0 0 0 55px rgba(219,255,243,.035),0 0 0 120px rgba(219,255,243,.02);
}
#login .auditar-login-story:after{
 content:"";position:absolute;z-index:-1;width:240px;height:240px;
 border:1px solid rgba(235,255,249,.12);border-radius:50%;bottom:-160px;left:-100px;
}
#login .auditar-brand-mark{
 width:44px;height:44px;border-radius:12px;flex:0 0 44px;
 color:#f4fffa;box-shadow:0 6px 16px rgba(0,0,0,.12);
}
#login .auditar-brand-lockup{gap:14px;font-size:20px;letter-spacing:.075em}
#login .auditar-brand-name{font-size:20px;font-weight:850;line-height:1.05;letter-spacing:.075em}
#login .auditar-brand-name small{margin-top:5px;letter-spacing:.14em;font-size:9px}
#login .auditar-story-eyebrow{letter-spacing:.13em;color:#a3f1d6}
#login .auditar-story-eyebrow span{padding:0 5px;color:#78b7aa}
#login .auditar-story-title{
 max-width:460px;font-size:clamp(30px,3.4vw,43px);line-height:1.13;
 letter-spacing:-.045em;margin-bottom:20px;
}
#login .auditar-story-intro{max-width:420px;color:#dcefee;font-size:14px}
#login .auditar-utility{margin-top:30px;gap:15px}
#login .auditar-utility li{font-size:13px}
#login .auditar-story-footer{color:#c4dcdb;font-size:11px}
#login .auditar-login-form{padding:clamp(30px,4.3vw,58px);background:#fff}
#login .auditar-mobile-brand{display:none}
#login .auditar-form-eyebrow{font-size:11px;color:#16836d;letter-spacing:.15em}
#login .auditar-login-form h1{
 max-width:370px;margin:0 0 14px;font-size:clamp(27px,2.8vw,35px);
 line-height:1.16;color:#123547;letter-spacing:-.04em;
}
#login .auditar-login-form>.muted{max-width:370px;margin:0;color:#526b76;font-size:13px;line-height:1.65}
#login .auditar-login-form form{margin-top:20px}
#login .auditar-login-form label{margin:17px 0 7px;color:#284555;font-size:12px}
#login .auditar-login-form input{
 min-height:49px;background:#fbfdfd;border:1px solid #c9d9dc;
 border-radius:11px;font-size:14px;transition:border-color .15s,box-shadow .15s;
}
#login .auditar-login-form input::placeholder{color:#8ca0a8}
#login .auditar-login-form input:focus{
 outline:none;border-color:#138671;box-shadow:0 0 0 3px rgba(19,134,113,.12);
}
#login .auditar-login-form #enter{
 margin-top:17px;min-height:50px;display:flex;justify-content:center;align-items:center;gap:12px;
 border-radius:11px;background:linear-gradient(100deg,#0b6c63,#138e74);
 font-size:14px;letter-spacing:.005em;box-shadow:0 7px 18px rgba(16,109,97,.19);
}
#login .auditar-login-form #enter span{font-size:20px;font-weight:500;line-height:1}
#login .auditar-login-form #enter:hover:not(:disabled){filter:brightness(1.08)}
#login .auditar-login-form #enter:focus-visible{outline:3px solid #83d6c2;outline-offset:3px}
#login .auditar-login-footnote{margin-top:25px;padding-top:17px;color:#69818a}
#login #loginError:not(:empty){font-size:12px;line-height:1.5}
@media(max-width:760px){
 body:has(#login:not(.hidden)) .wrap{padding:14px;align-items:center}
 #login.auditar-login{max-width:510px;min-height:0;grid-template-columns:minmax(0,1fr);border-radius:19px}
 #login .auditar-login-story{display:none}
 #login .auditar-login-form{padding:clamp(26px,7vw,39px)}
 #login .auditar-mobile-brand{display:flex;align-items:center;gap:12px;margin-bottom:36px;color:#123c4c}
 #login .auditar-mobile-brand .auditar-brand-mark{display:grid;place-items:center;
   background:linear-gradient(145deg,#168c78,#0d5d63);border-color:#b7dad0;color:#fff}
 #login .auditar-mobile-brand small{color:#28816d}
 #login .auditar-login-form h1{font-size:29px}
}
@media(max-width:370px){
 #login .auditar-login-form{padding:23px 19px}
 #login .auditar-mobile-brand{margin-bottom:26px}
 #login .auditar-login-form h1{font-size:27px}
}
@media(prefers-reduced-motion:reduce){
 #login .auditar-login-form input{transition:none}
}
'''
once('</style>', css + '\n</style>', 'CSS insertion')

new_js = s.split('<script>', 1)[1].split('</script>', 1)[0]
if new_js != old_js:
    raise SystemExit('Login behavior/JS changed; abort.')
for item in ('login','loginForm','email','password','enter','loginError',
             'dashboard','adminAccess','logout','clientForm'):
    if s.count('id="' + item + '"') != 1:
        raise SystemExit('Missing/duplicated element ID: ' + item)
html.write_text(s, encoding='utf-8', newline='\n')
changed = [name for name, digest in before.items()
           if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest]
if changed:
    raise SystemExit('Protected file changed: ' + ', '.join(changed))
print('AUDITAR_CLIENT_LOGIN_PREMIUM_VISUAL_ONLY_OK')
print('AUDITAR_GS_AUTH_SYNC_DB_MEDIA_UNCHANGED_OK')
