(()=>{
  'use strict';
  const APP_KEY="auditarEpiGestaoCacheV1";
  const KEY_ID='tenant-bio-v1';
  const CACHE_PREFIX='gestaoEpiBiometricWrappedKeyV1::';
  const DB_NAME='gestaoEpiSecureKeysV1';
  const DB_STORE='keys';
  const DEVICE_KEY='device-wrap-aes-gcm-v1';
  let tenantCryptoKey=null,tenantIdCached='',migrationBusy=false;

  const auth=()=>window.GestaoEpiAuth;
  const tenantId=()=>String(auth()?.tenant?.()?.id||'');
  const api=(action,extra={})=>auth()?.api?.(action,extra);
  const enc=new TextEncoder(),dec=new TextDecoder();

  function b64u(bytes){
    let s='';for(const b of new Uint8Array(bytes))s+=String.fromCharCode(b);
    return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function fromB64u(s){
    s=String(s||'').replace(/-/g,'+').replace(/_/g,'/');s+='='.repeat((4-s.length%4)%4);
    const raw=atob(s),out=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);return out;
  }
  function randomBytes(n){const a=new Uint8Array(n);crypto.getRandomValues(a);return a;}
  function readRoot(){try{return JSON.parse(localStorage.getItem(APP_KEY)||'{}');}catch(_){return {};}}
  function workers(root){root.app=root.app&&typeof root.app==='object'?root.app:{};root.app.workers=Array.isArray(root.app.workers)?root.app.workers:[];return root.app.workers;}
  function saveRoot(root){localStorage.setItem(APP_KEY,JSON.stringify(root));}
  function hasTemplate(w){const b=w?.biometric;return !!(Array.isArray(b?.embedding)&&b.embedding.length)||!!(b?.encryptedTemplate?.ciphertext&&b?.encryptedTemplate?.iv);}
  function legacyBiometric(embedding,meta={}){return {...meta,type:'face-1to1',engine:meta.engine||'human-faceres',version:2,embedding:Array.from(embedding||[]),encryptionPending:true};}

  function openDb(){
    return new Promise((resolve,reject)=>{
      if(!window.indexedDB)return reject(new Error('IndexedDB indisponível'));
      const req=indexedDB.open(DB_NAME,1);
      req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains(DB_STORE))db.createObjectStore(DB_STORE);};
      req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error||new Error('Falha no cofre local'));
    });
  }
  async function getDeviceKey(){
    const db=await openDb();
    const current=await new Promise((resolve,reject)=>{const tx=db.transaction(DB_STORE,'readonly'),r=tx.objectStore(DB_STORE).get(DEVICE_KEY);r.onsuccess=()=>resolve(r.result||null);r.onerror=()=>reject(r.error);});
    if(current)return current;
    const key=await crypto.subtle.generateKey({name:'AES-GCM',length:256},false,['encrypt','decrypt']);
    await new Promise((resolve,reject)=>{const tx=db.transaction(DB_STORE,'readwrite');tx.objectStore(DB_STORE).put(key,DEVICE_KEY);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);});
    return key;
  }
  async function cacheRawTenantKey(id,raw){
    try{
      const dk=await getDeviceKey(),iv=randomBytes(12),ct=await crypto.subtle.encrypt({name:'AES-GCM',iv},dk,raw);
      localStorage.setItem(CACHE_PREFIX+id,JSON.stringify({v:1,iv:b64u(iv),ct:b64u(ct)}));
    }catch(_){}
  }
  async function cachedRawTenantKey(id){
    try{
      const row=JSON.parse(localStorage.getItem(CACHE_PREFIX+id)||'null');if(!row?.iv||!row?.ct)return null;
      const dk=await getDeviceKey(),pt=await crypto.subtle.decrypt({name:'AES-GCM',iv:fromB64u(row.iv)},dk,fromB64u(row.ct));return new Uint8Array(pt);
    }catch(_){return null;}
  }
  async function importTenantKey(raw){return crypto.subtle.importKey('raw',raw,{name:'AES-GCM'},false,['encrypt','decrypt']);}
  async function getTenantKey(){
    const id=tenantId();if(!id)throw new Error('Empresa não identificada.');
    if(tenantCryptoKey&&tenantIdCached===id)return tenantCryptoKey;
    const cached=await cachedRawTenantKey(id);
    if(cached?.length===32){tenantCryptoKey=await importTenantKey(cached);tenantIdCached=id;return tenantCryptoKey;}
    if(!navigator.onLine||!api)throw new Error('Conecte à internet uma vez para habilitar a biometria criptografada neste dispositivo.');
    const r=await api('tenant_biometric_key');
    if(!r?.ok||!r.key)throw new Error(r?.message||'Central biométrica ainda não está habilitada.');
    const raw=fromB64u(r.key);if(raw.length!==32)throw new Error('Chave biométrica inválida.');
    await cacheRawTenantKey(id,raw);tenantCryptoKey=await importTenantKey(raw);tenantIdCached=id;return tenantCryptoKey;
  }
  async function encryptEmbedding(embedding){
    const key=await getTenantKey(),iv=randomBytes(12),plain=enc.encode(JSON.stringify(Array.from(embedding||[])));
    const ct=await crypto.subtle.encrypt({name:'AES-GCM',iv},key,plain);
    return {v:1,alg:'AES-GCM',keyId:KEY_ID,iv:b64u(iv),ciphertext:b64u(ct)};
  }
  async function decryptTemplate(t){
    if(!t?.iv||!t?.ciphertext)throw new Error('Template biométrico criptografado inválido.');
    const key=await getTenantKey(),pt=await crypto.subtle.decrypt({name:'AES-GCM',iv:fromB64u(t.iv)},key,fromB64u(t.ciphertext));
    const arr=JSON.parse(dec.decode(pt));if(!Array.isArray(arr)||!arr.length)throw new Error('Template biométrico vazio.');return arr.map(Number);
  }
  async function getEmbedding(worker){
    const b=worker?.biometric||{};
    if(b?.encryptedTemplate?.ciphertext)return decryptTemplate(b.encryptedTemplate);
    if(Array.isArray(b.embedding)&&b.embedding.length)return b.embedding.map(Number);
    return [];
  }
  async function storeEncrypted(workerId,biometric){
    if(!api)return false;
    try{const r=await api('tenant_store_biometric',{payload:{workerId,biometric}});return !!r?.ok;}catch(_){return false;}
  }
  async function protectEmbedding(workerId,embedding,meta={}){
    try{
      const encryptedTemplate=await encryptEmbedding(embedding);
      const biometric={...meta,type:'face-1to1',engine:meta.engine||'human-faceres',version:3,encryption:'AES-GCM-256',keyId:KEY_ID,encryptedTemplate};
      delete biometric.embedding;delete biometric.encryptionPending;
      const stored=await storeEncrypted(workerId,biometric);
      if(!stored)return legacyBiometric(embedding,meta);
      return biometric;
    }catch(_){return legacyBiometric(embedding,meta);}
  }
  async function migrate(){
    if(migrationBusy||!tenantId())return false;
    migrationBusy=true;
    try{
      await getTenantKey();
      const root=readRoot(),rows=workers(root);let changed=false;
      for(const w of rows){
        const b=w?.biometric;
        if(!Array.isArray(b?.embedding)||!b.embedding.length)continue;
        const encryptedTemplate=await encryptEmbedding(b.embedding);
        const next={...b,version:3,encryption:'AES-GCM-256',keyId:KEY_ID,encryptedTemplate,migratedAt:new Date().toISOString()};
        delete next.embedding;delete next.encryptionPending;
        const stored=await storeEncrypted(w.id,next);
        if(!stored)continue;
        w.biometric=next;w.updatedAt=new Date().toISOString();changed=true;
      }
      if(changed)saveRoot(root);
      return changed;
    }catch(_){return false;}finally{migrationBusy=false;}
  }
  function scheduleMigration(){[350,1400,4500].forEach(ms=>setTimeout(()=>migrate(),ms));}
  document.addEventListener('gestao-epi-auth-ready',scheduleMigration);
  document.addEventListener('auditar-epi-state-refreshed',scheduleMigration);
  window.addEventListener('online',scheduleMigration);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scheduleMigration,{once:true});else scheduleMigration();

  window.GestaoEpiBiometricCrypto={hasTemplate,getEmbedding,protectEmbedding,migrate,getTenantKey,keyId:KEY_ID};
})();