(() => {
  const TOKEN_KEY='gestaoEpiAuthToken';
  const USER_KEY='gestaoEpiAuthUser';
  const TENANT_KEY='gestaoEpiAuthTenant';
  const TENANT_CODE_KEY='gestaoEpiTenantCode';

  // No PC, cada abertura começa com autenticação nova.
  // O cache local do tenant continua preservado; somente a sessão é encerrada.
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(TENANT_KEY);
  localStorage.removeItem(TENANT_CODE_KEY);

  // Evita que o adaptador antigo de fetch seja instalado. A v2.0.8 sincroniza
  // diretamente por GestaoEpiAuth.api(), sem chave de sincronização antiga.
  window.__gestaoEpiSyncTransportFix=true;

  const style=document.createElement('style');
  style.id='gestaoEpiPcIndependentScroll';
  style.textContent=`
    @media (min-width:721px){
      html,body{height:100%;overflow:hidden!important}
      .layout{height:100vh!important;min-height:0!important;overflow:hidden!important}
      .sidebar{position:relative!important;top:auto!important;height:100vh!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important}
      .main{height:100vh!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important}
    }
    .gestao-pc-version{font-size:10px;font-weight:800;color:#8fa5a1;line-height:1.2}
    .gestao-pc-version-login{margin-top:8px;text-align:center}
  `;
  document.head.appendChild(style);

  function addVersionLabels(){
    const auth=document.getElementById('gestaoAuthOverlay');
    const card=auth?.querySelector('.gestao-auth-card');
    if(card&&!card.querySelector('.gestao-pc-version-login')){
      const v=document.createElement('div');
      v.className='gestao-pc-version gestao-pc-version-login';
      v.textContent='PC v2.0.8';
      card.appendChild(v);
    }

    const foot=document.querySelector('.sidebar-foot');
    if(foot&&!foot.querySelector('.gestao-pc-version')){
      const v=document.createElement('small');
      v.className='gestao-pc-version';
      v.textContent='PC v2.0.8';
      foot.appendChild(v);
    }
  }

  function enforceCleanLogin(){
    const connect=document.getElementById('connectOverlay');
    if(connect){
      connect.classList.add('hidden');
      connect.style.display='none';
      connect.setAttribute('aria-hidden','true');
    }

    const auth=document.getElementById('gestaoAuthOverlay');
    const tenantCode=document.getElementById('gestaoTenantCode');
    const username=document.getElementById('gestaoAuthUser');
    const password=document.getElementById('gestaoAuthPass');

    if(tenantCode)tenantCode.value='';
    if(username)username.value='';
    if(password)password.value='';
    if(auth)auth.classList.remove('hidden');

    const status=document.getElementById('syncStatus');
    const time=document.getElementById('syncTime');
    if(status)status.textContent='Aguardando login';
    if(time)time.textContent='—';

    addVersionLabels();
  }

  // Se algum erro JavaScript impedir a inicialização, mostra na própria tela em
  // vez de ficar silenciosamente em "Não conectado".
  window.addEventListener('error',event=>{
    const status=document.getElementById('syncStatus');
    if(status)status.textContent='Erro interno do app';
    console.error('Gestão EPI PC:',event.error||event.message);
  });

  window.addEventListener('unhandledrejection',event=>{
    const status=document.getElementById('syncStatus');
    if(status)status.textContent='Erro interno do app';
    console.error('Gestão EPI PC:',event.reason);
  });

  document.addEventListener('DOMContentLoaded',()=>{
    enforceCleanLogin();
    setTimeout(addVersionLabels,0);
  });
})();