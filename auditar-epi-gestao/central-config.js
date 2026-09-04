(() => {
  const OLD_KEY='auditarEpiSyncKey';
  const CENTRAL_KEY='auditarEpiCentralKey';
  const AUTH_TOKEN_KEY='gestaoEpiAuthToken';
  const AUTH_USER_KEY='gestaoEpiAuthUser';
  const AUTH_TENANT_KEY='gestaoEpiAuthTenant';
  const OLD_ENDPOINT='https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
  const NEW_ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';

  const nativeGet=Storage.prototype.getItem;
  const nativeSet=Storage.prototype.setItem;
  const nativeRemove=Storage.prototype.removeItem;

  // No PC a senha deve ser solicitada a cada nova abertura do programa.
  // Mantemos apenas o código da empresa para facilitar o preenchimento.
  try{
    nativeRemove.call(localStorage,AUTH_TOKEN_KEY);
    nativeRemove.call(localStorage,AUTH_USER_KEY);
    nativeRemove.call(localStorage,AUTH_TENANT_KEY);
  }catch(_){}

  Storage.prototype.getItem=function(key){
    if(key===OLD_KEY||key===CENTRAL_KEY){
      // O painel antigo só enxerga uma "chave" depois que o login comercial
      // criou uma sessão válida. Isso evita a sync antes do login.
      return nativeGet.call(this,AUTH_TOKEN_KEY)?'commercial-session':'';
    }
    return nativeGet.call(this,key);
  };
  Storage.prototype.setItem=function(key,value){
    if(key===OLD_KEY||key===CENTRAL_KEY)return;
    return nativeSet.call(this,key,value);
  };
  Storage.prototype.removeItem=function(key){
    if(key===OLD_KEY||key===CENTRAL_KEY)return;
    return nativeRemove.call(this,key);
  };

  const nativeFetch=window.fetch.bind(window);
  window.fetch=function(input,init){if(typeof input==='string'&&input===OLD_ENDPOINT)input=NEW_ENDPOINT;return nativeFetch(input,init);};

  function sanitizeText(root=document.body){
    if(!root)return;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    let node;
    while((node=walker.nextNode())){
      const old=node.nodeValue||'';
      const next=old.replace(/AUDITAR\s+EPI/gi,'GESTÃO EPI').replace(/Auditar\s+EPI/gi,'Gestão EPI');
      if(next!==old)node.nodeValue=next;
    }
  }

  function applyNeutralBrand(){
    document.title='Gestão EPI • Gestão';
    document.querySelectorAll('.logo').forEach(el=>el.innerHTML='GESTÃO <span>EPI</span>');
    const sidebar=document.querySelector('.sidebar-brand small');if(sidebar)sidebar.textContent='GESTÃO';
    sanitizeText();
  }

  document.addEventListener('DOMContentLoaded',()=>{
    const overlay=document.getElementById('connectOverlay');if(overlay)overlay.classList.add('hidden');
    applyNeutralBrand();
    const obs=new MutationObserver(()=>sanitizeText());
    obs.observe(document.body,{childList:true,subtree:true,characterData:true});
    setTimeout(applyNeutralBrand,300);
  });

  function loadScript(src,attr){if(document.querySelector(`script[data-${attr}]`))return;const script=document.createElement('script');script.src=src;script.async=false;script.setAttribute(`data-${attr}`,'1');document.head.appendChild(script);}
  loadScript('auth-gestao.js','auth-gestao');
  loadScript('epi-tools.js','epi-tools');
  loadScript('epi-photo-ca-gestao.js','epi-photo-ca-gestao');
  loadScript('company-branding-gestao.js','company-branding-gestao');
  loadScript('worker-link-pc-fix.js','worker-link-pc-fix');
  loadScript('https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js','xlsx-lib');
  loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js','pdfjs-lib');
  loadScript('https://cdn.jsdelivr.net/npm/@vladmandic/human@3.3.6/dist/human.js','human-lib');
  loadScript('pc-stability.js','pc-stability');
  loadScript('campo-pc.js','campo-pc');
  loadScript('ai-import-pc.js','ai-import-pc');
})();