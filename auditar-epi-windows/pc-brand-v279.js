(()=>{
  const BRAND='brand-logo-v279.svg';

  function ensureStyle(){
    if(document.getElementById('v279BrandStyle')) return;
    const s=document.createElement('style');
    s.id='v279BrandStyle';
    s.textContent=`
      .v279-brand-full{display:block;width:100%;max-width:176px;height:auto;object-fit:contain}
      .sidebar-brand{padding-top:22px!important;padding-bottom:18px!important}
      .sidebar-brand .v279-brand-full{max-width:174px;margin:0 auto}
      .gestao-auth-card .v279-login-logo{display:block;width:min(285px,86%);height:auto;margin:0 auto 16px;object-fit:contain}
      #connectOverlay .connect-card .v279-connect-logo{display:block;width:min(280px,88%);height:auto;margin:0 auto 16px;object-fit:contain}
      @media(max-width:720px){.sidebar-brand .v279-brand-full{max-width:150px}}
    `;
    document.head.appendChild(s);
  }

  function image(cls,alt='Gestão EPI'){
    const img=document.createElement('img');
    img.src=BRAND;
    img.alt=alt;
    img.className=cls;
    return img;
  }

  function applySidebar(){
    const brand=document.querySelector('.sidebar-brand');
    if(!brand || brand.dataset.v279Brand==='1') return;
    brand.replaceChildren(image('v279-brand-full'));
    brand.dataset.v279Brand='1';
  }

  function applyLogin(){
    const card=document.querySelector('.gestao-auth-card');
    if(!card || card.querySelector('.v279-login-logo')) return;
    const old=card.querySelector('.gestao-auth-mark');
    if(old) old.replaceWith(image('v279-login-logo'));
    else card.prepend(image('v279-login-logo'));
  }

  function applyConnect(){
    const old=document.querySelector('#connectOverlay .connect-card .logo');
    if(!old || old.dataset.v279Brand==='1') return;
    const img=image('v279-connect-logo');
    img.dataset.v279Brand='1';
    old.replaceWith(img);
  }

  function apply(){
    ensureStyle();
    applySidebar();
    applyLogin();
    applyConnect();
  }

  function boot(){
    apply();
    [150,500,1200,2500].forEach(ms=>setTimeout(apply,ms));
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
