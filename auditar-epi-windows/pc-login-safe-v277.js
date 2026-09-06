(()=>{
  const $=(s,r=document)=>r.querySelector(s);

  function addCss(){
    if($('#v277LoginSafeCss'))return;
    const s=document.createElement('style');
    s.id='v277LoginSafeCss';
    s.textContent=`
      .gestao-auth-overlay{
        z-index:2147483000!important;
        pointer-events:auto!important;
      }
      .gestao-auth-overlay.hidden{display:none!important}
      .gestao-auth-overlay:not(.hidden){display:flex!important;opacity:1!important;visibility:visible!important}
      .gestao-auth-overlay:not(.hidden),
      .gestao-auth-overlay:not(.hidden) .gestao-auth-card,
      .gestao-auth-overlay:not(.hidden) .gestao-auth-card *{
        pointer-events:auto!important;
      }
      body:has(.gestao-auth-overlay:not(.hidden)) #connectOverlay{
        display:none!important;
        pointer-events:none!important;
      }
      body:has(.gestao-auth-overlay:not(.hidden)) .layout{
        pointer-events:none!important;
      }
      body:has(.gestao-auth-overlay:not(.hidden)) .gestao-auth-overlay,
      body:has(.gestao-auth-overlay:not(.hidden)) .gestao-auth-overlay *{
        pointer-events:auto!important;
      }
      .gestao-auth-overlay input,
      .gestao-auth-overlay select,
      .gestao-auth-overlay button{
        position:relative;
        z-index:2;
        user-select:auto!important;
      }
    `;
    document.head.appendChild(s);
  }

  function normalize(){
    const overlay=$('#gestaoAuthOverlay');
    if(!overlay||overlay.classList.contains('hidden'))return;
    $('#connectOverlay')?.classList.add('hidden');
    overlay.querySelectorAll('input').forEach(el=>el.removeAttribute('readonly'));
  }

  function boot(){
    addCss();
    [0,150,500,1200,2500].forEach(ms=>setTimeout(normalize,ms));
    window.addEventListener('focus',normalize);
  }

  addCss();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
