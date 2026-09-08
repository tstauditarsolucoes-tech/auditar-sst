(() => {
  'use strict';
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const REV_STORE='auditarEpiServerRevision';
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const SYNC_TIMEOUT=30000;
  let syncing=false,pushTimer=null,ready=false,lastSyncAt=0;

  function loadScript(src,attr){
    if(document.querySelector(`script[src="${src}"]`)||document.querySelector(`script[data-${attr}]`))return;
    const s=document.createElement('script');s.src=src;s.dataset[attr.replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]='1';document.head.appendChild(s);
  }
  loadScript('mobile-layout-fix.js','mobile-layout-fix');
  loadScript('epi-photo-ca.js','epi-photo-ca');
  loadScript('worker-link.js','worker-link');
  loadScript('bulk-delivery.js','bulk-delivery');
  loadScript('signature-worker-name.js','signature-worker-name');

  const $=(s,r=document)=>r.querySelector(s);
  const auth=()=>window.GestaoEpiAuth;
  const compactBytes=()=>String(localStorage.getItem(APP_KEY)||'{}').length+String(localStorage.getItem(STOCK_KEY)||'{}').length;
  const isHome=()=>$('#home')?.classList.contains('active');

  function status(text,kind='idle'){const el=$('#epiCloudStatus');if(!el)return;el.textContent=text;el.dataset.kind=kind;el.title=text;}
  function toast(msg){const el=$('#toast');if(!el)return;el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);}
  function setBusy(v){const b=$('#epiCloudButton');if(b){b.disabled=!!v;b.style.opacity=v?'.55':'1';}}

  function injectUi(){
    if($('#epiCloudButton'))return;const top=$('.topbar');if(!top)return;
    const wrap=document.createElement('div');wrap.style.cssText='display:flex;align-items:center;gap:7px';
    wrap.innerHTML='<button id="epiCloudButton" class="icon-btn" type="button" title="Sincronizar agora">☁️</button><span id="epiCloudStatus" style="font-size:9px;font-weight:800;max-width:92px;line-height:1.05;color:#647b78">Aguardando</span>';
    const backup=$('#btnBackup');if(backup){backup.parentNode.insertBefore(wrap,backup);wrap.appendChild(backup);}else top.appendChild(wrap);
    $('#epiCloudButton')?.addEventListener('click',()=>sync({manual:true}));
  }

  function buildPayload(token){
    const compactApp=JSON.parse(localStorage.getItem(APP_KEY)||'{}');
    const stock=JSON.parse(localStorage.getItem(STOCK_KEY)||'{}');
    const app=window.GestaoEpiSignatureStore?.hydrate?window.GestaoEpiSignatureStore.hydrate(compactApp):compactApp;
    return JSON.stringify({
      action:'epi_sync_merge',
      authToken:token,
      deviceId:auth()?.deviceId?.()||'',
      client:'campo-android-v312',
      payload:{version:1,revision:Number(localStorage.getItem(REV_STORE)||0),updatedAt:new Date().toISOString(),app,stock}
    });
  }

  function applyRemote(remote){
    let app=remote?.app||{};
    if(window.GestaoEpiSignatureStore?.compactRemote)app=window.GestaoEpiSignatureStore.compactRemote(app);
    const appRaw=JSON.stringify(app),stockRaw=JSON.stringify(remote?.stock||{});
    const changed=appRaw!==(localStorage.getItem(APP_KEY)||'')||stockRaw!==(localStorage.getItem(STOCK_KEY)||'');
    if(appRaw!==(localStorage.getItem(APP_KEY)||''))localStorage.setItem(APP_KEY,appRaw);
    if(stockRaw!==(localStorage.getItem(STOCK_KEY)||''))localStorage.setItem(STOCK_KEY,stockRaw);
    return changed;
  }

  async function sync({manual=false}={}){
    if(syncing)return false;
    if(!navigator.onLine){status('Offline','offline');if(manual)toast('Sem internet para sincronizar.');return false;}
    const token=auth()?.token?.()||'';if(!token){status('Pronto','idle');if(manual)toast('Entre no sistema para sincronizar.');return false;}
    syncing=true;setBusy(true);status('Sincronizando…','busy');
    const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),SYNC_TIMEOUT);
    try{
      await new Promise(resolve=>requestAnimationFrame(()=>setTimeout(resolve,80)));
      const body=buildPayload(token);
      const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body,signal:controller.signal});
      const json=JSON.parse(await res.text()||'{}');if(!json?.ok)throw new Error(json?.message||'Falha na sincronização.');
      const changed=applyRemote(json.payload||{});
      localStorage.setItem(REV_STORE,String(json.revision||json.payload?.revision||0));lastSyncAt=Date.now();
      status(changed?'Sincronizado':'Tudo em dia','ok');
      if(changed)requestAnimationFrame(()=>setTimeout(()=>document.dispatchEvent(new CustomEvent('gestao-epi-sync-applied',{detail:{remote:true}})),180));
      if(manual)toast(changed?'Sincronizado. Dados atualizados.':'Sincronizado. Tudo em dia.');
      return true;
    }catch(err){
      const timeoutHit=err?.name==='AbortError';status(timeoutHit?'Sync demorou':'Falha sync','error');
      if(manual)toast(timeoutHit?'A sincronização demorou. Tente novamente com internet estável.':(err?.message||'Não foi possível sincronizar.'));
      return false;
    }finally{clearTimeout(timeout);syncing=false;setBusy(false);}
  }

  function canAuto(){return ready&&navigator.onLine&&!!auth()?.token?.()&&isHome()&&compactBytes()<450000;}
  function scheduleAuto(delay=18000){
    clearTimeout(pushTimer);
    if(!canAuto()){status(navigator.onLine?'Pendente • toque ☁️':'Offline',navigator.onLine?'idle':'offline');return;}
    pushTimer=setTimeout(()=>{if(canAuto()&&Date.now()-lastSyncAt>15000)sync({manual:false});},delay);
  }
  function bindWrites(){
    ['companyForm','workerForm','epiForm'].forEach(id=>$('#'+id)?.addEventListener('submit',()=>scheduleAuto()));
    $('#btnSaveDelivery')?.addEventListener('click',()=>scheduleAuto(22000));
    $('#btnStockSave')?.addEventListener('click',()=>scheduleAuto());
    $('#btnCommitImport')?.addEventListener('click',()=>scheduleAuto(22000));
    document.addEventListener('auditar-epi-data-changed',()=>scheduleAuto(20000));
  }
  function onAuth(){ready=true;status('Pronto','idle');}

  window.addEventListener('online',()=>status(ready?'Pronto':'Online','idle'));
  window.addEventListener('offline',()=>status('Offline','offline'));
  document.addEventListener('gestao-epi-auth-ready',onAuth);
  document.addEventListener('DOMContentLoaded',()=>{injectUi();bindWrites();status(navigator.onLine?'Aguardando login':'Offline',navigator.onLine?'idle':'offline');if(auth()?.isReady?.())onAuth();},{once:true});
})();
