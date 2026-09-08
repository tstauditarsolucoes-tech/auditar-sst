(()=>{
  const CURRENT='2.7.7';
  const RELEASE_API='https://api.github.com/repos/tstauditarsolucoes-tech/auditar-sst/releases/latest';
  const TENANT_CODE_KEY='gestaoEpiTenantCode';
  const TENANT_CODE_BACKUP_KEY='gestaoEpiTenantCodeV277Backup';
  const nativeFetch=window.fetch.bind(window);
  let pendingTenantCode='';

  window.fetch=async function(input,init){
    const url=typeof input==='string'?input:String(input?.url||'');
    const res=await nativeFetch(input,init);
    if(url!==RELEASE_API)return res;
    try{
      const data=await res.clone().json();
      const tag=String(data?.tag_name||'');
      if(tag==='gestao-epi-v'+CURRENT||tag==='v'+CURRENT||tag===CURRENT){
        data.tag_name='gestao-epi-v2.7.0';
        return new Response(JSON.stringify(data),{status:res.status,statusText:res.statusText,headers:{'Content-Type':'application/json'}});
      }
    }catch(_){ }
    return res;
  };

  function fixText(){
    const el=document.getElementById('v270UpdateText');
    if(!el)return;
    const next=String(el.textContent||'').replace(/Versão atual: 2\.7\.\d+/g,'Versão atual: 2.7.7');
    if(el.textContent!==next)el.textContent=next;
  }

  function positionBatch(){
    const nav=document.querySelector('.sidebar nav');
    const batch=nav?.querySelector('.nav[data-view="batchDeliveryPc"]');
    const normal=nav?.querySelector('.nav[data-view="newDeliveryPc"]');
    if(batch&&normal&&batch.nextElementSibling!==normal)nav.insertBefore(batch,normal);
  }

  function cleanFaceText(){
    const p=document.querySelector('#pcFaceOverlay .pc-face-head p');
    if(p&&!document.getElementById('v274FaceName')&&p.textContent!=='Olhe normalmente para a câmera.'){
      p.textContent='Olhe normalmente para a câmera.';
    }
  }

  function fixDialogCancelAndClose(){
    if(document.documentElement.dataset.v277DialogCloseFix==='1')return;
    document.documentElement.dataset.v277DialogCloseFix='1';

    document.addEventListener('click',event=>{
      const button=event.target.closest('button[value="cancel"],button.x');
      if(!button)return;
      const dialog=button.closest('dialog');
      if(!dialog)return;

      event.preventDefault();
      event.stopPropagation();

      try{
        if(dialog.open)dialog.close('cancel');
      }catch(_){
        dialog.removeAttribute('open');
      }
    },true);
  }

  function storedTenantCode(){
    return String(localStorage.getItem(TENANT_CODE_KEY)||localStorage.getItem(TENANT_CODE_BACKUP_KEY)||'').trim();
  }

  function rememberTenantCode(){
    const typed=String(document.getElementById('gestaoTenantCode')?.value||'').trim();
    const code=typed||pendingTenantCode||storedTenantCode();
    if(!code)return;
    pendingTenantCode=code;
    localStorage.setItem(TENANT_CODE_BACKUP_KEY,code);
    localStorage.setItem(TENANT_CODE_KEY,code);
  }

  function simplifyLogin(){
    const codeInput=document.getElementById('gestaoTenantCode');
    if(!codeInput)return;

    const codeLabel=codeInput.closest('label');
    const storedCode=storedTenantCode();
    const card=document.querySelector('#gestaoAuthOverlay .gestao-auth-card');
    const subtitle=card?.querySelector(':scope > p');

    if(storedCode){
      localStorage.setItem(TENANT_CODE_KEY,storedCode);
      codeInput.value=storedCode;
      if(codeLabel)codeLabel.style.display='none';
      if(subtitle)subtitle.textContent='Digite seu usuário e senha.';
    }else{
      if(codeLabel)codeLabel.style.display='';
      if(subtitle)subtitle.textContent='Primeiro acesso: informe o código da empresa uma única vez.';
    }
  }

  function watchSimpleLogin(){
    const overlay=document.getElementById('gestaoAuthOverlay');
    if(!overlay)return;

    simplifyLogin();
    if(overlay.dataset.v277SimpleLogin==='1')return;
    overlay.dataset.v277SimpleLogin='1';

    overlay.addEventListener('click',event=>{
      if(event.target.closest('#gestaoAuthSubmit'))rememberTenantCode();
    },true);
    overlay.addEventListener('keydown',event=>{
      if(event.key==='Enter'&&event.target.closest('#gestaoAuthPass'))rememberTenantCode();
    },true);

    const observer=new MutationObserver(()=>{
      if(overlay.classList.contains('hidden'))rememberTenantCode();
      simplifyLogin();
    });
    observer.observe(overlay,{attributes:true,attributeFilter:['class']});
  }

  function refreshUi(){
    fixText();
    cleanFaceText();
    positionBatch();
    fixDialogCancelAndClose();
    watchSimpleLogin();
  }

  function boot(){
    fixDialogCancelAndClose();
    watchSimpleLogin();
    [0,300,1000,2500,5000,9000].forEach(ms=>setTimeout(refreshUi,ms));
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
