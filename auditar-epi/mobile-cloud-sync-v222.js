(() => {
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const REV_STORE='auditarEpiServerRevision';
  const NEEDS_REFRESH='gestaoEpiNeedsRefreshV222';
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const SYNC_TIMEOUT=25000;
  const AUTO_SYNC_MAX_BYTES=650000;
  const AUTO_SYNC_DELAY=9000;
  const SAFE_REFRESH_MAX_BYTES=900000;
  let syncing=false,pushTimer=null,lastSyncAt=0,ready=false;

  function loadScript(src,attr){if(document.querySelector(`script[data-${attr}]`))return;const s=document.createElement('script');s.src=src;s.dataset[attr.replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]='1';document.head.appendChild(s);}
  function loadStyle(src,attr){if(document.querySelector(`link[data-${attr}]`))return;const l=document.createElement('link');l.rel='stylesheet';l.href=src;l.dataset[attr.replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]='1';document.head.appendChild(l);}
  loadScript('company-branding.js','company-branding');
  loadScript('mobile-layout-fix.js','mobile-layout-fix');
  loadScript('epi-photo-ca.js','epi-photo-ca');
  loadScript('worker-link.js','worker-link');
  loadScript('bulk-delivery.js','bulk-delivery');
  loadScript('signature-worker-name.js','signature-worker-name');
  loadScript('field-operations-v221.js','field-operations-v221');
  loadStyle('mobile-v3.css','mobile-v3-style');
  loadScript('mobile-v3.js','mobile-v3');

  const $=(s,root=document)=>root.querySelector(s);
  const auth=()=>window.GestaoEpiAuth;
  const raw=(k,fallback)=>localStorage.getItem(k)||fallback;
  const totalLocalBytes=()=>raw(APP_KEY,'{}').length+raw(STOCK_KEY,'{}').length;

  function status(text,kind='idle'){const el=$('#epiCloudStatus');if(!el)return;el.textContent=text;el.dataset.kind=kind;el.title=text;}
  function showToast(msg){const el=$('#toast');if(!el)return;el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),3000);}
  function setButtonBusy(busy){const b=$('#epiCloudButton');if(!b)return;b.disabled=!!busy;b.style.opacity=busy?'.55':'1';}

  function injectUi(){
    if($('#epiCloudButton'))return;
    const top=$('.topbar');if(!top)return;
    const oldBackup=$('#btnBackup');const wrap=document.createElement('div');wrap.style.cssText='display:flex;align-items:center;gap:7px';
    wrap.innerHTML=`<button id="epiCloudButton" class="icon-btn" type="button" title="Sincronizar agora" aria-label="Sincronizar agora">☁️</button><span id="epiCloudStatus" data-kind="idle" style="font-size:9px;font-weight:800;max-width:92px;line-height:1.05;color:#647b78">Aguardando</span>`;
    if(oldBackup){oldBackup.parentNode.insertBefore(wrap,oldBackup);wrap.appendChild(oldBackup);}else top.appendChild(wrap);
    $('#epiCloudButton')?.addEventListener('click',()=>manualSync());
  }

  function validJsonRaw(v,fallback='{}'){
    if(!v)return fallback;
    const t=v.trim();
    if((t.startsWith('{')&&t.endsWith('}'))||(t.startsWith('[')&&t.endsWith(']')))return t;
    return fallback;
  }

  function buildSyncBody(token){
    const appRaw=validJsonRaw(localStorage.getItem(APP_KEY),'{}');
    const stockRaw=validJsonRaw(localStorage.getItem(STOCK_KEY),'{}');
    const rev=Number(localStorage.getItem(REV_STORE)||0);
    const now=new Date().toISOString();
    return `{"action":"epi_sync_merge","authToken":${JSON.stringify(token)},"deviceId":${JSON.stringify(auth()?.deviceId?.()||'')},"client":"campo-android-v300","payload":{"version":1,"revision":${rev},"updatedAt":${JSON.stringify(now)},"app":${appRaw},"stock":${stockRaw}}}`;
  }

  function isHomeVisible(){return $('#home')?.classList.contains('active');}
  function canAutoSync(){return navigator.onLine&&!!auth()?.token?.()&&totalLocalBytes()<=AUTO_SYNC_MAX_BYTES;}

  async function manualSync(){
    if(!auth()?.token()){showToast('Entre no sistema para sincronizar.');return;}
    await sync({manual:true,allowRefresh:true});
  }

  async function sync({manual=false,allowRefresh=false}={}){
    if(syncing)return false;
    if(!navigator.onLine){status('Offline','offline');return false;}
    const token=auth()?.token?.()||'';
    if(!token){status('Pronto','idle');return false;}

    syncing=true;setButtonBusy(true);status('Sincronizando…','busy');
    const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),SYNC_TIMEOUT);

    try{
      // Libera um quadro de renderização antes de montar/enviar a base.
      await new Promise(resolve=>requestAnimationFrame(()=>setTimeout(resolve,40)));
      const body=buildSyncBody(token);
      const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body,signal:controller.signal});
      const responseText=await res.text();
      const json=JSON.parse(responseText||'{}');
      if(!json?.ok)throw new Error(json?.message||'Falha na sincronização.');

      const remote=json.payload||{};
      const currentApp=localStorage.getItem(APP_KEY)||'';
      const currentStock=localStorage.getItem(STOCK_KEY)||'';
      const remoteApp=JSON.stringify(remote.app||{});
      const remoteStock=JSON.stringify(remote.stock||{});
      const changed=remoteApp!==currentApp||remoteStock!==currentStock;

      localStorage.setItem(REV_STORE,String(json.revision||remote.revision||0));
      if(remoteApp!==currentApp)localStorage.setItem(APP_KEY,remoteApp);
      if(remoteStock!==currentStock)localStorage.setItem(STOCK_KEY,remoteStock);
      lastSyncAt=Date.now();

      const responseBytes=responseText.length;
      if(changed){
        // Só redesenha imediatamente quando a resposta é pequena.
        // Bases grandes ficam salvas e são aplicadas na próxima abertura, evitando congelar o WebView.
        if(allowRefresh&&responseBytes<=SAFE_REFRESH_MAX_BYTES&&isHomeVisible()){
          requestAnimationFrame(()=>setTimeout(()=>document.dispatchEvent(new CustomEvent('gestao-epi-sync-applied',{detail:{remote:true}})),120));
          localStorage.removeItem(NEEDS_REFRESH);
        }else{
          localStorage.setItem(NEEDS_REFRESH,'1');
        }
      }

      status(changed?'Sincronizado':'Tudo em dia','ok');
      if(manual){
        if(changed&&responseBytes>SAFE_REFRESH_MAX_BYTES)showToast('Sincronizado. Os dados foram salvos; reabra o app quando quiser atualizar a tela.');
        else showToast(changed?'Sincronizado. Dados atualizados.':'Sincronizado. Tudo em dia.');
      }
      return true;
    }catch(err){
      const timedOut=err?.name==='AbortError';
      status(timedOut?'Sync demorou':'Falha sync','error');
      if(manual)showToast(timedOut?'A sincronização demorou demais. Tente novamente com internet estável.':(err?.message||'Não foi possível sincronizar.'));
      return false;
    }finally{
      clearTimeout(timeout);syncing=false;setButtonBusy(false);
    }
  }

  function scheduleAuto(delay=AUTO_SYNC_DELAY){
    clearTimeout(pushTimer);
    if(!canAutoSync()){status('Pendente • toque ☁️','idle');return;}
    pushTimer=setTimeout(()=>{
      // Nunca inicia uma sincronização automática enquanto o usuário está na tela de entrega.
      if($('#delivery')?.classList.contains('active')){status('Pendente • toque ☁️','idle');return;}
      sync({manual:false,allowRefresh:false});
    },delay);
  }

  function bindWrites(){
    ['companyForm','workerForm','epiForm'].forEach(id=>$('#'+id)?.addEventListener('submit',()=>scheduleAuto(5000)));
    $('#btnSaveDelivery')?.addEventListener('click',()=>scheduleAuto(6500));
    $('#btnStockSave')?.addEventListener('click',()=>scheduleAuto(5000));
    $('#btnCommitImport')?.addEventListener('click',()=>scheduleAuto(6500));
    document.addEventListener('auditar-epi-data-changed',()=>scheduleAuto(5000));
  }

  function onAuthReady(){
    ready=true;
    // Mobile v3 mantém a regra estável: não sincroniza tudo imediatamente após o login.
    status('Pronto','idle');
    if(canAutoSync())scheduleAuto(12000);
  }

  window.addEventListener('online',()=>{status(ready?'Pronto':'Online','idle');if(ready&&canAutoSync()&&Date.now()-lastSyncAt>180000)scheduleAuto(12000);});
  window.addEventListener('offline',()=>status('Offline','offline'));
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&ready&&canAutoSync()&&Date.now()-lastSyncAt>300000)scheduleAuto(15000);});
  document.addEventListener('gestao-epi-auth-ready',onAuthReady);
  document.addEventListener('DOMContentLoaded',()=>{
    injectUi();bindWrites();status(navigator.onLine?'Aguardando login':'Offline',navigator.onLine?'idle':'offline');
    if(auth()?.isReady?.())onAuthReady();
  },{once:true});
})();
