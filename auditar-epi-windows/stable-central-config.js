(() => {
  const OLD_KEY='auditarEpiSyncKey';
  const CENTRAL_KEY='auditarEpiCentralKey';
  const AUTH_TOKEN_KEY='gestaoEpiAuthToken';
  const OLD_ENDPOINT='https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
  const NEW_ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';

  const nativeGet=Storage.prototype.getItem;
  const nativeSet=Storage.prototype.setItem;
  const nativeRemove=Storage.prototype.removeItem;

  Storage.prototype.getItem=function(key){
    if(key===OLD_KEY||key===CENTRAL_KEY){
      // A chave de compatibilidade só existe depois que o login comercial criou
      // um authToken. Assim o app não tenta sincronizar antes da autenticação.
      const token=String(nativeGet.call(this,AUTH_TOKEN_KEY)||'').trim();
      return token?'commercial-session':'';
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
  window.fetch=function(input,init){
    if(typeof input==='string'&&input===OLD_ENDPOINT)input=NEW_ENDPOINT;
    return nativeFetch(input,init);
  };

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
    const sidebar=document.querySelector('.sidebar-brand small');
    if(sidebar)sidebar.textContent='GESTÃO';
    sanitizeText();
  }

  document.addEventListener('DOMContentLoaded',()=>{
    const overlay=document.getElementById('connectOverlay');
    if(overlay)overlay.classList.add('hidden');
    applyNeutralBrand();
    const obs=new MutationObserver(()=>sanitizeText());
    obs.observe(document.body,{childList:true,subtree:true,characterData:true});
    setTimeout(applyNeutralBrand,300);
  });

  function loadScript(src,attr){
    if(document.querySelector(`script[data-${attr}]`))return;
    const script=document.createElement('script');
    script.src=src;
    script.async=false;
    script.setAttribute(`data-${attr}`,'1');
    document.head.appendChild(script);
  }

  // Mesma ordem da versão PC comprovadamente funcional enviada pelo usuário.
  loadScript('auth-gestao.js','auth-gestao');
  loadScript('epi-tools.js','epi-tools');
  loadScript('company-branding-gestao.js','company-branding-gestao');
})();
