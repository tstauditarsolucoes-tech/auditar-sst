(()=>{
  const TOKEN_KEY='gestaoEpiAuthToken';
  const $=(s,r=document)=>r.querySelector(s);
  let forced=false;

  function addCss(){
    if($('#v276LoginGateCss'))return;
    const s=document.createElement('style');
    s.id='v276LoginGateCss';
    s.textContent=`
      html.v276-auth-gate .layout{visibility:hidden!important;pointer-events:none!important}
      html.v276-auth-gate #connectOverlay{display:none!important}
      html.v276-auth-gate .gestao-auth-overlay{visibility:visible!important;pointer-events:auto!important}
    `;
    document.head.appendChild(s);
  }

  function gate(){document.documentElement.classList.add('v276-auth-gate')}
  function release(){document.documentElement.classList.remove('v276-auth-gate')}

  function ensure(){
    const auth=window.GestaoEpiAuth;
    const user=auth?.user?.();
    const token=String(localStorage.getItem(TOKEN_KEY)||'').trim();
    const overlay=$('#gestaoAuthOverlay');

    $('#connectOverlay')?.classList.add('hidden');

    if(user){
      release();
      return true;
    }

    gate();

    // Em uma abertura nova não existe token: o login precisa aparecer obrigatoriamente.
    if(!token && auth && !forced){
      forced=true;
      try{auth.logout(true,'');}catch(_){ }
    }

    if(overlay){
      overlay.classList.remove('hidden');
      overlay.style.pointerEvents='auto';
      overlay.style.visibility='visible';
      const card=overlay.querySelector('.gestao-auth-card');
      if(card)card.style.pointerEvents='auto';
      overlay.querySelectorAll('input,select,button').forEach(el=>el.style.pointerEvents='auto');
      return false;
    }
    return false;
  }

  function boot(){
    addCss();gate();
    let tries=0;
    const timer=setInterval(()=>{
      tries++;
      if(ensure()){clearInterval(timer);return;}
      // Se a autenticação não tiver criado a tela em até 5 s, não libera o painel desconectado.
      if(tries>100){
        clearInterval(timer);
        const auth=window.GestaoEpiAuth;
        if(auth&&!auth.user?.()){
          try{auth.logout(true,'Informe o código da empresa, usuário e senha.');}catch(_){ }
        }
      }
    },50);
    window.addEventListener('focus',ensure);
  }

  addCss();gate();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
