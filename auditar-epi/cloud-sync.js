(() => {
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const REV_STORE='auditarEpiServerRevision';
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const SYNC_TIMEOUT=22000;
  let syncing=false,pushTimer=null,lastSyncAt=0,startupQueued=false;

  function loadScript(src,attr){
    if(document.querySelector(`script[data-${attr}]`))return;
    const s=document.createElement('script');
    s.src=src;
    s.dataset[attr.replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]='1';
    document.head.appendChild(s);
  }
  loadScript('company-branding.js','company-branding');
  loadScript('mobile-layout-fix.js','mobile-layout-fix');
  loadScript('epi-photo-ca.js','epi-photo-ca');
  loadScript('worker-link.js','worker-link');
  loadScript('bulk-delivery.js','bulk-delivery');
  loadScript('signature-worker-name.js','signature-worker-name');
  loadScript('field-operations-v221.js','field-operations-v221');

  const $=(s,root=document)=>root.querySelector(s);
  const readJson=(key,fallback)=>{try{return {...fallback,...JSON.parse(localStorage.getItem(key)||'{}')};}catch{return fallback;}};
  const auth=()=>window.GestaoEpiAuth;

  function snapshot(){
    return {
      version:1,
      revision:Number(localStorage.getItem(REV_STORE)||0),
      updatedAt:new Date().toISOString(),
      app:readJson(APP_KEY,{companies:[],workers:[],epis:[],deliveries:[]}),
      stock:readJson(STOCK_KEY,{startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}})
    };
  }
  function status(text,kind='idle'){
    const el=$('#epiCloudStatus');
    if(!el)return;
    el.textContent=text;
    el.dataset.kind=kind;
    el.title=text;
  }
  function showToast(msg){
    const el=$('#toast');
    if(!el)return alert(msg);
    el.textContent=msg;
    el.classList.add('show');
    setTimeout(()=>el.classList.remove('show'),2800);
  }
  function setButtonBusy(busy){
    const b=$('#epiCloudButton');
    if(!b)return;
    b.disabled=!!busy;
    b.style.opacity=busy?'.55':'1';
  }

  function injectUi(){
    if($('#epiCloudButton'))return;
    const top=$('.topbar');
    if(!top)return;
    const oldBackup=$('#btnBackup');
    const wrap=document.createElement('div');
    wrap.style.cssText='display:flex;align-items:center;gap:7px';
    wrap.innerHTML=`<button id="epiCloudButton" class="icon-btn" type="button" title="Sincronizar" aria-label="Sincronizar">☁️</button><span id="epiCloudStatus" data-kind="idle" style="font-size:9px;font-weight:800;max-width:82px;line-height:1.05;color:#647b78">Aguardando</span>`;
    if(oldBackup){oldBackup.parentNode.insertBefore(wrap,oldBackup);wrap.appendChild(oldBackup);}else top.appendChild(wrap);
    $('#epiCloudButton')?.addEventListener('click',()=>manualSync());
  }

  async function manualSync(){
    if(!auth()?.token()){
      showToast('Entre no sistema para sincronizar.');
      return;
    }
    await sync({manual:true});
  }

  async function sync({manual=false}={}){
    if(syncing)return false;
    if(!navigator.onLine){status('Offline','offline');return false;}
    const token=auth()?.token?.()||'';
    if(!token){status('Aguardando login','idle');return false;}

    syncing=true;
    setButtonBusy(true);
    status('Sincronizando…','busy');

    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),SYNC_TIMEOUT);

    try{
      // Dá tempo para o Android desenhar o estado "Sincronizando" antes do trabalho pesado.
      await new Promise(resolve=>setTimeout(resolve,60));
      const local=snapshot();
      const body=JSON.stringify({
        action:'epi_sync_merge',
        authToken:token,
        deviceId:auth()?.deviceId?.()||'',
        client:'campo',
        payload:local
      });

      const res=await fetch(ENDPOINT,{
        method:'POST',
        headers:{'Content-Type':'text/plain;charset=utf-8'},
        body,
        signal:controller.signal
      });
      const json=await res.json();
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
      status('Sincronizado','ok');

      // IMPORTANTE: não recarrega mais o WebView Android depois da sincronização.
      // Os módulos novos leem o localStorage diretamente e recebem este evento.
      if(changed){
        document.dispatchEvent(new CustomEvent('gestao-epi-sync-applied',{detail:{remote:true}}));
      }

      if(manual){
        showToast(changed?'Sincronizado. Dados atualizados.':'Sincronizado. Tudo em dia.');
      }
      return true;
    }catch(err){
      const timedOut=err?.name==='AbortError';
      status(timedOut?'Sync demorou':'Falha sync','error');
      if(manual)showToast(timedOut?'A sincronização demorou demais. Tente novamente com internet estável.':(err?.message||'Não foi possível sincronizar.'));
      return false;
    }finally{
      clearTimeout(timeout);
      syncing=false;
      setButtonBusy(false);
    }
  }

  function schedulePush(delay=1200){
    clearTimeout(pushTimer);
    pushTimer=setTimeout(()=>sync({manual:false}),delay);
  }
  function bindWrites(){
    ['companyForm','workerForm','epiForm'].forEach(id=>$('#'+id)?.addEventListener('submit',()=>schedulePush(1400)));
    $('#btnSaveDelivery')?.addEventListener('click',()=>schedulePush(1800));
    $('#btnStockSave')?.addEventListener('click',()=>schedulePush(1400));
    $('#btnCommitImport')?.addEventListener('click',()=>schedulePush(1800));
    document.addEventListener('auditar-epi-data-changed',()=>schedulePush(1200));
  }
  function startupSync(){
    if(startupQueued)return;
    startupQueued=true;
    if(auth()?.token())setTimeout(()=>sync({manual:false}),2200);
  }

  window.addEventListener('online',()=>{
    status('Online','idle');
    if(auth()?.token()&&Date.now()-lastSyncAt>60000)schedulePush(1800);
  });
  window.addEventListener('offline',()=>status('Offline','offline'));
  document.addEventListener('visibilitychange',()=>{
    if(!document.hidden&&Date.now()-lastSyncAt>120000&&auth()?.token())schedulePush(1500);
  });
  document.addEventListener('gestao-epi-auth-ready',()=>startupSync());
  document.addEventListener('DOMContentLoaded',()=>{
    injectUi();
    bindWrites();
    status(navigator.onLine?'Aguardando login':'Offline',navigator.onLine?'idle':'offline');
    if(auth()?.isReady?.())startupSync();
  });
})();