(() => {
  'use strict';
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const APP_KEY='auditarEpiV1';
  const CA_URL='https://caepi.trabalho.gov.br/internet/ConsultaCAInternet.aspx';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const clean=v=>String(v??'').replace(/\s+/g,' ').trim();
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let debounce=null,lastKey='',pendingChecks=new Map(),writing=false;

  function token(){return window.GestaoEpiAuth?.token?.()||'';}
  function normalizeRows(){
    const rows=$$('[data-nfai]');
    let changed=false;
    for(const row of rows){
      const name=row.querySelector('.nfai-name'),ca=row.querySelector('.nfai-ca'),size=row.querySelector('.nfai-size');
      if(!name||!ca)continue;
      const raw=String(name.value||'');
      const caMatch=raw.match(/(?:^|\s)CA\s*[.:#º°-]*\s*(\d{3,6})\b/i);
      if(!ca.value&&caMatch){ca.value=caMatch[1];changed=true;}
      if(size&&!size.value){
        let m=raw.match(/\bNR\.?\s*(\d{2})\b/i);
        if(!m)m=raw.match(/\b(PP|P|M|G|GG|XG|XGG)(?:\s+(\d{1,2}(?:-\d{1,2})?))?\b/i);
        if(m){size.value=m[1]+(m[2]?' '+m[2]:'');changed=true;}
      }
      let next=raw.replace(/(?:^|\s)CA\s*[.:#º°-]*\s*\d{3,6}\b/ig,' ')
        .replace(/\bNR\.?\s*\d{2}\b/ig,' ')
        .replace(/\b(PP|P|M|G|GG|XG|XGG)\s+\d{1,2}(?:-\d{1,2})?\b/ig,' ');
      next=clean(next);
      if(next&&next!==raw){name.value=next;changed=true;}
    }
    if(changed)scheduleValidation();
  }

  function scheduleValidation(){clearTimeout(debounce);debounce=setTimeout(validate,450);}

  async function validate(){
    const auth=token();if(!auth||!navigator.onLine)return;
    const rows=$$('[data-nfai]');
    const items=rows.map(row=>({ca:clean(row.querySelector('.nfai-ca')?.value).replace(/\D/g,''),name:clean(row.querySelector('.nfai-name')?.value)})).filter(x=>x.ca);
    const key=items.map(x=>x.ca+'|'+x.name).join(';');if(!items.length||key===lastKey)return;lastKey=key;
    try{
      const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'tenant_ai_assistant',authToken:auth,payload:{mode:'ca_validate',items}})});
      const data=await res.json();if(!data?.ok||!Array.isArray(data.result?.checks))return;
      pendingChecks=new Map(data.result.checks.map(c=>[String(c.ca||'').replace(/\D/g,''),c]));
      for(const row of rows){
        const ca=clean(row.querySelector('.nfai-ca')?.value).replace(/\D/g,''),c=pendingChecks.get(ca),status=row.querySelector('.nfai-status');if(!ca||!status)continue;
        if(c?.found===true){const bad=/venc|expir|cancel/i.test(String(c.status||''));status.innerHTML=`<span class="nfai-pill ${bad?'bad':'ok'}">CA ${esc(ca)} • ${esc(c.status||'confirmado')}</span><a class="nfai-official" href="${esc(c.sourceUrl||CA_URL)}" target="_blank" rel="noopener">Fonte oficial</a>`;}
        else if(c){status.innerHTML=`<span class="nfai-pill bad">CA ${esc(ca)} não confirmado</span><a class="nfai-official" href="${CA_URL}" target="_blank" rel="noopener">Consultar MTE</a>`;}
      }
    }catch(_){ }
  }

  function persistChecks(){
    if(writing||!pendingChecks.size)return;
    try{
      const app=JSON.parse(localStorage.getItem(APP_KEY)||'{}');if(!Array.isArray(app.epis))return;
      let changed=false,now=new Date().toISOString();
      for(const epi of app.epis){const ca=String(epi.ca||'').replace(/\D/g,''),c=pendingChecks.get(ca);if(!c)continue;epi.caVerified=c.found===true;epi.caStatus=clean(c.status);epi.caCheckedAt=now;epi.caSource=clean(c.sourceUrl||CA_URL);if(!epi.model&&c.manufacturer)epi.model=clean(c.manufacturer);changed=true;}
      if(changed){writing=true;localStorage.setItem(APP_KEY,JSON.stringify(app));setTimeout(()=>writing=false,0);}
    }catch(_){ }
  }

  function boot(){
    const observer=new MutationObserver(()=>{normalizeRows();scheduleValidation();});
    observer.observe(document.body,{childList:true,subtree:true});
    document.addEventListener('input',e=>{if(e.target.closest?.('[data-nfai]'))scheduleValidation();});
    document.addEventListener('auditar-epi-data-changed',()=>setTimeout(persistChecks,80));
    setTimeout(normalizeRows,500);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();