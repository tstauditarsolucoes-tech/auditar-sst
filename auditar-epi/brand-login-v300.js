(()=>{
  'use strict';
  const LOGO='brand-logo-v300.svg';
  const ICON='brand-icon-v300.svg';
  const $=(s,r=document)=>r.querySelector(s);

  function style(){
    if($('#brandV302Style'))return;
    const s=document.createElement('style');
    s.id='brandV302Style';
    s.textContent=`
      .epi-auth-overlay{
        overflow:auto!important;
        align-items:flex-start!important;
        padding:max(20px,env(safe-area-inset-top)) 14px max(20px,env(safe-area-inset-bottom))!important;
        background:
          radial-gradient(circle at 0 0,rgba(27,205,154,.20),transparent 31%),
          radial-gradient(circle at 100% 100%,rgba(8,95,88,.15),transparent 36%),
          linear-gradient(155deg,#f8fcfb 0%,#edf7f4 54%,#e6f3f0 100%)!important;
      }
      .epi-auth-overlay:before{
        content:'';
        position:fixed;left:-70px;top:-95px;width:240px;height:240px;border-radius:50%;
        border:46px solid rgba(14,164,126,.055);pointer-events:none
      }
      .epi-auth-overlay:after{
        content:'';
        position:fixed;right:-85px;bottom:-105px;width:260px;height:260px;border-radius:50%;
        border:52px solid rgba(6,87,84,.045);pointer-events:none
      }
      .epi-auth-card{
        position:relative;z-index:1;
        width:min(470px,100%)!important;
        margin:auto!important;
        border-radius:30px!important;
        padding:22px 22px 18px!important;
        border:1px solid rgba(18,116,96,.11)!important;
        background:rgba(255,255,255,.985)!important;
        box-shadow:0 28px 80px rgba(8,58,51,.16),0 4px 18px rgba(8,58,51,.06)!important
      }
      .brand-v300-login-logo{display:none!important}
      .epi-auth-card .epi-auth-mark{display:none!important}
      .brand-v302-top{
        display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px
      }
      .brand-v302-badge{
        display:inline-flex;align-items:center;gap:7px;padding:7px 10px;border-radius:999px;
        background:#ecf8f4;color:#0c705e;border:1px solid #d8ece6;
        font-size:9px;font-weight:900;letter-spacing:.07em;text-transform:uppercase
      }
      .brand-v302-status{
        display:inline-flex;align-items:center;gap:6px;color:#66827d;font-size:9px;font-weight:800;
        white-space:nowrap
      }
      .brand-v302-status i{width:7px;height:7px;border-radius:50%;background:#12a77c;box-shadow:0 0 0 4px rgba(18,167,124,.10)}
      .brand-v302-status.off i{background:#d97706;box-shadow:0 0 0 4px rgba(217,119,6,.10)}
      .brand-v302-logo{
        display:block;width:min(252px,78%);height:auto;margin:2px auto 7px
      }
      .epi-auth-card h1{
        font-size:27px!important;line-height:1.12!important;text-align:center!important;
        margin:5px auto 6px!important;color:#12353b!important;letter-spacing:-.035em!important;
        max-width:360px
      }
      .epi-auth-card>p{display:none!important}
      .brand-v302-message{
        text-align:center;color:#58726e;font-size:12.5px;line-height:1.5;
        margin:0 auto 14px;max-width:355px
      }
      .brand-v300-message,.brand-v300-benefits,.brand-v300-secure{display:none!important}
      .brand-v302-features{
        display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:0 0 16px
      }
      .brand-v302-feature{
        min-width:0;background:linear-gradient(180deg,#f5fbf9,#eef8f5);
        border:1px solid #dcece8;border-radius:13px;padding:9px 4px 8px;text-align:center;color:#26554e
      }
      .brand-v302-feature span{display:block;font-size:17px;line-height:1;margin-bottom:5px}
      .brand-v302-feature b{display:block;font-size:9px;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .brand-v302-form-title{
        display:flex;align-items:center;gap:8px;margin:1px 0 2px;color:#244e48;
        font-size:11px;font-weight:950;text-transform:uppercase;letter-spacing:.07em
      }
      .brand-v302-form-title:after{content:'';height:1px;background:#e1ece9;flex:1}
      .epi-auth-card label{
        position:relative;margin:10px 0!important;color:#365c57!important;font-size:10.5px!important;
        letter-spacing:.035em!important;text-transform:uppercase!important
      }
      .epi-auth-card input{
        min-height:53px!important;border-radius:15px!important;background:#fbfdfc!important;
        border:1px solid #cfdfdb!important;padding:0 14px!important;font-size:15px!important;
        color:#173d39!important;box-shadow:none!important;transition:border-color .16s,box-shadow .16s,background .16s
      }
      .epi-auth-card input:focus{
        background:#fff!important;border-color:#12a77c!important;
        box-shadow:0 0 0 4px rgba(18,167,124,.10)!important
      }
      .epi-auth-card input::placeholder{color:#8a9c99!important;font-weight:600!important}
      #epiAuthSubmit{
        min-height:56px!important;border-radius:15px!important;margin-top:13px!important;
        background:linear-gradient(135deg,#10ac80 0%,#07856b 54%,#056353 100%)!important;
        box-shadow:0 13px 28px rgba(7,123,98,.22)!important;font-size:15px!important;
        letter-spacing:.015em!important
      }
      #epiAuthSubmit:active{transform:translateY(1px)}
      #epiAuthSubmit:disabled{opacity:.72!important}
      .epi-auth-error{
        min-height:17px!important;margin-top:8px!important;text-align:center!important;
        font-size:10.5px!important
      }
      .brand-v302-footer{
        border-top:1px solid #e6efed;margin-top:5px;padding-top:11px;text-align:center
      }
      .brand-v302-footer b{display:block;color:#385d58;font-size:10px}
      .brand-v302-footer small{display:block;color:#829491;font-size:8.5px;margin-top:3px;line-height:1.35}
      .topbar>div:first-child::before{
        background-image:url('${ICON}')!important;background-size:contain!important;
        background-color:transparent!important;box-shadow:none!important
      }
      @media(max-width:420px){
        .epi-auth-overlay{padding-left:10px!important;padding-right:10px!important}
        .epi-auth-card{padding:18px 17px 15px!important;border-radius:27px!important}
        .brand-v302-logo{width:min(230px,76%)}
        .epi-auth-card h1{font-size:24px!important}
        .brand-v302-message{font-size:12px;margin-bottom:12px}
        .brand-v302-features{gap:5px;margin-bottom:13px}
        .brand-v302-feature{padding:8px 2px 7px}
        .brand-v302-feature span{font-size:16px}.brand-v302-feature b{font-size:8px}
        .epi-auth-card label{margin:8px 0!important}
        .epi-auth-card input{min-height:50px!important}
        #epiAuthSubmit{min-height:53px!important}
      }
      @media(max-height:720px){
        .epi-auth-card{padding-top:15px!important;padding-bottom:13px!important}
        .brand-v302-logo{width:min(205px,65%);margin-bottom:2px}
        .epi-auth-card h1{font-size:22px!important;margin-top:2px!important}
        .brand-v302-message{margin-bottom:9px}
        .brand-v302-features{margin-bottom:9px}
        .brand-v302-feature{padding:6px 2px}
        .epi-auth-card label{margin:6px 0!important}
        .epi-auth-card input{min-height:47px!important}
        #epiAuthSubmit{min-height:50px!important;margin-top:9px!important}
        .brand-v302-footer{padding-top:8px}
      }
    `;
    document.head.appendChild(s);
  }

  function onlineState(){
    const el=$('.brand-v302-status');
    if(!el)return;
    const on=navigator.onLine;
    el.classList.toggle('off',!on);
    el.innerHTML='<i></i>'+(on?'Online':'Offline');
  }

  function decorate(){
    style();
    const card=$('.epi-auth-card');
    if(!card || card.dataset.brandV302==='1')return;
    card.dataset.brandV302='1';

    card.querySelectorAll('.brand-v300-login-logo,.brand-v300-message,.brand-v300-benefits,.brand-v300-secure').forEach(e=>e.remove());

    const top=document.createElement('div');
    top.className='brand-v302-top';
    top.innerHTML='<div class="brand-v302-badge">🛡️ Segurança & EPI</div><div class="brand-v302-status"><i></i>Online</div>';
    card.prepend(top);

    const logo=document.createElement('img');
    logo.src=LOGO;logo.alt='Gestão EPI Auditar';logo.className='brand-v302-logo';
    top.insertAdjacentElement('afterend',logo);

    const h=card.querySelector('h1');
    if(h)h.textContent='Gestão de EPI simples, segura e rastreável';

    const msg=document.createElement('div');
    msg.className='brand-v302-message';
    msg.textContent='Entregue, acompanhe e comprove EPIs com agilidade — do estoque ao trabalhador.';
    h?.insertAdjacentElement('afterend',msg);

    const features=document.createElement('div');
    features.className='brand-v302-features';
    features.innerHTML=
      '<div class="brand-v302-feature"><span>⚡</span><b>Entrega rápida</b></div>'+
      '<div class="brand-v302-feature"><span>📦</span><b>Estoque</b></div>'+
      '<div class="brand-v302-feature"><span>👤</span><b>Biometria</b></div>'+
      '<div class="brand-v302-feature"><span>📋</span><b>Histórico</b></div>';
    msg.insertAdjacentElement('afterend',features);

    const firstLabel=card.querySelector('label');
    if(firstLabel){
      const title=document.createElement('div');
      title.className='brand-v302-form-title';
      title.textContent='Acesse sua conta';
      firstLabel.insertAdjacentElement('beforebegin',title);
    }

    const err=card.querySelector('.epi-auth-error');
    if(err){
      const footer=document.createElement('div');
      footer.className='brand-v302-footer';
      footer.innerHTML='<b>🔒 Acesso protegido • Gestão EPI Auditar</b><small>Controle operacional de EPI para equipes de campo e gestão.</small>';
      err.insertAdjacentElement('afterend',footer);
    }

    onlineState();
  }

  function boot(){
    style();
    decorate();
    window.addEventListener('online',onlineState);
    window.addEventListener('offline',onlineState);
    [80,250,700,1400].forEach(ms=>setTimeout(decorate,ms));
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();