(() => {
  const TOKEN_KEY='gestaoEpiAuthToken';
  const USER_KEY='gestaoEpiAuthUser';
  const TENANT_KEY='gestaoEpiAuthTenant';
  const TENANT_CODE_KEY='gestaoEpiTenantCode';
  const WINDOW_SESSION='gestaoEpiPcWindowSessionV221';

  // Na primeira carga de uma nova janela do Windows, encerra a sessão anterior.
  // Em recargas internas do app (usadas após salvar/importar), sessionStorage
  // permanece e evita pedir login novamente.
  if(!sessionStorage.getItem(WINDOW_SESSION)){
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TENANT_KEY);
    localStorage.removeItem(TENANT_CODE_KEY);
    sessionStorage.setItem(WINDOW_SESSION,'1');
  }else{
    // O código da empresa nunca deve ficar preenchido automaticamente.
    localStorage.removeItem(TENANT_CODE_KEY);
  }

  document.addEventListener('DOMContentLoaded',()=>{
    const tenant=document.getElementById('gestaoTenantCode');
    if(tenant)tenant.value='';
  });
})();
