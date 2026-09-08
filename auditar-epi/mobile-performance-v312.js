(() => {
  'use strict';
  const APP_KEY='auditarEpiV1';
  const SIG_PREFIX='auditarEpiSignatureV2:';
  const nativeGet=Storage.prototype.getItem;
  const nativeSet=Storage.prototype.setItem;
  const nativeRemove=Storage.prototype.removeItem;

  function sigKey(id){return SIG_PREFIX+String(id||'');}
  function getSig(id){try{return nativeGet.call(localStorage,sigKey(id))||'';}catch{return '';}}
  function putSig(id,data){if(!id||!data)return;try{nativeSet.call(localStorage,sigKey(id),String(data));}catch(_){}}
  function removeSig(id){try{nativeRemove.call(localStorage,sigKey(id));}catch(_){}}

  function compactObject(app){
    if(!app||typeof app!=='object')return app;
    const rows=Array.isArray(app.deliveries)?app.deliveries:[];
    for(const d of rows){
      if(!d?.id)continue;
      if(typeof d.signature==='string'&&d.signature.length>80){putSig(d.id,d.signature);delete d.signature;d.signatureStored=true;}
    }
    return app;
  }

  function hydrateObject(app){
    if(!app||typeof app!=='object')return app;
    const clone=JSON.parse(JSON.stringify(app));
    const rows=Array.isArray(clone.deliveries)?clone.deliveries:[];
    for(const d of rows){
      if(!d?.id)continue;
      if(!d.signature){const sig=getSig(d.id);if(sig)d.signature=sig;}
    }
    return clone;
  }

  function compactStoredApp(){
    try{
      const raw=nativeGet.call(localStorage,APP_KEY)||'{}';
      const app=JSON.parse(raw);let changed=false;
      const rows=Array.isArray(app.deliveries)?app.deliveries:[];
      for(const d of rows){
        if(d?.id&&typeof d.signature==='string'&&d.signature.length>80){putSig(d.id,d.signature);delete d.signature;d.signatureStored=true;changed=true;}
      }
      if(changed)nativeSet.call(localStorage,APP_KEY,JSON.stringify(app));
    }catch(_){ }
  }

  // Mantém o banco principal leve mesmo quando módulos antigos salvam uma assinatura dentro dele.
  Storage.prototype.setItem=function(key,value){
    if(this===localStorage&&key===APP_KEY&&typeof value==='string'){
      try{const app=compactObject(JSON.parse(value));value=JSON.stringify(app);}catch(_){ }
    }
    return nativeSet.call(this,key,value);
  };

  function patchReceipt(deliveryId=''){
    setTimeout(()=>{
      const content=document.querySelector('#receiptContent');if(!content)return;
      let id=deliveryId;
      if(!id){
        const btn=document.querySelector('[data-receipt].active');id=btn?.dataset?.receipt||'';
      }
      if(!id){
        try{
          const app=JSON.parse(nativeGet.call(localStorage,APP_KEY)||'{}');
          const text=content.textContent||'';
          const row=(app.deliveries||[]).find(d=>text.includes(new Date(d.createdAt||0).toLocaleDateString('pt-BR')));id=row?.id||'';
        }catch(_){ }
      }
      if(!id)return;
      const sig=getSig(id);if(!sig)return;
      const img=content.querySelector('.receipt-sign img, img[data-signature], .receipt-signature img');
      if(img&&!img.getAttribute('src'))img.setAttribute('src',sig);
    },40);
  }

  compactStoredApp();
  window.GestaoEpiSignatureStore={
    get:getSig,
    put:putSig,
    remove:removeSig,
    compact:compactObject,
    hydrate:hydrateObject,
    hydrateRaw(raw){try{return JSON.stringify(hydrateObject(JSON.parse(raw||'{}')));}catch{return raw||'{}';}},
    compactRemote(app){return compactObject(app);}
  };

  document.addEventListener('click',e=>{
    const r=e.target.closest?.('[data-receipt]');if(r)patchReceipt(r.dataset.receipt||'');
  },true);
  document.addEventListener('DOMContentLoaded',()=>{
    document.querySelector('#btnSaveDelivery')?.addEventListener('click',()=>patchReceipt(''));
  },{once:true});
})();
