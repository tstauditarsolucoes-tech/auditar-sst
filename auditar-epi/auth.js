(() => {
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const SYNC_KEY='auditarEpiCentralKey';
  const TOKEN_KEY='gestaoEpiAuthToken';
  const USER_KEY='gestaoEpiAuthUser';
  const nativeFetch=window.fetch.bind(window);
  let currentUser=null;
  let ready=false;

  const $=(s,r=document)=>r.querySelector(s);

  function syncKey(){return (localStorage.getItem(SYNC_KEY)||'').trim();}
  function token(){return (localStorage.getItem(TOKEN_KEY)||'').trim();}
  function user(){try{return JSON.parse(localStorage.getItem(USER_KEY)||'null');}catch{return null;}}
  function saveSession(t,u){localStorage.setItem(TOKEN_KEY,t);localStorage.setItem(USER_KEY,JSON.stringify(u));currentUser=u;}
  function clearSession(){localStorage.removeItem(TOKEN_KEY);localStorage.removeItem(USER_KEY);currentUser=null;}
  function roleLabel(r){return r==='admin'?'Administrador':r==='campo'?'Campo':'Consulta';}

  async function api(action,extra={}){
    const body={action,syncKey:syncKey(),...extra};
    if(token()&&!body.authToken)body.authToken=token();
    const res=await nativeFetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify(body)});
    return res.json();
  }

  window.fetch=async function(input,init){
    if(typeof input==='string'&&input===ENDPOINT&&init?.body){
      try{
        const body=JSON.parse(init.body);
        if(body.action==='epi_sync_merge'&&!body.authToken)body.authToken=token();
        init={...init,body:JSON.stringify(body)};
      }catch(_){}
    }
    const res=await nativeFetch(input,init);
    try{
      const clone=res.clone();
      clone.json().then(j=>{
        if(j&&j.ok===false&&(j.code==='SESSION_EXPIRED'||j.code==='USER_DISABLED')) logout(false,j.message);
      }).catch(()=>{});
    }catch(_){}
    return res;
  };

  function injectStyles(){
    if($('#epiAuthStyle'))return;
    const s=document.createElement('style');s.id='epiAuthStyle';s.textContent=`
      .epi-auth-overlay{position:fixed;inset:0;z-index:20000;background:#eef5f4;display:flex;align-items:center;justify-content:center;padding:18px}.epi-auth-overlay.hidden{display:none}
      .epi-auth-card{width:min(430px,100%);background:#fff;border-radius:24px;padding:22px;box-shadow:0 24px 60px rgba(19,61,57,.18)}.epi-auth-mark{width:58px;height:58px;border-radius:18px;background:#0f8f83;color:#fff;display:grid;place-items:center;font-size:27px;margin-bottom:13px}.epi-auth-card h1{margin:0;color:#173d39;font-size:25px}.epi-auth-card>p{color:#617b77;font-size:13px;line-height:1.45;margin:7px 0 16px}.epi-auth-card label{display:block;font-weight:800;color:#355b57;font-size:12px;margin:10px 0}.epi-auth-card input{width:100%;box-sizing:border-box;margin-top:5px;min-height:49px;border:1px solid #cededa;border-radius:13px;padding:0 13px;font-size:15px}.epi-auth-card button{width:100%;min-height:52px;border:0;border-radius:14px;background:#0f766e;color:#fff;font-weight:900;font-size:15px;margin-top:8px}.epi-auth-error{min-height:18px;color:#b42318;font-size:12px;font-weight:800;margin-top:9px}.epi-user-chip{display:flex;align-items:center;gap:7px;font-size:10px;font-weight:850;color:#355b57}.epi-user-chip button{border:0;background:#edf6f4;color:#0f766e;border-radius:9px;padding:7px 9px;font-weight:850}.epi-role-readonly{display:none!important}
    `;document.head.appendChild(s);
  }

  function injectOverlay(){
    if($('#epiAuthOverlay'))return;
    const d=document.createElement('div');d.id='epiAuthOverlay';d.className='epi-auth-overlay';d.innerHTML=`
      <div class="epi-auth-card">
        <div class="epi-auth-mark">🦺</div>
        <h1 id="epiAuthTitle">Entrar no Gestão EPI</h1>
        <p id="epiAuthText">Informe seu usuário e senha para acessar o sistema.</p>
        <div id="epiAuthNameWrap" style="display:none"><label>Seu nome<input id="epiAuthName" autocomplete="name" placeholder="Ex.: Luan Sena"></label></div>
        <label>Usuário<input id="epiAuthUser" autocomplete="username" autocapitalize="none" placeholder="Ex.: luan"></label>
        <label>Senha<input id="epiAuthPass" type="password" autocomplete="current-password" placeholder="Sua senha"></label>
        <button id="epiAuthSubmit" type="button">Entrar</button>
        <div id="epiAuthError" class="epi-auth-error"></div>
      </div>`;
    document.body.appendChild(d);
    $('#epiAuthSubmit').addEventListener('click',submitAuth);
    $('#epiAuthPass').addEventListener('keydown',e=>{if(e.key==='Enter')submitAuth();});
  }

  let setupMode=false;
  function showLogin(setup=false,msg=''){
    setupMode=setup;injectStyles();injectOverlay();
    $('#epiAuthOverlay').classList.remove('hidden');
    $('#epiAuthNameWrap').style.display=setup?'block':'none';
    $('#epiAuthTitle').textContent=setup?'Criar administrador':'Entrar no Gestão EPI';
    $('#epiAuthText').textContent=setup?'Primeiro acesso: crie o usuário administrador do sistema.':'Informe seu usuário e senha para acessar.';
    $('#epiAuthSubmit').textContent=setup?'Criar administrador':'Entrar';
    $('#epiAuthPass').setAttribute('autocomplete',setup?'new-password':'current-password');
    $('#epiAuthError').textContent=msg||'';
    setTimeout(()=>$('#epiAuthUser')?.focus(),80);
  }
  function hideLogin(){$('#epiAuthOverlay')?.classList.add('hidden');}

  async function submitAuth(){
    const username=($('#epiAuthUser')?.value||'').trim();
    const password=$('#epiAuthPass')?.value||'';
    const btn=$('#epiAuthSubmit');const err=$('#epiAuthError');
    if(!username||!password){err.textContent='Informe usuário e senha.';return;}
    btn.disabled=true;btn.textContent='Aguarde…';err.textContent='';
    try{
      const r=setupMode?await api('auth_bootstrap_admin',{username,password,name:($('#epiAuthName')?.value||'').trim()}):await api('auth_login',{username,password});
      if(!r?.ok)throw new Error(r?.message||'Não foi possível entrar.');
      saveSession(r.token,r.user);hideLogin();applyUser(r.user);ready=true;
      document.dispatchEvent(new CustomEvent('gestao-epi-auth-ready',{detail:r.user}));
    }catch(e){err.textContent=e.message||'Falha no login.';}
    finally{btn.disabled=false;btn.textContent=setupMode?'Criar administrador':'Entrar';}
  }

  function injectUserChip(){
    const top=$('.topbar');if(!top)return;
    let chip=$('#epiUserChip');if(!chip){chip=document.createElement('div');chip.id='epiUserChip';chip.className='epi-user-chip';top.appendChild(chip);}
    if(currentUser)chip.innerHTML=`<span>👤 ${escapeHtml(currentUser.name||currentUser.username)}<br><small>${roleLabel(currentUser.role)}</small></span><button id="epiLogout" type="button">Sair</button>`;
    $('#epiLogout')?.addEventListener('click',()=>logout(true));
  }

  function applyUser(u){
    currentUser=u;document.body.dataset.epiRole=u.role;injectUserChip();
    const admin=u.role==='admin', campo=u.role==='campo';
    const disable=(sel,hide=true)=>document.querySelectorAll(sel).forEach(el=>{if(hide)el.style.display='none';else el.disabled=true;});
    if(!admin){
      disable('#companyForm,#workerForm,#epiForm,#btnStockSave,#btnCommitImport,.worker-import-actions');
      document.querySelectorAll('[data-bio-worker]').forEach(b=>b.style.display='none');
    }
    if(!admin&&!campo){
      disable('#btnSaveDelivery,[data-go="delivery"]');
      disable('#btnAddItem');
    }
    const obs=new MutationObserver(()=>{
      if(currentUser?.role!=='admin')document.querySelectorAll('[data-bio-worker]').forEach(b=>b.style.display='none');
    });
    obs.observe(document.body,{childList:true,subtree:true});
  }

  function escapeHtml(v=''){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

  function logout(show=true,msg=''){
    clearSession();
    if(show||msg)showLogin(false,msg||'Você saiu do sistema.');
    else showLogin(false,msg);
  }

  async function init(){
    injectStyles();injectOverlay();
    if(!syncKey()){showLogin(false,'A central ainda não está configurada neste aparelho.');return;}
    try{
      const status=await api('auth_status');
      if(!status?.ok){showLogin(false,status?.message||'Atualize a central para ativar o login.');return;}
      if(!status.configured){showLogin(true);return;}
      if(token()){
        const me=await api('auth_me');
        if(me?.ok){currentUser=me.user;hideLogin();applyUser(me.user);ready=true;document.dispatchEvent(new CustomEvent('gestao-epi-auth-ready',{detail:me.user}));return;}
        clearSession();
      }
      showLogin(false);
    }catch(_){showLogin(false,'Não foi possível conectar à central. Verifique a internet.');}
  }

  window.GestaoEpiAuth={api,token,user:()=>currentUser||user(),logout,isReady:()=>ready};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
