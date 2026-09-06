(()=>{
  const $=(s,r=document)=>r.querySelector(s);

  function css(){
    if($('#v275LoginInteractionCss'))return;
    const s=document.createElement('style');
    s.id='v275LoginInteractionCss';
    s.textContent=`
      .gestao-auth-overlay{
        z-index:2147483000!important;
        pointer-events:auto!important;
        visibility:visible;
      }
      .gestao-auth-overlay.hidden{display:none!important}
      .gestao-auth-overlay:not(.hidden){display:flex!important;opacity:1!important}
      .gestao-auth-overlay:not(.hidden) .gestao-auth-card,
      .gestao-auth-overlay:not(.hidden) .gestao-auth-card *{
        pointer-events:auto!important;
      }
      .gestao-auth-overlay input,
      .gestao-auth-overlay select,
      .gestao-auth-overlay button{
        position:relative;
        z-index:2;
        user-select:auto!important;
      }
      html.v275-login-open .layout{
        pointer-events:none!important;
      }
      html.v275-login-open #connectOverlay,
      html.v275-login-open .pc-face-overlay,
      html.v275-login-open .v25scan,
      html.v275-login-open .users-modal,
      html.v275-login-open .v270-results{
        display:none!important;
        pointer-events:none!important;
      }
    `;
    document.head.appendChild(s);
  }

  function visible(el){
    if(!el||el.classList.contains('hidden'))return false;
    const st=getComputedStyle(el);
    return st.display!=='none'&&st.visibility!=='hidden';
  }

  function apply(){
    const overlay=$('#gestaoAuthOverlay');
    const open=visible(overlay);
    document.documentElement.classList.toggle('v275-login-open',open);
    if(!open)return;

    // Nenhuma tela auxiliar deve ficar por cima do login.
    $('#connectOverlay')?.classList.add('hidden');
    $('#pcFaceOverlay')?.classList.remove('open');
    $('#v25Scanner')?.classList.remove('open');
    $('#usersModal')?.classList.remove('open');

    // Garante foco e clique nos campos mesmo se outro módulo tiver alterado estilos.
    overlay.style.pointerEvents='auto';
    const card=overlay.querySelector('.gestao-auth-card');
    if(card)card.style.pointerEvents='auto';
    overlay.querySelectorAll('input,select,button').forEach(el=>{
      el.style.pointerEvents='auto';
      if(el.tagName==='INPUT')el.removeAttribute('readonly');
    });
  }

  function boot(){
    css();
    apply();
    if(document.body){
      new MutationObserver(apply).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['class','style']});
    }
    let n=0;
    const t=setInterval(()=>{apply();if(++n>80)clearInterval(t)},100);
    window.addEventListener('focus',apply);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
