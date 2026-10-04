(()=>{
  'use strict';
  const LOGO='brand-logo-v300.svg';
  const $=(s,r=document)=>r.querySelector(s);
  function style(){
    if($('#pcBrandV300Style'))return;
    const s=document.createElement('style');s.id='pcBrandV300Style';s.textContent=`
      .gestao-auth-overlay{background:
        radial-gradient(circle at 8% 8%,rgba(20,201,144,.13),transparent 33%),
        radial-gradient(circle at 92% 90%,rgba(9,112,91,.11),transparent 35%),
        linear-gradient(145deg,#f7fbfa,#e9f4f1)!important}
      .gestao-auth-card{width:min(500px,100%)!important;border-radius:28px!important;padding:28px!important;border:1px solid rgba(8,118,94,.12)!important;box-shadow:0 30px 90px rgba(7,48,44,.18)!important}
      .pc-v300-login-logo{display:block;width:min(345px,92%);height:auto;margin:0 auto 12px}
      .gestao-auth-card .gestao-auth-mark,.gestao-auth-card .v279-login-logo{display:none!important}
      .gestao-auth-card h1{text-align:center!important;color:#15313c!important;font-size:24px!important;margin:2px 0 5px!important}
      .gestao-auth-card>p{display:none!important}
      .pc-v300-message{text-align:center;color:#456762;font-size:13px;line-height:1.5;margin:0 auto 14px;max-width:380px}
      .pc-v300-benefits{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:0 0 16px}
      .pc-v300-benefit{background:#eef8f5;border:1px solid #d8ece7;border-radius:13px;padding:10px 6px;text-align:center;color:#25504a}
      .pc-v300-benefit b{display:block;font-size:12px}.pc-v300-benefit small{font-size:9px;color:#66827d}
      .gestao-auth-card input{min-height:52px!important;border-radius:14px!important;background:#fbfdfc!important}
      .gestao-auth-card>button{min-height:54px!important;background:linear-gradient(135deg,#08a77d,#06705e)!important;border-radius:14px!important;box-shadow:0 10px 26px rgba(8,130,101,.2)!important}
      .pc-v300-secure{text-align:center;color:#718682;font-size:10px;margin-top:4px}
      .sidebar-brand .pc-v300-sidebar-logo{display:block;width:182px;max-width:92%;height:auto;margin:0 auto}
    `;document.head.appendChild(s);
  }
  function image(cls){const i=document.createElement('img');i.src=LOGO;i.alt='Gestão EPI Auditar';i.className=cls;return i;}
  function decorate(){
    style();
    const card=$('.gestao-auth-card');
    if(card && !card.querySelector('.pc-v300-login-logo')){
      card.prepend(image('pc-v300-login-logo'));
      const h=card.querySelector('h1');if(h)h.textContent='Bem-vindo ao Gestão EPI';
      const msg=document.createElement('div');msg.className='pc-v300-message';msg.textContent='Controle de EPIs com mais agilidade, rastreabilidade e segurança.';
      h?.insertAdjacentElement('afterend',msg);
      const benefits=document.createElement('div');benefits.className='pc-v300-benefits';benefits.innerHTML='<div class="pc-v300-benefit"><b>⚡ Ágil</b><small>operação simplificada</small></div><div class="pc-v300-benefit"><b>📋 Rastreável</b><small>histórico e evidências</small></div><div class="pc-v300-benefit"><b>✓ Seguro</b><small>controle protegido</small></div>';
      msg.insertAdjacentElement('afterend',benefits);
      const err=card.querySelector('.gestao-auth-error');if(err){const f=document.createElement('div');f.className='pc-v300-secure';f.textContent='🔒 Acesso protegido • Gestão EPI Auditar';err.insertAdjacentElement('afterend',f);}
    }
    const sb=$('.sidebar-brand');
    if(sb && !sb.querySelector('.pc-v300-sidebar-logo')){sb.replaceChildren(image('pc-v300-sidebar-logo'));}
    const connect=$('#connectOverlay .connect-card .logo,#connectOverlay .connect-card img');
    if(connect && !connect.classList.contains('pc-v300-connect-logo')){const i=image('pc-v300-connect-logo');connect.replaceWith(i);}
  }
  function boot(){decorate();const o=new MutationObserver(decorate);o.observe(document.body,{childList:true,subtree:true});[100,400,1000,2200].forEach(ms=>setTimeout(decorate,ms));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();