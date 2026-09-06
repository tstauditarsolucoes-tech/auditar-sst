(() => {
  const TOKEN_KEY='gestaoEpiAuthToken';
  const USER_KEY='gestaoEpiAuthUser';
  const TENANT_KEY='gestaoEpiAuthTenant';
  const TENANT_CODE_KEY='gestaoEpiTenantCode';
  const WINDOW_SESSION='gestaoEpiPcWindowSessionV221';

  const hadWindowSession=Boolean(sessionStorage.getItem(WINDOW_SESSION));
  const hadToken=Boolean(String(localStorage.getItem(TOKEN_KEY)||'').trim());
  const resumeInternalReload=hadWindowSession&&hadToken;

  // Na primeira carga de uma nova janela do Windows, encerra a sessão anterior.
  // Em recargas internas do app (usadas após salvar/importar), sessionStorage
  // permanece e evita pedir login novamente.
  if(!hadWindowSession){
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TENANT_KEY);
    localStorage.removeItem(TENANT_CODE_KEY);
    sessionStorage.setItem(WINDOW_SESSION,'1');
  }else{
    // O código da empresa nunca deve ficar preenchido automaticamente.
    localStorage.removeItem(TENANT_CODE_KEY);
  }

  // Em uma recarga interna já autenticada, o auth-gestao valida a sessão de novo.
  // Antes desta correção, o overlay de login aparecia por alguns instantes durante
  // essa validação. Mantemos o login oculto somente enquanto a sessão existente é
  // revalidada. Se o token tiver expirado, o login volta a aparecer normalmente.
  if(resumeInternalReload){
    const style=document.createElement('style');
    style.id='pcAuthResumeStyle';
    style.textContent='html.pc-auth-resume .gestao-auth-overlay{display:none!important}';
    document.head.appendChild(style);
    document.documentElement.classList.add('pc-auth-resume');

    const release=()=>document.documentElement.classList.remove('pc-auth-resume');
    const waitAuth=()=>{
      let tries=0;
      const timer=setInterval(()=>{
        tries++;
        const auth=window.GestaoEpiAuth;
        const user=auth?.user?.();
        const tokenNow=String(localStorage.getItem(TOKEN_KEY)||'').trim();
        if(user||!tokenNow||tries>200){
          clearInterval(timer);
          release();
        }
      },40);
    };
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',waitAuth,{once:true});
    else waitAuth();
  }

  document.addEventListener('DOMContentLoaded',()=>{
    const tenant=document.getElementById('gestaoTenantCode');
    if(tenant)tenant.value='';
  });
})();
