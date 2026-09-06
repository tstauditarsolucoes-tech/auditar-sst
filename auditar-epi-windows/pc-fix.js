(() => {
  const TOKEN_KEY='gestaoEpiAuthToken';
  const USER_KEY='gestaoEpiAuthUser';
  const TENANT_KEY='gestaoEpiAuthTenant';
  const TENANT_CODE_KEY='gestaoEpiTenantCode';
  const LEGACY_SYNC_KEY='auditarEpiCentralKey';

  // Sempre inicia sem reaproveitar sessão nem código da empresa no PC.
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(TENANT_KEY);
  localStorage.removeItem(TENANT_CODE_KEY);
  localStorage.removeItem(LEGACY_SYNC_KEY);

  const storageGet=Storage.prototype.getItem;
  const storageSet=Storage.prototype.setItem;
  const storageRemove=Storage.prototype.removeItem;

  // Compatibilidade definitiva com o app.js antigo:
  // - código da empresa nunca fica salvo;
  // - a antiga chave de sync só é considerada presente quando existe login válido.
  Storage.prototype.getItem=function(key){
    if(key===TENANT_CODE_KEY)return '';
    if(key===LEGACY_SYNC_KEY){
      const token=String(storageGet.call(this,TOKEN_KEY)||'').trim();
      return token ? 'AUTHENTICATED_SESSION' : '';
    }
    return storageGet.call(this,key);
  };

  Storage.prototype.setItem=function(key,value){
    if(key===TENANT_CODE_KEY){
      storageRemove.call(this,key);
      return;
    }
    if(key===LEGACY_SYNC_KEY){
      // Não grava mais a chave antiga. A sincronização depende apenas do login.
      storageRemove.call(this,key);
      return;
    }
    return storageSet.call(this,key,value);
  };

  // Impede adaptadores antigos de sincronização de assumirem a conexão.
  window.__gestaoEpiSyncTransportFix=true;

  // Toda chamada de sincronização é convertida para a mesma API autenticada do login.
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

  // Rolagem independente: menu azul e área principal possuem rolagens próprias.
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
      v.textContent='PC v2.0.7';
      card.appendChild(v);
    }

    const status=document.getElementById('syncStatus');
    const time=document.getElementById('syncTime');
    if(status)status.textContent='Aguardando login';
    if(time)time.textContent='—';
  }

  function refreshAfterLogin(){
    const token=String(window.GestaoEpiAuth?.token?.()||'').trim();
    const auth=document.getElementById('gestaoAuthOverlay');
    if(!token||!auth?.classList.contains('hidden'))return;
    const btn=document.getElementById('btnRefresh');
    if(btn)setTimeout(()=>btn.click(),120);
  }

  document.addEventListener('DOMContentLoaded',()=>{
    enforceCleanLogin();
    setTimeout(enforceCleanLogin,0);

    const auth=document.getElementById('gestaoAuthOverlay');
    if(auth){
      const observer=new MutationObserver(refreshAfterLogin);
      observer.observe(auth,{attributes:true,attributeFilter:['class']});
    }
  });
})();