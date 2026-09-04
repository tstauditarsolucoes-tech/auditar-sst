(() => {
  const OLD_KEY='auditarEpiSyncKey';
  const CENTRAL_KEY='auditarEpiCentralKey';
  const OLD_ENDPOINT='https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
  const NEW_ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';

  /* Bloqueia o painel imediatamente. Só removemos este bloqueio quando
     auth-gestao.js realmente criar a tela de autenticação comercial. */
  const gate=document.createElement('div');
  gate.id='gestaoCommercialBootGate';
  gate.style.cssText='position:fixed;inset:0;z-index:50000;background:linear-gradient(135deg,#e8f5f3,#f7faf9);display:flex;align-items:center;justify-content:center;padding:24px;font-family:Arial,sans-serif';
  gate.innerHTML='<div style="width:min(420px,100%);background:#fff;border-radius:24px;padding:28px;box-shadow:0 30px 80px rgba(22,61,56,.18);text-align:center"><div style="width:64px;height:64px;margin:0 auto 14px;border-radius:18px;background:#0f8f83;color:#fff;display:grid;place-items:center;font-size:30px">🦺</div><h2 style="margin:0 0 8px;color:#173d39">Gestão EPI</h2><p id="gestaoCommercialBootText" style="margin:0;color:#617b77">Carregando acesso da empresa…</p></div>';
  document.body.appendChild(gate);

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

  function hideLegacyConnect(){
    const overlay=document.getElementById('connectOverlay');
    if(!overlay)return;
    overlay.classList.add('hidden');
    overlay.style.display='none';
    overlay.setAttribute('aria-hidden','true');
  }

  function releaseGateWhenAuthExists(){
    const release=()=>{
      if(document.getElementById('gestaoAuthOverlay')){
        gate.remove();
        return true;
      }
      return false;
    };
    if(release())return;
    const obs=new MutationObserver(()=>{if(release())obs.disconnect();});
    obs.observe(document.body,{childList:true,subtree:true});
    setTimeout(()=>{
      if(!release()){
        const text=document.getElementById('gestaoCommercialBootText');
        if(text)text.textContent='Não foi possível abrir o login. Feche o programa e abra novamente.';
      }
    },5000);
  }

  function loadScript(src,attr,onload,onerror){
    if(document.querySelector(`script[data-${attr}]`)){onload?.();return;}
    const script=document.createElement('script');
    script.src=src;
    script.async=false;
    script.setAttribute(`data-${attr}`,'1');
    if(onload)script.onload=onload;
    if(onerror)script.onerror=onerror;
    document.head.appendChild(script);
  }

  hideLegacyConnect();
  applyNeutralBrand();
  releaseGateWhenAuthExists();

  /* O login é carregado explicitamente. Não usamos document.write nem dependemos
     de outro arquivo para iniciar a autenticação. */
  loadScript('auth-gestao.js','auth-gestao',()=>{
    loadScript('login-uppercase-gestao.js','login-uppercase-gestao');
  },()=>{
    const text=document.getElementById('gestaoCommercialBootText');
    if(text)text.textContent='Falha ao carregar a autenticação do Gestão EPI.';
  });

  loadScript('epi-tools.js','epi-tools');
  loadScript('epi-photo-ca-gestao.js','epi-photo-ca-gestao');
  loadScript('worker-link-gestao.js','worker-link-gestao');
  loadScript('company-branding-gestao.js','company-branding-gestao');

  document.addEventListener('DOMContentLoaded',()=>{
    hideLegacyConnect();
    applyNeutralBrand();
    const obs=new MutationObserver(()=>sanitizeText());
    obs.observe(document.body,{childList:true,subtree:true,characterData:true});
    setTimeout(applyNeutralBrand,300);
  });
})();