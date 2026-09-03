(() => {
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const KEY_STORE='auditarEpiCentralKey';
  const DEVICE_STORE='auditarEpiDeviceId';
  const REV_STORE='auditarEpiServerRevision';
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  let syncing=false, pushTimer=null, lastSyncAt=0;

  if(!document.querySelector('script[data-company-branding]')){
    const brand=document.createElement('script');
    brand.src='company-branding.js';
    brand.dataset.companyBranding='1';
    document.head.appendChild(brand);
  }

  const $=(s,root=document)=>root.querySelector(s);
  const uid=()=>`campo_${Date.now()}_${Math.random().toString(36).slice(2,10)}`;
  const readJson=(key,fallback)=>{ try{return {...fallback,...JSON.parse(localStorage.getItem(key)||'{}')};}catch{return fallback;} };

  function deviceId(){
    let id=localStorage.getItem(DEVICE_STORE);
    if(!id){ id=uid(); localStorage.setItem(DEVICE_STORE,id); }
    return id;
  }

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
    const el=$('#epiCloudStatus'); if(!el) return;
    el.textContent=text; el.dataset.kind=kind; el.title=text;
  }

  function injectUi(){
    if($('#epiCloudButton')) return;
    const top=$('.topbar'); if(!top) return;
    const oldBackup=$('#btnBackup');
    const wrap=document.createElement('div');
    wrap.style.cssText='display:flex;align-items:center;gap:7px';
    wrap.innerHTML=`<button id="epiCloudButton" class="icon-btn" type="button" title="Sincronizar Campo e Gestão" aria-label="Sincronizar">☁️</button><span id="epiCloudStatus" data-kind="idle" style="font-size:9px;font-weight:800;max-width:62px;line-height:1.05;color:#647b78">Local</span>`;
    if(oldBackup){ oldBackup.parentNode.insertBefore(wrap,oldBackup); wrap.appendChild(oldBackup); }
    else top.appendChild(wrap);
    $('#epiCloudButton')?.addEventListener('click',()=>manualSync());
  }

  async function manualSync(){
    let key=(localStorage.getItem(KEY_STORE)||'').trim();
    if(!key){
      key=(prompt('Cole a chave de sincronização do Auditar EPI. Ela ficará salva neste aparelho.')||'').trim();
      if(!key) return;
      localStorage.setItem(KEY_STORE,key);
    }
    await sync({applyRemote:true,manual:true});
  }

  async function sync({applyRemote=false,manual=false}={}){
    if(syncing || !navigator.onLine) { if(!navigator.onLine) status('Offline','offline'); return false; }
    const key=(localStorage.getItem(KEY_STORE)||'').trim();
    if(!key){ status('Não conectado','offline'); return false; }
    syncing=true; status('Sincronizando…','busy');
    try{
      const local=snapshot();
      const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'epi_sync_merge',syncKey:key,deviceId:deviceId(),client:'campo',payload:local})});
      const json=await res.json();
      if(!json?.ok) throw new Error(json?.message||'Falha na sincronização.');
      const remote=json.payload||{};
      const currentApp=localStorage.getItem(APP_KEY)||'';
      const currentStock=localStorage.getItem(STOCK_KEY)||'';
      const remoteApp=JSON.stringify(remote.app||{});
      const remoteStock=JSON.stringify(remote.stock||{});
      localStorage.setItem(REV_STORE,String(json.revision||remote.revision||0));
      lastSyncAt=Date.now(); status('Sincronizado','ok');

      if(applyRemote && (remoteApp!==currentApp || remoteStock!==currentStock)){
        localStorage.setItem(APP_KEY,remoteApp); localStorage.setItem(STOCK_KEY,remoteStock);
        sessionStorage.setItem('auditarEpiSyncedReload','1'); location.reload(); return true;
      }
      localStorage.setItem(APP_KEY,remoteApp); localStorage.setItem(STOCK_KEY,remoteStock);
      if(manual) showToast('Dados sincronizados com a Gestão.');
      return true;
    }catch(err){
      status('Falha sync','error'); if(manual) showToast(err.message||'Não foi possível sincronizar.'); return false;
    }finally{ syncing=false; }
  }

  function showToast(msg){
    const el=$('#toast'); if(!el) return alert(msg);
    el.textContent=msg; el.classList.add('show'); setTimeout(()=>el.classList.remove('show'),2600);
  }

  function schedulePush(delay=700){ clearTimeout(pushTimer); pushTimer=setTimeout(()=>sync({applyRemote:false}),delay); }

  function bindWrites(){
    ['companyForm','workerForm','epiForm'].forEach(id=>$('#'+id)?.addEventListener('submit',()=>schedulePush(900)));
    $('#btnSaveDelivery')?.addEventListener('click',()=>schedulePush(1200));
    $('#btnStockSave')?.addEventListener('click',()=>schedulePush(900));
    $('#btnCommitImport')?.addEventListener('click',()=>schedulePush(1300));
    document.addEventListener('auditar-epi-data-changed',()=>schedulePush(650));
  }

  function startupSync(){
    if(sessionStorage.getItem('auditarEpiSyncedReload')){
      sessionStorage.removeItem('auditarEpiSyncedReload'); status('Sincronizado','ok'); return;
    }
    if((localStorage.getItem(KEY_STORE)||'').trim()) setTimeout(()=>sync({applyRemote:true}),900);
  }

  window.addEventListener('online',()=>{status('Online','idle');schedulePush(350);});
  window.addEventListener('offline',()=>status('Offline','offline'));
  document.addEventListener('visibilitychange',()=>{ if(!document.hidden && Date.now()-lastSyncAt>30000) sync({applyRemote:false}); });
  document.addEventListener('DOMContentLoaded',()=>{
    injectUi(); bindWrites(); status(navigator.onLine?'Local':'Offline',navigator.onLine?'idle':'offline'); startupSync();
  });
})();
