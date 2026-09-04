(() => {
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const REV_STORE='auditarEpiServerRevision';
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  let syncing=false,pushTimer=null,lastSyncAt=0;

  function loadScript(src,attr){if(document.querySelector(`script[data-${attr}]`))return;const s=document.createElement('script');s.src=src;s.dataset[attr.replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]='1';document.head.appendChild(s);}
  loadScript('company-branding.js','company-branding');
  loadScript('mobile-layout-fix.js','mobile-layout-fix');
  loadScript('epi-photo-ca.js','epi-photo-ca');
  loadScript('worker-link.js','worker-link');
  loadScript('bulk-delivery.js','bulk-delivery');
  loadScript('signature-worker-name.js','signature-worker-name');

  const $=(s,root=document)=>root.querySelector(s);
  const readJson=(key,fallback)=>{try{return {...fallback,...JSON.parse(localStorage.getItem(key)||'{}')};}catch{return fallback;}};
  const auth=()=>window.GestaoEpiAuth;

  function snapshot(){return {version:1,revision:Number(localStorage.getItem(REV_STORE)||0),updatedAt:new Date().toISOString(),app:readJson(APP_KEY,{companies:[],workers:[],epis:[],deliveries:[]}),stock:readJson(STOCK_KEY,{startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}})};}
  function status(text,kind='idle'){const el=$('#epiCloudStatus');if(!el)return;el.textContent=text;el.dataset.kind=kind;el.title=text;}
  function showToast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2600);}

  function injectUi(){
    if($('#epiCloudButton'))return;const top=$('.topbar');if(!top)return;const oldBackup=$('#btnBackup');const wrap=document.createElement('div');wrap.style.cssText='display:flex;align-items:center;gap:7px';wrap.innerHTML=`<button id="epiCloudButton" class="icon-btn" type="button" title="Sincronizar" aria-label="Sincronizar">☁️</button><span id="epiCloudStatus" data-kind="idle" style="font-size:9px;font-weight:800;max-width:72px;line-height:1.05;color:#647b78">Aguardando</span>`;if(oldBackup){oldBackup.parentNode.insertBefore(wrap,oldBackup);wrap.appendChild(oldBackup);}else top.appendChild(wrap);$('#epiCloudButton')?.addEventListener('click',()=>manualSync());
  }

  async function manualSync(){if(!auth()?.token()){showToast('Entre no sistema para sincronizar.');return;}await sync({applyRemote:true,manual:true});}

  async function sync({applyRemote=false,manual=false}={}){
    if(syncing||!navigator.onLine){if(!navigator.onLine)status('Offline','offline');return false;}
    const token=auth()?.token?.()||'';if(!token){status('Aguardando login','idle');return false;}
    syncing=true;status('Sincronizando…','busy');
    try{
      const local=snapshot();
      const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'epi_sync_merge',authToken:token,deviceId:auth()?.deviceId?.()||'',client:'campo',payload:local})});
      const json=await res.json();if(!json?.ok)throw new Error(json?.message||'Falha na sincronização.');
      const remote=json.payload||{},currentApp=localStorage.getItem(APP_KEY)||'',currentStock=localStorage.getItem(STOCK_KEY)||'',remoteApp=JSON.stringify(remote.app||{}),remoteStock=JSON.stringify(remote.stock||{});localStorage.setItem(REV_STORE,String(json.revision||remote.revision||0));lastSyncAt=Date.now();status('Sincronizado','ok');
      if(applyRemote&&(remoteApp!==currentApp||remoteStock!==currentStock)){localStorage.setItem(APP_KEY,remoteApp);localStorage.setItem(STOCK_KEY,remoteStock);sessionStorage.setItem('gestaoEpiSyncedReload','1');location.reload();return true;}
      localStorage.setItem(APP_KEY,remoteApp);localStorage.setItem(STOCK_KEY,remoteStock);if(manual)showToast('Dados sincronizados.');return true;
    }catch(err){status('Falha sync','error');if(manual)showToast(err.message||'Não foi possível sincronizar.');return false;}finally{syncing=false;}
  }

  function schedulePush(delay=700){clearTimeout(pushTimer);pushTimer=setTimeout(()=>sync({applyRemote:false}),delay);}
  function bindWrites(){['companyForm','workerForm','epiForm'].forEach(id=>$('#'+id)?.addEventListener('submit',()=>schedulePush(900)));$('#btnSaveDelivery')?.addEventListener('click',()=>schedulePush(1200));$('#btnStockSave')?.addEventListener('click',()=>schedulePush(900));$('#btnCommitImport')?.addEventListener('click',()=>schedulePush(1300));document.addEventListener('auditar-epi-data-changed',()=>schedulePush(650));}
  function startupSync(){if(sessionStorage.getItem('gestaoEpiSyncedReload')){sessionStorage.removeItem('gestaoEpiSyncedReload');status('Sincronizado','ok');return;}if(auth()?.token())setTimeout(()=>sync({applyRemote:true}),700);}

  window.addEventListener('online',()=>{status('Online','idle');if(auth()?.token())schedulePush(350);});window.addEventListener('offline',()=>status('Offline','offline'));document.addEventListener('visibilitychange',()=>{if(!document.hidden&&Date.now()-lastSyncAt>30000&&auth()?.token())sync({applyRemote:false});});document.addEventListener('gestao-epi-auth-ready',()=>startupSync());
  document.addEventListener('DOMContentLoaded',()=>{injectUi();bindWrites();status(navigator.onLine?'Aguardando login':'Offline',navigator.onLine?'idle':'offline');if(auth()?.isReady?.())startupSync();});
})();