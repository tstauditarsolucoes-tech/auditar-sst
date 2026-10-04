(()=>{
  'use strict';
  const LOGO='brand-logo-v300.svg';
  const ICON='brand-icon-v300.svg';
  const $=(s,r=document)=>r.querySelector(s);

  function style(){
    if($('#brandV300Style'))return;
    const s=document.createElement('style');s.id='brandV300Style';s.textContent=`
      .epi-auth-overlay{background:
        radial-gradient(circle at 10% 10%,rgba(20,201,144,.16),transparent 32%),
        radial-gradient(circle at 90% 90%,rgba(8,118,102,.12),transparent 34%),
        linear-gradient(145deg,#f7fbfa,#eaf5f2)!important}
      .epi-auth-card{width:min(470px,100%)!important;border-radius:28px!important;padding:26px!important;
        border:1px solid rgba(10,122,100,.12)!important;box-shadow:0 28px 80px rgba(7,54,49,.18)!important}
      .brand-v300-login-logo{display:block;width:min(320px,94%);height:auto;margin:0 auto 12px}
      .epi-auth-card .epi-auth-mark{display:none!important}
      .epi-auth-card h1{font-size:22px!important;text-align:center!important;margin:2px 0 5px!important;color:#15313c!important}
      .epi-auth-card>p{display:none!important}
      .brand-v300-message{text-align:center;color:#456762;font-size:13px;line-height:1.45;margin:0 auto 13px;max-width:360px}
      .brand-v300-benefits{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin:0 0 16px}
      .brand-v300-benefit{background:#eef8f5;border:1px solid #d8ece7;border-radius:13px;padding:9px 5px;text-align:center;color:#25504a}
      .brand-v300-benefit b{display:block;font-size:12px}.brand-v300-benefit small{font-size:9px;color:#66827d}
      .epi-auth-card label{margin:9px 0!important}.epi-auth-card input{min-height:52px!important;border-radius:14px!important;background:#fbfdfc!important}
      .epi-auth-card button{min-height:54px!important;border-radius:14px!important;background:linear-gradient(135deg,#08a77d,#06705e)!important;
        box-shadow:0 10px 26px rgba(8,130,101,.2)!important}
      .brand-v300-secure{text-align:center;color:#718682;font-size:10px;margin-top:5px}
      .topbar>div:first-child::before{background-image:url('${ICON}')!important;background-size:contain!important;background-color:transparent!important;box-shadow:none!important}
      @media(max-width:420px){.epi-auth-overlay{padding:12px!important}.epi-auth-card{padding:20px!important}.brand-v300-benefits{gap:5px}.brand-v300-benefit{padding:8px 3px}.brand-v300-login-logo{width:min(270px,90%)}}
    `;document.head.appendChild(s);
  }

  function decorate(){
    style();
    const card=$('.epi-auth-card');
    if(card && !card.querySelector('.brand-v300-login-logo')){
      const img=document.createElement('img');img.src=LOGO;img.alt='Gestão EPI Auditar';img.className='brand-v300-login-logo';
      card.prepend(img);
      const h=card.querySelector('h1');if(h)h.textContent='Bem-vindo ao Gestão EPI';
      const msg=document.createElement('div');msg.className='brand-v300-message';msg.textContent='Controle de EPIs com mais agilidade, rastreabilidade e segurança.';
      h?.insertAdjacentElement('afterend',msg);
      const benefits=document.createElement('div');benefits.className='brand-v300-benefits';
      benefits.innerHTML='<div class="brand-v300-benefit"><b>⚡ Ágil</b><small>menos etapas</small></div><div class="brand-v300-benefit"><b>📋 Rastreável</b><small>histórico completo</small></div><div class="brand-v300-benefit"><b>✓ Seguro</b><small>evidências protegidas</small></div>';
      msg.insertAdjacentElement('afterend',benefits);
      const err=card.querySelector('.epi-auth-error');
      if(err && !card.querySelector('.brand-v300-secure')){
        const foot=document.createElement('div');foot.className='brand-v300-secure';foot.textContent='🔒 Acesso protegido • Gestão EPI Auditar';
        err.insertAdjacentElement('afterend',foot);
      }
    }
  }

  function boot(){
    decorate();
    const o=new MutationObserver(decorate);o.observe(document.body,{childList:true,subtree:true});
    [100,350,900,1800].forEach(ms=>setTimeout(decorate,ms));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();