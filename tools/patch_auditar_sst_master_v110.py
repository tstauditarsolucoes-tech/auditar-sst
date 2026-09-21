#!/usr/bin/env python3
from pathlib import Path
import re, sys

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('auditar-sst-master')
app=root/'app.js'
html=root/'index.html'
pkg=Path('auditar-sst-master-windows/package.json')

c=app.read_text(encoding='utf-8')

old="""  const cleanUsername=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9._-]+/g,'').replace(/^[._-]+|[._-]+$/g,'').slice(0,40);
"""
new="""  const cleanUsername=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9._-]+/g,'').replace(/^[._-]+|[._-]+$/g,'').slice(0,40);
  const cleanLogin=v=>String(v||'').trim().toLowerCase();
  const loginEmail=v=>{const raw=cleanLogin(v);if(raw.includes('@'))return raw;const u=cleanUsername(raw);return u?u+'@auditar.local':''};
"""
if old not in c: raise RuntimeError('cleanUsername marker ausente')
c=c.replace(old,new,1)

old="""    const username=cleanUsername($('#loginUser').value),password=$('#loginPass').value,name=$('#setupName').value.trim(),btn=$('#btnLogin'),err=$('#loginError');
    if(!username||!password){err.textContent='Informe usuário e senha.';return}
"""
new="""    const loginValue=cleanLogin($('#loginUser').value),username=cleanUsername(loginValue.split('@')[0]),email=loginEmail(loginValue),password=$('#loginPass').value,name=$('#setupName').value.trim(),btn=$('#btnLogin'),err=$('#loginError');
    if(!email||!password){err.textContent='Informe usuário/e-mail e senha.';return}
"""
if old not in c: raise RuntimeError('login const marker ausente')
c=c.replace(old,new,1)

old="""        r=await api('auth_bootstrap_admin',{syncKey:BOOTSTRAP_KEY,name,username,email:`${username}@auditar.local`,password,deviceId:deviceId(),platform:'windows'});
      }else{
        r=await api('auth_login',{username,email:username,password,deviceId:deviceId(),platform:'windows'});
"""
new="""        r=await api('auth_bootstrap_admin',{syncKey:BOOTSTRAP_KEY,name,username,email:email,password,deviceId:deviceId(),platform:'windows'});
      }else{
        r=await api('auth_login',{username,email:email,password,deviceId:deviceId(),platform:'windows'});
"""
if old not in c: raise RuntimeError('auth login marker ausente')
c=c.replace(old,new,1)

old="""    try{const s=await api('auth_status');if(!s?.ok)throw new Error(s?.message||'Central indisponível.');if(s.configured===false){showLogin('A Central Online ainda não foi configurada.');return}if(s.hasUsers!==true){clearSession();showLogin('',true);return}const ok=await verifySavedSession();if(!ok){clearSession();showLogin();return}hideLogin();await refresh()}catch(e){clearSession();showLogin(e.message||'Não foi possível acessar a Central Online.')}
"""
new="""    try{const s=await api('auth_status');if(!s?.ok)throw new Error(s?.message||'Central indisponível.');if(s.configured===false){showLogin('A Central Online ainda não foi configurada.');return}if(s.hasUsers!==true){clearSession();showLogin('',true);return}const ok=await verifySavedSession();if(!ok){clearSession();showLogin();return}hideLogin();await refresh()}catch(e){clearSession();showLogin(e.message||'Não foi possível acessar a Central Online.')}
"""
# keep marker for assertion only

# Don't sanitize login input as username because e-mail must remain valid.
old="""$('#loginUser').oninput=e=>{const v=cleanUsername(e.target.value);if(v!==e.target.value)e.target.value=v};$('#uUsername').oninput=e=>{const v=cleanUsername(e.target.value);if(v!==e.target.value)e.target.value=v};
"""
new="""$('#loginUser').oninput=e=>{const v=cleanLogin(e.target.value).replace(/\s+/g,'');if(v!==e.target.value)e.target.value=v};$('#uUsername').oninput=e=>{const v=cleanUsername(e.target.value);if(v!==e.target.value)e.target.value=v};
"""
if old not in c: raise RuntimeError('login oninput marker ausente')
c=c.replace(old,new,1)

app.write_text(c,encoding='utf-8',newline='\n')

h=html.read_text(encoding='utf-8')
h=h.replace('placeholder="Seu usuário"','placeholder="Usuário ou e-mail"',1)
h=h.replace('Acesso administrativo para controlar usuários do aplicativo de vistoria.','Acesso administrativo para controlar usuários, empresas e permissões do Auditar SST.',1)
html.write_text(h,encoding='utf-8',newline='\n')

p=pkg.read_text(encoding='utf-8')
p=re.sub(r'"version":\s*"[^"]+"','"version": "1.1.0"',p,count=1)
pkg.write_text(p,encoding='utf-8',newline='\n')

assert "const loginEmail=" in app.read_text(encoding='utf-8')
assert "email:email" in app.read_text(encoding='utf-8')
assert 'Usuário ou e-mail' in html.read_text(encoding='utf-8')
assert '"version": "1.1.0"' in pkg.read_text(encoding='utf-8')
print('MASTER_V110_OK')
