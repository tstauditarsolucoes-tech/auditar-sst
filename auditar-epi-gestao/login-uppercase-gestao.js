(() => {
  const STYLE_ID='gestaoEpiLoginUppercaseStyle';

  function apply(){
    if(!document.getElementById(STYLE_ID)){
      const style=document.createElement('style');
      style.id=STYLE_ID;
      style.textContent=`
        #gestaoAuthOverlay .gestao-auth-card h1,
        #gestaoAuthOverlay .gestao-auth-card > p,
        #gestaoAuthOverlay .gestao-auth-card label,
        #gestaoAuthOverlay #gestaoAuthSubmit{
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

    if(h1)h1.textContent='ENTRAR NO GESTÃO EPI';
    if(p)p.textContent='ACESSO EXCLUSIVO DA EMPRESA LICENCIADA.';
    if(labels[0])labels[0].childNodes[0].nodeValue='CÓDIGO DA EMPRESA';
    if(labels[1])labels[1].childNodes[0].nodeValue='USUÁRIO';
    if(labels[2])labels[2].childNodes[0].nodeValue='SENHA';
    if(btn&&!btn.disabled)btn.textContent='ENTRAR';
    if(tenant)tenant.placeholder='EX.: EMPRESA-X';
    if(user)user.placeholder='SEU USUÁRIO';
    if(pass)pass.placeholder='SUA SENHA';
  }

  function init(){
    apply();
    const obs=new MutationObserver(()=>apply());
    obs.observe(document.documentElement,{childList:true,subtree:true});
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
