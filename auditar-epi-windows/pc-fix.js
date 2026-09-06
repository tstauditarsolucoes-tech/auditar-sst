(() => {
  const TOKEN_KEY='gestaoEpiAuthToken';
  const USER_KEY='gestaoEpiAuthUser';
  const TENANT_KEY='gestaoEpiAuthTenant';
  const LAUNCH_KEY='gestaoEpiPcLaunchAuthV1';

  // Uma autenticação nova a cada abertura do programa, sem apagar o código da empresa.
  if(!sessionStorage.getItem(LAUNCH_KEY)){
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TENANT_KEY);
    sessionStorage.setItem(LAUNCH_KEY,'1');
  }

  // Impede o adaptador antigo de sincronização de ser instalado.
  window.__gestaoEpiSyncTransportFix=true;

  // No PC, a sincronização usa a mesma sessão autenticada do login.
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

  // Rolagem independente: menu azul e conteúdo branco não arrastam um ao outro.
  const style=document.createElement('style');
  style.id='gestaoEpiPcIndependentScroll';
  style.textContent=`
    @media (min-width:721px){
      html,body{height:100%;overflow:hidden!important}
      .layout{height:100vh!important;min-height:0!important;overflow:hidden!important}
      .sidebar{position:relative!important;top:auto!important;height:100vh!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important}
      .main{height:100vh!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important}
    }
  `;
  document.head.appendChild(style);

  document.addEventListener('DOMContentLoaded',()=>{
    const connect=document.getElementById('connectOverlay');
    if(connect){
      connect.classList.add('hidden');
      connect.style.display='none';
    }

    // Enquanto a tela de login estiver aberta, não deixa a interface parecer travada.
    const auth=document.getElementById('gestaoAuthOverlay');
    if(auth&&!auth.classList.contains('hidden')){
      const status=document.getElementById('syncStatus');
      const time=document.getElementById('syncTime');
      if(status)status.textContent='Aguardando login';
      if(time)time.textContent='—';
    }
  });
})();