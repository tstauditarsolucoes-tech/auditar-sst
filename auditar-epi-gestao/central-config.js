(() => {
  const OLD_KEY='auditarEpiSyncKey';
  const CENTRAL_KEY='auditarEpiCentralKey';
  const OLD_ENDPOINT='https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';

  const TOKEN_KEY='gestaoEpiAuthToken';
  const USER_KEY='gestaoEpiAuthUser';
  const TENANT_KEY='gestaoEpiAuthTenant';
  const TENANT_CODE_KEY='gestaoEpiTenantCode';
  const DEVICE_KEY='auditarEpiGestaoDeviceId';

  const nativeGet=Storage.prototype.getItem;
  const nativeSet=Storage.prototype.setItem;
  const nativeRemove=Storage.prototype.removeItem;
  const nativeFetch=window.fetch.bind(window);

  window.__GESTAO_AUTH_CORE_ACTIVE=true;

  function lsGet(key){return nativeGet.call(localStorage,key);}
  function lsSet(key,value){return nativeSet.call(localStorage,key,value);}
  function lsRemove(key){return nativeRemove.call(localStorage,key);}

  /* O app legado ainda procura uma chave local. No modelo comercial a
     autorização real é o token da sessão, então devolvemos apenas um marcador
     interno para impedir que a antiga tela de chave apareça. */
  Storage.prototype.getItem=function(key){
    if(key===OLD_KEY||key===CENTRAL_KEY)return 'commercial-session';
    return nativeGet.call(this,key);
  };
  Storage.prototype.setItem=function(key,value){
    if(key===OLD_KEY||key===CENTRAL_KEY)return;
    return nativeSet.call(this,key,value);
  };
  Storage.prototype.removeItem=function(key){
    if(key===OLD_KEY||key===CENTRAL_KEY)return;
    return nativeRemove.call(this,key);
  };

  function token(){return String(lsGet(TOKEN_KEY)||'').trim();}

  function deviceId(){
    let id=String(lsGet(DEVICE_KEY)||'').trim();
    if(!id){
      id=`gestao_${Date.now()}_${Math.random().toString(36).slice(2,10)}`;
      lsSet(DEVICE_KEY,id);
    }
    return id;
  }

  function deviceLabel(){
    return `Gestão PC • ${navigator.platform||'Windows'}`.slice(0,80);
  }

  /* Redireciona qualquer chamada antiga para a central comercial e injeta o
     token da empresa na sincronização. */
  window.fetch=function(input,init){
    let target=input;
    if(typeof target==='string'&&target===OLD_ENDPOINT)target=ENDPOINT;

    if(typeof target==='string'&&target===ENDPOINT&&init&&init.body){
      try{
        const body=JSON.parse(init.body);
        if(body.action==='epi_sync_merge'&&!body.authToken&&token()){
          body.authToken=token();
          init={...init,body:JSON.stringify(body)};
        }
      }catch(_){ }
    }
    return nativeFetch(target,init);
  };

  function sanitizeText(root=document.body){
    if(!root)return;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    let node;
    while((node=walker.nextNode())){
      const old=node.nodeValue||'';
      const next=old.replace(/AUDITAR\s+EPI/gi,'GESTÃO EPI').replace(/Auditar\s+EPI/gi,'Gestão EPI');
      if(next!==old)node.nodeValue=next;
    }
  }

  function hideLegacyConnect(){
    const overlay=document.getElementById('connectOverlay');
    if(!overlay)return;
    overlay.classList.add('hidden');
    overlay.style.display='none';
    overlay.setAttribute('aria-hidden','true');
  }

  function applyNeutralBrand(){
    document.title='Gestão EPI • Gestão';
    document.querySelectorAll('.logo').forEach(el=>el.innerHTML='GESTÃO <span>EPI</span>');
    const sidebar=document.querySelector('.sidebar-brand small');
    if(sidebar)sidebar.textContent='GESTÃO';
    sanitizeText();
  }

  function ensureAuthStyle(){
    if(document.getElementById('gestaoAuthStyle'))return;
    const s=document.createElement('style');
    s.id='gestaoAuthStyle';
    s.textContent=`
      .gestao-auth-overlay{position:fixed;inset:0;z-index:50000;background:linear-gradient(135deg,#e8f5f3,#f7faf9);display:flex;align-items:center;justify-content:center;padding:24px;font-family:Arial,sans-serif}
      .gestao-auth-overlay.hidden{display:none}
      .gestao-auth-card{width:min(430px,100%);background:#fff;border-radius:24px;padding:28px;box-shadow:0 30px 80px rgba(22,61,56,.18)}
      .gestao-auth-mark{width:62px;height:62px;border-radius:19px;background:#0f8f83;color:#fff;display:grid;place-items:center;font-size:29px;margin-bottom:14px}
      .gestao-auth-card h1{margin:0;color:#173d39;font-size:28px}
      .gestao-auth-card>p{color:#617b77;font-size:14px;line-height:1.5;margin:8px 0 18px}
      .gestao-auth-card label{display:block;font-size:12px;font-weight:850;color:#355b57;margin:12px 0;text-transform:uppercase}
      .gestao-auth-card input{width:100%;box-sizing:border-box;min-height:50px;border:1px solid #cfdfdc;border-radius:13px;padding:0 13px;margin-top:6px;font-size:16px;outline:none}
      .gestao-auth-card input:focus{border-color:#0fa88e;box-shadow:0 0 0 3px rgba(15,168,142,.12)}
      #gestaoTenantCode,#gestaoAuthUser{text-transform:uppercase}
      #gestaoAuthPass{text-transform:none}
      .gestao-auth-card>button{width:100%;min-height:52px;border:0;border-radius:14px;background:#0fa88e;color:white;font-weight:900;font-size:16px;cursor:pointer;margin-top:8px}
      .gestao-auth-card>button:disabled{opacity:.65;cursor:wait}
      .gestao-auth-error{min-height:18px;margin-top:10px;color:#b42318;font-size:12px;font-weight:800}
      .gestao-user-chip{display:flex;align-items:center;gap:10px;background:#f1f7f6;border:1px solid #d8e7e4;border-radius:13px;padding:7px 10px;font-size:11px;color:#355b57}
      .gestao-user-chip b{display:block}
      .gestao-user-chip button{border:0;background:transparent;color:#0f766e;font-weight:900;cursor:pointer}
    `;
    document.head.appendChild(s);
  }

  function ensureAuthOverlay(){
    let d=document.getElementById('gestaoAuthOverlay');
    if(d)return d;
    d=document.createElement('div');
    d.id='gestaoAuthOverlay';
    d.className='gestao-auth-overlay';
    d.innerHTML=`
      <div class="gestao-auth-card">
        <div class="gestao-auth-mark">🦺</div>
        <h1>Entrar no Gestão EPI</h1>
        <p>Acesso exclusivo da empresa licenciada.</p>
        <label>CÓDIGO DA EMPRESA
          <input id="gestaoTenantCode" autocomplete="organization" placeholder="EX.: EMPRESA-X">
        </label>
        <label>USUÁRIO
          <input id="gestaoAuthUser" autocomplete="username" placeholder="SEU USUÁRIO">
        </label>
        <label>SENHA
          <input id="gestaoAuthPass" type="password" autocomplete="current-password" placeholder="SUA SENHA">
        </label>
        <button id="gestaoAuthSubmit" type="button">Entrar</button>
        <div id="gestaoAuthError" class="gestao-auth-error"></div>
      </div>`;
    document.body.appendChild(d);

    const tenant=document.getElementById('gestaoTenantCode');
    const user=document.getElementById('gestaoAuthUser');
    const pass=document.getElementById('gestaoAuthPass');
    tenant.value=String(lsGet(TENANT_CODE_KEY)||'').toUpperCase();
    tenant.addEventListener('input',()=>{tenant.value=tenant.value.toUpperCase();});
    user.addEventListener('input',()=>{user.value=user.value.toUpperCase();});
    document.getElementById('gestaoAuthSubmit').addEventListener('click',login);
    pass.addEventListener('keydown',e=>{if(e.key==='Enter')login();});
    return d;
  }

  function showAuth(message=''){
    ensureAuthStyle();
    const d=ensureAuthOverlay();
    d.classList.remove('hidden');
    const err=document.getElementById('gestaoAuthError');
    if(err)err.textContent=message||'';
    setTimeout(()=>{
      const tenant=document.getElementById('gestaoTenantCode');
      const user=document.getElementById('gestaoAuthUser');
      (tenant&&tenant.value?user:tenant)?.focus();
    },50);
  }

  function hideAuth(){
    document.getElementById('gestaoAuthOverlay')?.classList.add('hidden');
  }

  function clearSession(){
    lsRemove(TOKEN_KEY);
    lsRemove(USER_KEY);
    lsRemove(TENANT_KEY);
  }

  function saveSession(r){
    lsSet(TOKEN_KEY,String(r.token||''));
    lsSet(USER_KEY,JSON.stringify(r.user||{}));
    lsSet(TENANT_KEY,JSON.stringify(r.tenant||{}));
    if(r.tenant?.code)lsSet(TENANT_CODE_KEY,String(r.tenant.code).toUpperCase());
  }

  async function api(action,extra={}){
    const body={action,...extra};
    if(token()&&!body.authToken)body.authToken=token();
    const res=await nativeFetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify(body)});
    return res.json();
  }

  function userChip(user,tenant){
    const mount=document.querySelector('.top-actions')||document.querySelector('.topbar');
    if(!mount)return;
    let chip=document.getElementById('gestaoUserChip');
    if(!chip){
      chip=document.createElement('div');
      chip.id='gestaoUserChip';
      chip.className='gestao-user-chip';
      mount.appendChild(chip);
    }
    const role=user?.role==='admin'?'Administrador':user?.role==='campo'?'Campo':'Consulta';
    chip.innerHTML=`<span><b>🏢 ${escapeHtml(tenant?.name||tenant?.code||'Empresa')}</b>👤 ${escapeHtml(user?.name||user?.username||'Usuário')} • ${role}</span><button id="gestaoLogout" type="button">Sair</button>`;
    document.getElementById('gestaoLogout').onclick=()=>{
      clearSession();
      chip.remove();
      showAuth('Você saiu do sistema.');
    };
  }

  function escapeHtml(v=''){
    return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function syncSoon(){
    setTimeout(()=>document.getElementById('btnRefresh')?.click(),250);
    setTimeout(()=>document.getElementById('btnRefresh')?.click(),1000);
  }

  async function login(){
    const tenantEl=document.getElementById('gestaoTenantCode');
    const userEl=document.getElementById('gestaoAuthUser');
    const passEl=document.getElementById('gestaoAuthPass');
    const btn=document.getElementById('gestaoAuthSubmit');
    const err=document.getElementById('gestaoAuthError');
    const tenantCode=String(tenantEl?.value||'').trim().toUpperCase();
    const username=String(userEl?.value||'').trim();
    const password=String(passEl?.value||'');

    if(!tenantCode||!username||!password){
      if(err)err.textContent='Informe código da empresa, usuário e senha.';
      return;
    }

    btn.disabled=true;
    btn.textContent='Aguarde…';
    if(err)err.textContent='';
    try{
      const r=await api('tenant_login',{tenantCode,username,password,deviceId:deviceId(),deviceLabel:deviceLabel()});
      if(!r?.ok)throw new Error(r?.message||'Falha no login.');
      saveSession(r);
      hideAuth();
      userChip(r.user,r.tenant);
      syncSoon();
    }catch(e){
      if(err)err.textContent=e?.message||'Não foi possível entrar.';
    }finally{
      btn.disabled=false;
      btn.textContent='Entrar';
    }
  }

  async function initCommercialAuth(){
    hideLegacyConnect();
    applyNeutralBrand();
    ensureAuthStyle();
    ensureAuthOverlay();

    if(!token()){
      showAuth();
      return;
    }

    /* Mantém a tela de login visível enquanto valida a sessão salva. */
    showAuth('Validando acesso…');
    try{
      const r=await api('tenant_me');
      if(!r?.ok)throw new Error(r?.message||'Sessão expirada.');
      hideAuth();
      userChip(r.user,r.tenant);
      syncSoon();
    }catch(e){
      clearSession();
      showAuth(e?.message||'Entre novamente.');
    }
  }

  window.GestaoEpiAuth={
    api,
    token,
    logout(){
      clearSession();
      document.getElementById('gestaoUserChip')?.remove();
      showAuth('Você saiu do sistema.');
    },
    deviceId
  };

  hideLegacyConnect();
  applyNeutralBrand();

  document.addEventListener('DOMContentLoaded',()=>{
    hideLegacyConnect();
    applyNeutralBrand();
    const obs=new MutationObserver(()=>sanitizeText());
    obs.observe(document.body,{childList:true,subtree:true,characterData:true});
    initCommercialAuth();
    setTimeout(applyNeutralBrand,300);
  },{once:true});
})();