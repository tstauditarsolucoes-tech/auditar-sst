(() => {
  const OLD_KEY='auditarEpiSyncKey';
  const CENTRAL_KEY='auditarEpiCentralKey';
  const OLD_ENDPOINT='https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
  const NEW_ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';

  /*
    IMPORTANTE: este arquivo é carregado diretamente pelo index.html antes do app.js.
    A autenticação comercial precisa entrar na página de forma síncrona para o painel
    nunca ficar visível sem Código da empresa + Usuário + Senha.
  */
  if(!document.querySelector('script[data-auth-gestao]')){
    document.write('<script src="auth-gestao.js" data-auth-gestao="1"><\\/script>');
  }
  if(!document.querySelector('script[data-login-uppercase-gestao]')){
    document.write('<script src="login-uppercase-gestao.js" data-login-uppercase-gestao="1"><\\/script>');
  }

  const nativeGet=Storage.prototype.getItem;
  const nativeSet=Storage.prototype.setItem;
  const nativeRemove=Storage.prototype.removeItem;

  Storage.prototype.getItem=function(key){
    if(key===OLD_KEY||key===CENTRAL_KEY)return 'commercial-session';
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
    if(overlay){
      overlay.classList.add('hidden');
      overlay.style.display='none';
      overlay.setAttribute('aria-hidden','true');
    }
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

  loadScript('epi-tools.js','epi-tools');
  loadScript('epi-photo-ca-gestao.js','epi-photo-ca-gestao');
  loadScript('worker-link-gestao.js','worker-link-gestao');
  loadScript('company-branding-gestao.js','company-branding-gestao');
})();