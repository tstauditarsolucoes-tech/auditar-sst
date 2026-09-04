(() => {
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const TOKEN_KEY='gestaoEpiAuthToken';
  const USER_KEY='gestaoEpiAuthUser';
  const TENANT_KEY='gestaoEpiAuthTenant';
  const TENANT_CODE_KEY='gestaoEpiTenantCode';
  const LOCAL_TENANT_KEY='gestaoEpiLocalTenantId';
  const VALIDATED_AT_KEY='gestaoEpiAuthValidatedAt';
  const DEVICE_STORE='auditarEpiDeviceId';
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const REV_KEY='auditarEpiServerRevision';
  const nativeFetch=window.fetch.bind(window);
  let currentUser=null,currentTenant=null,ready=false;

  const $=(s,r=document)=>r.querySelector(s);
  function token(){return (localStorage.getItem(TOKEN_KEY)||'').trim();}
  function savedUser(){try{return JSON.parse(localStorage.getItem(USER_KEY)||'null');}catch{return null;}}
  function savedTenant(){try{return JSON.parse(localStorage.getItem(TENANT_KEY)||'null');}catch{return null;}}
  function deviceId(){let id=localStorage.getItem(DEVICE_STORE);if(!id){id=`campo_${Date.now()}_${Math.random().toString(36).slice(2,10)}`;localStorage.setItem(DEVICE_STORE,id);}return id;}
  function deviceLabel(){return `Campo • ${navigator.platform||'Android'}`.slice(0,80);}
  function roleLabel(r){return r==='admin'?'Administrador':r==='campo'?'Campo':'Consulta';}
  function escapeHtml(v=''){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function toast(msg){const el=$('#toast');if(!el)return;el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);}

  function saveSession(t,u,tenant){
    prepareTenantStorage(tenant?.id||'');
    localStorage.setItem(TOKEN_KEY,t);localStorage.setItem(USER_KEY,JSON.stringify(u));localStorage.setItem(TENANT_KEY,JSON.stringify(tenant));localStorage.setItem(TENANT_CODE_KEY,tenant?.code||'');localStorage.setItem(VALIDATED_AT_KEY,String(Date.now()));currentUser=u;currentTenant=tenant;
  }
  function clearSession(){localStorage.removeItem(TOKEN_KEY);localStorage.removeItem(USER_KEY);localStorage.removeItem(TENANT_KEY);localStorage.removeItem(VALIDATED_AT_KEY);currentUser=null;currentTenant=null;}

  function prepareTenantStorage(tenantId){
    if(!tenantId)return;
    const old=localStorage.getItem(LOCAL_TENANT_KEY)||'';
    if(old===tenantId)return;
    const existingApp=localStorage.getItem(APP_KEY),existingStock=localStorage.getItem(STOCK_KEY);
    if(existingApp||existingStock){
      try{localStorage.setItem('gestaoEpiPreviousTenantBackupV1',JSON.stringify({tenantId:old||'legacy',savedAt:new Date().toISOString(),app:existingApp?JSON.parse(existingApp):null,stock:existingStock?JSON.parse(existingStock):null}));}catch(_){}
    }
    localStorage.removeItem(APP_KEY);localStorage.removeItem(STOCK_KEY);localStorage.removeItem(REV_KEY);localStorage.setItem(LOCAL_TENANT_KEY,tenantId);
  }

  function tokenStillValid(){
    try{const p=token().split('.')[0];if(!p)return false;const base=p.replace(/-/g,'+').replace(/_/g,'/');const padded=base+'='.repeat((4-base.length%4)%4);const payload=JSON.parse(decodeURIComponent(escape(atob(padded))));return Number(payload.exp||0)>Date.now();}catch{return false;}
  }
  function offlineSessionFresh(){return Date.now()-Number(localStorage.getItem(VALIDATED_AT_KEY)||0)<24*60*60*1000;}

  async function api(action,extra={}){
    const body={action,...extra};if(token()&&!body.authToken)body.authToken=token();
    const res=await nativeFetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify(body)});return res.json();
  }

  window.fetch=async function(input,init){
    if(typeof input==='string'&&input===ENDPOINT&&init?.body){
      try{const body=JSON.parse(init.body);if(body.action==='epi_sync_merge'&&!body.authToken)body.authToken=token();if(body.action==='epi_sync_merge'&&!body.deviceId)body.deviceId=deviceId();init={...init,body:JSON.stringify(body)};}catch(_){}
    }
    const res=await nativeFetch(input,init);
    try{res.clone().json().then(j=>{if(j&&j.ok===false&&['SESSION_EXPIRED','SESSION_INVALID','USER_DISABLED','DEVICE_DISABLED','LICENSE_EXPIRED','LICENSE_SUSPENDED'].includes(j.code))logout(false,j.message);}).catch(()=>{});}catch(_){}
    return res;
  };

  function injectStyles(){
    if($('#epiAuthStyle'))return;const s=document.createElement('style');s.id='epiAuthStyle';s.textContent=`
      .epi-auth-overlay{position:fixed;inset:0;z-index:20000;background:#eef5f4;display:flex;align-items:center;justify-content:center;padding:18px}.epi-auth-overlay.hidden{display:none}.epi-auth-card{width:min(430px,100%);background:#fff;border-radius:24px;padding:22px;box-shadow:0 24px 60px rgba(19,61,57,.18)}.epi-auth-mark{width:58px;height:58px;border-radius:18px;background:#0f8f83;color:#fff;display:grid;place-items:center;font-size:27px;margin-bottom:13px}.epi-auth-card h1{margin:0;color:#173d39;font-size:25px}.epi-auth-card>p{color:#617b77;font-size:13px;line-height:1.45;margin:7px 0 16px}.epi-auth-card label{display:block;font-weight:800;color:#355b57;font-size:12px;margin:10px 0}.epi-auth-card input{width:100%;box-sizing:border-box;margin-top:5px;min-height:49px;border:1px solid #cededa;border-radius:13px;padding:0 13px;font-size:15px;text-transform:none}.epi-auth-card button{width:100%;min-height:52px;border:0;border-radius:14px;background:#0f766e;color:#fff;font-weight:900;font-size:15px;margin-top:8px}.epi-auth-error{min-height:18px;color:#b42318;font-size:12px;font-weight:800;margin-top:9px}.epi-user-chip{display:flex;align-items:center;gap:7px;font-size:10px;font-weight:850;color:#355b57}.epi-user-chip button{border:0;background:#edf6f4;color:#0f766e;border-radius:9px;padding:7px 9px;font-weight:850}.epi-tenant-name{max-width:110px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block}
    `;document.head.appendChild(s);
  }

  function injectOverlay(){
    if($('#epiAuthOverlay'))return;const d=document.createElement('div');d.id='epiAuthOverlay';d.className='epi-auth-overlay';d.innerHTML=`<div class="epi-auth-card"><div class="epi-auth-mark">🦺</div><h1>Entrar no Gestão EPI</h1><p>Acesso exclusivo da empresa licenciada.</p><label>Código da empresa<input id="epiTenantCode" autocomplete="organization" autocapitalize="characters" placeholder="Ex.: EMPRESA-X"></label><label>Usuário<input id="epiAuthUser" autocomplete="username" autocapitalize="none" placeholder="Seu usuário"></label><label>Senha<input id="epiAuthPass" type="password" autocomplete="current-password" placeholder="Sua senha"></label><button id="epiAuthSubmit" type="button">Entrar</button><div id="epiAuthError" class="epi-auth-error"></div></div>`;document.body.appendChild(d);$('#epiTenantCode').value=localStorage.getItem(TENANT_CODE_KEY)||'';$('#epiAuthSubmit').addEventListener('click',submitAuth);$('#epiAuthPass').addEventListener('keydown',e=>{if(e.key==='Enter')submitAuth();});
  }
  function showLogin(msg=''){injectStyles();injectOverlay();$('#epiAuthOverlay').classList.remove('hidden');$('#epiAuthError').textContent=msg||'';setTimeout(()=>($('#epiTenantCode').value?$('#epiAuthUser'):$('#epiTenantCode'))?.focus(),80);}
  function hideLogin(){$('#epiAuthOverlay')?.classList.add('hidden');}

  async function submitAuth(){
    const tenantCode=($('#epiTenantCode')?.value||'').trim(),username=($('#epiAuthUser')?.value||'').trim(),password=$('#epiAuthPass')?.value||'',btn=$('#epiAuthSubmit'),err=$('#epiAuthError');
    if(!tenantCode||!username||!password){err.textContent='Informe código da empresa, usuário e senha.';return;}if(!navigator.onLine){err.textContent='O login precisa de internet.';return;}
    btn.disabled=true;btn.textContent='Aguarde…';err.textContent='';
    try{const r=await api('tenant_login',{tenantCode,username,password,deviceId:deviceId(),deviceLabel:deviceLabel()});if(!r?.ok)throw new Error(r?.message||'Não foi possível entrar.');saveSession(r.token,r.user,r.tenant);hideLogin();applyUser(r.user,r.tenant);ready=true;document.dispatchEvent(new CustomEvent('gestao-epi-auth-ready',{detail:{user:r.user,tenant:r.tenant}}));}
    catch(e){err.textContent=e.message||'Falha no login.';}finally{btn.disabled=false;btn.textContent='Entrar';}
  }

  function injectUserChip(){
    const top=$('.topbar');if(!top)return;let chip=$('#epiUserChip');if(!chip){chip=document.createElement('div');chip.id='epiUserChip';chip.className='epi-user-chip';top.appendChild(chip);}if(currentUser)chip.innerHTML=`<span><span class="epi-tenant-name">🏢 ${escapeHtml(currentTenant?.name||currentTenant?.code||'Empresa')}</span>👤 ${escapeHtml(currentUser.name||currentUser.username)}<br><small>${roleLabel(currentUser.role)}</small></span><button id="epiLogout" type="button">Sair</button>`;$('#epiLogout')?.addEventListener('click',()=>logout(true));
  }
  function markHidden(el){if(!el)return;el.dataset.authHidden='1';el.style.display='none';}
  function resetHidden(){document.querySelectorAll('[data-auth-hidden="1"]').forEach(el=>{el.style.display='';delete el.dataset.authHidden;});}

  function applyUser(u,tenant){
    currentUser=u;currentTenant=tenant||currentTenant;document.body.dataset.epiRole=u.role;resetHidden();injectUserChip();const admin=u.role==='admin',campo=u.role==='campo';
    if(!admin){document.querySelectorAll('#companyForm,#workerForm,#epiForm,#btnStockSave,#btnCommitImport,.worker-import-actions').forEach(markHidden);document.querySelectorAll('[data-bio-worker]').forEach(markHidden);}
    if(!admin&&!campo)document.querySelectorAll('#btnSaveDelivery,[data-go="delivery"],#btnAddItem').forEach(markHidden);
    if(!$('#btnSaveDelivery')?.dataset.authStampBound){const b=$('#btnSaveDelivery');if(b){b.dataset.authStampBound='1';b.addEventListener('click',()=>setTimeout(stampLatestDelivery,180));}}
    if(!window.__gestaoEpiAuthObserver){window.__gestaoEpiAuthObserver=new MutationObserver(()=>{if(currentUser?.role!=='admin')document.querySelectorAll('[data-bio-worker]').forEach(markHidden);});window.__gestaoEpiAuthObserver.observe(document.body,{childList:true,subtree:true});}
  }

  function stampLatestDelivery(){
    if(!currentUser||!currentTenant)return;try{const root=JSON.parse(localStorage.getItem(APP_KEY)||'{}');const rows=Array.isArray(root.deliveries)?root.deliveries:[];const d=rows[0];if(!d||Date.now()-new Date(d.createdAt||0).getTime()>15000)return;d.tenantId=currentTenant.id;d.registeredBy={username:currentUser.username,name:currentUser.name||currentUser.username,role:currentUser.role};d.registeredByAt=new Date().toISOString();d.updatedAt=new Date().toISOString();localStorage.setItem(APP_KEY,JSON.stringify(root));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed'));}catch(_){}
  }

  function logout(show=true,msg=''){clearSession();resetHidden();if(show||msg)showLogin(msg||'Você saiu do sistema.');}
  function useCachedOffline(){const u=savedUser(),t=savedTenant();if(!u||!t||!tokenStillValid()||!offlineSessionFresh())return false;currentUser=u;currentTenant=t;hideLogin();applyUser(u,t);ready=true;document.dispatchEvent(new CustomEvent('gestao-epi-auth-ready',{detail:{user:u,tenant:t}}));toast('Modo offline • acesso temporário');return true;}

  async function init(){
    injectStyles();injectOverlay();if(!navigator.onLine&&useCachedOffline())return;
    if(token()){
      try{const me=await api('tenant_me');if(me?.ok){saveSession(token(),me.user,me.tenant);hideLogin();applyUser(me.user,me.tenant);ready=true;document.dispatchEvent(new CustomEvent('gestao-epi-auth-ready',{detail:{user:me.user,tenant:me.tenant}}));return;}clearSession();}
      catch(_){if(useCachedOffline())return;}
    }
    showLogin();
  }

  window.GestaoEpiAuth={api,token,user:()=>currentUser||savedUser(),tenant:()=>currentTenant||savedTenant(),logout,isReady:()=>ready,deviceId};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();