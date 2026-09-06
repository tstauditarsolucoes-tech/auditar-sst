(() => {
  const TOKEN_KEY='gestaoEpiAuthToken';
  const USER_KEY='gestaoEpiAuthUser';
  const TENANT_KEY='gestaoEpiAuthTenant';
  const TENANT_CODE_KEY='gestaoEpiTenantCode';
  const LEGACY_SYNC_KEY='auditarEpiCentralKey';

  // Sempre inicia sem sessão reaproveitada no PC.
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(TENANT_KEY);
  localStorage.removeItem(TENANT_CODE_KEY);
  // O app antigo exige esta chave antes de chamar a sync. Limpamos na abertura
  // e liberamos somente depois que o login autenticado for concluído.
  localStorage.removeItem(LEGACY_SYNC_KEY);

  // Nunca mantém o código da empresa salvo no PC.
  const storageGet=Storage.prototype.getItem;
  const storageSet=Storage.prototype.setItem;
  const storageRemove=Storage.prototype.removeItem;
  Storage.prototype.getItem=function(key){
    if(key===TENANT_CODE_KEY)return '';
    return storageGet.call(this,key);
  };
  Storage.prototype.setItem=function(key,value){
    if(key===TENANT_CODE_KEY){
      storageRemove.call(this,key);
      return;
    }
    return storageSet.call(this,key,value);
  };

  // Impede o adaptador antigo de sincronização de ser instalado.
  window.__gestaoEpiSyncTransportFix=true;

  // Sincronização usa a mesma sessão autenticada do login.
  const previousFetch=window.fetch.bind(window);
  window.fetch=async function(input,init){
    try{
      if(typeof input==='string'&&init?.body&&window.GestaoEpiAuth?.api){
        const body=JSON.parse(init.body);
        if(body?.action==='epi_sync_merge'){
          const token=String(window.GestaoEpiAuth.token?.()||'').trim();
          if(!token){
            return new Response(JSON.stringify({
              ok:false,
              code:'SESSION_REQUIRED',
              message:'Entre no Gestão EPI para sincronizar.'
            }),{
              status:200,
              headers:{'Content-Type':'application/json;charset=utf-8'}
            });
          }
          const extra={...body};
          delete extra.action;
          delete extra.authToken;
          delete extra.syncKey;
          const json=await window.GestaoEpiAuth.api('epi_sync_merge',extra);
          return new Response(JSON.stringify(json),{
            status:200,
            headers:{'Content-Type':'application/json;charset=utf-8'}
          });
        }
      }
    }catch(error){
      console.error('Falha na sincronização autenticada do Gestão EPI:',error);
      return new Response(JSON.stringify({
        ok:false,
        message:'Falha na sincronização: '+String(error?.message||error)
      }),{
        status:200,
        headers:{'Content-Type':'application/json;charset=utf-8'}
      });
    }
    return previousFetch(input,init);
  };

  // Rolagem independente no PC.
  const style=document.createElement('style');
  style.id='gestaoEpiPcIndependentScroll';
  style.textContent=`
    @media (min-width:721px){
      html,body{height:100%;overflow:hidden!important}
      .layout{height:100vh!important;min-height:0!important;overflow:hidden!important}
      .sidebar{position:relative!important;top:auto!important;height:100vh!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important}
      .main{height:100vh!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important}
    }
    .gestao-pc-version{margin-top:8px;font-size:11px;font-weight:800;color:#78908c;text-align:center}
  `;
  document.head.appendChild(style);

  function enableAuthenticatedSync(){
    const token=String(window.GestaoEpiAuth?.token?.()||'').trim();
    const auth=document.getElementById('gestaoAuthOverlay');
    const loggedIn=!!token && !!auth && auth.classList.contains('hidden');
    if(!loggedIn)return false;

    // Compatibilidade com o app.js antigo: apenas libera a chamada de sync.
    // O valor não autentica nada; o backend recebe o token real da sessão.
    localStorage.setItem(LEGACY_SYNC_KEY,'AUTHENTICATED_SESSION');
    const btn=document.getElementById('btnRefresh');
    if(btn)setTimeout(()=>btn.click(),80);
    return true;
  }

  function enforceCleanLogin(){
    const connect=document.getElementById('connectOverlay');
    if(connect){
      connect.classList.add('hidden');
      connect.style.display='none';
    }

    const auth=document.getElementById('gestaoAuthOverlay');
    const tenantCode=document.getElementById('gestaoTenantCode');
    const username=document.getElementById('gestaoAuthUser');
    const password=document.getElementById('gestaoAuthPass');
    if(tenantCode)tenantCode.value='';
    if(username)username.value='';
    if(password)password.value='';
    if(auth)auth.classList.remove('hidden');

    const card=auth?.querySelector('.gestao-auth-card');
    if(card&&!card.querySelector('.gestao-pc-version')){
      const v=document.createElement('div');
      v.className='gestao-pc-version';
      v.textContent='PC v2.0.6';
      card.appendChild(v);
    }

    const status=document.getElementById('syncStatus');
    const time=document.getElementById('syncTime');
    if(status)status.textContent='Aguardando login';
    if(time)time.textContent='—';
  }

  document.addEventListener('DOMContentLoaded',()=>{
    enforceCleanLogin();
    setTimeout(enforceCleanLogin,0);

    const auth=document.getElementById('gestaoAuthOverlay');
    if(auth){
      const observer=new MutationObserver(()=>enableAuthenticatedSync());
      observer.observe(auth,{attributes:true,attributeFilter:['class']});
    }
  });
})();