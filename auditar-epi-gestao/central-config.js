(() => {
  const OLD_KEY='auditarEpiSyncKey';
  const CENTRAL_KEY='auditarEpiCentralKey';
  const OLD_ENDPOINT='https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
  const NEW_ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';

  const nativeGet=Storage.prototype.getItem;
  const nativeSet=Storage.prototype.setItem;
  const nativeRemove=Storage.prototype.removeItem;

  /* O app legado ainda verifica uma chave local antes de sincronizar.
     No modelo comercial, a autorização real é o token da sessão da empresa.
     Mantemos apenas um marcador interno para impedir a antiga tela de chave. */
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

  function hideLegacyConnect(){
    const overlay=document.getElementById('connectOverlay');
    if(!overlay)return;
    overlay.classList.add('hidden');
    overlay.style.display='none';
    overlay.setAttribute('aria-hidden','true');
  }

  function applyNeutralBrand(){
    document.title='Gestão EPI • Gestão';
    document.querySelectorAll('.logo').forEach(el=>el.innerHTML='GESTÃO <span>EPI</span>');
    const sidebar=document.querySelector('.sidebar-brand small');
    if(sidebar)sidebar.textContent='GESTÃO';
    sanitizeText();
  }

  hideLegacyConnect();
  applyNeutralBrand();

  document.addEventListener('DOMContentLoaded',()=>{
    hideLegacyConnect();
    applyNeutralBrand();
    const obs=new MutationObserver(()=>sanitizeText());
    obs.observe(document.body,{childList:true,subtree:true,characterData:true});
    setTimeout(applyNeutralBrand,300);
  });
})();
