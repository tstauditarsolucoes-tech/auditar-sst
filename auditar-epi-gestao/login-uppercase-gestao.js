(() => {
  const STYLE_ID='gestaoEpiLoginUppercaseStyle';

  function apply(){
    if(!document.getElementById(STYLE_ID)){
      const style=document.createElement('style');
      style.id=STYLE_ID;
      style.textContent=`
        #gestaoAuthOverlay .gestao-auth-card label{
          text-transform:uppercase;
        }
        #gestaoAuthOverlay #gestaoTenantCode,
        #gestaoAuthOverlay #gestaoAuthUser{
          text-transform:uppercase;
        }
        #gestaoAuthOverlay #gestaoAuthPass{
          text-transform:none;
        }
        #gestaoAuthOverlay #gestaoTenantCode::placeholder,
        #gestaoAuthOverlay #gestaoAuthUser::placeholder,
        #gestaoAuthOverlay #gestaoAuthPass::placeholder{
          text-transform:uppercase;
        }
        @media (min-width:721px){
          html,body{height:100%;overflow:hidden!important}
          .layout{height:100vh!important;min-height:0!important;overflow:hidden!important}
          .sidebar{position:relative!important;top:auto!important;height:100vh!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain}
          .main{height:100vh!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain}
        }
      `;
      document.head.appendChild(style);
    }

    const overlay=document.getElementById('gestaoAuthOverlay');
    if(!overlay)return;
    const h1=overlay.querySelector('h1');
    const p=overlay.querySelector('.gestao-auth-card > p');
    const labels=overlay.querySelectorAll('label');
    const btn=document.getElementById('gestaoAuthSubmit');
    const tenant=document.getElementById('gestaoTenantCode');
    const user=document.getElementById('gestaoAuthUser');
    const pass=document.getElementById('gestaoAuthPass');

    if(h1)h1.textContent='Entrar no Gestão EPI';
    if(p)p.textContent='Acesso exclusivo da empresa licenciada.';
    if(labels[0])labels[0].childNodes[0].nodeValue='CÓDIGO DA EMPRESA';
    if(labels[1])labels[1].childNodes[0].nodeValue='USUÁRIO';
    if(labels[2])labels[2].childNodes[0].nodeValue='SENHA';
    if(btn&&!btn.disabled)btn.textContent='Entrar';
    if(tenant)tenant.placeholder='EX.: EMPRESA-X';
    if(user)user.placeholder='SEU USUÁRIO';
    if(pass)pass.placeholder='SUA SENHA';
  }

  function installSyncTransportFix(){
    if(window.__gestaoEpiSyncTransportFix)return;
    const previousFetch=window.fetch.bind(window);

    window.fetch=async function(input,init){
      try{
        if(typeof input==='string'&&init?.body&&window.GestaoEpiAuth?.api){
          const body=JSON.parse(init.body);
          if(body?.action==='epi_sync_merge'){
            const extra={...body};
            delete extra.action;
            delete extra.authToken;
            const json=await window.GestaoEpiAuth.api('epi_sync_merge',extra);
            return new Response(JSON.stringify(json),{
              status:200,
              headers:{'Content-Type':'application/json;charset=utf-8'}
            });
          }
        }
      }catch(error){
        console.error('Falha no transporte autenticado da sincronização:',error);
        throw error;
      }
      return previousFetch(input,init);
    };

    window.__gestaoEpiSyncTransportFix=true;
  }

  function init(){
    apply();
    installSyncTransportFix();
    const obs=new MutationObserver(()=>apply());
    obs.observe(document.documentElement,{childList:true,subtree:true});
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
