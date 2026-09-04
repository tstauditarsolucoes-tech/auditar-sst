(() => {
  const CACHE='auditarEpiGestaoCacheV1';
  const OPTIONS=[['employee','Funcionário'],['pending','Aguardando admissão'],['third_party','Terceirizado'],['temporary','Temporário'],['visitor','Visitante / prestador']];
  const $=(s,r=document)=>r.querySelector(s);
  let pending=null;
  function load(){try{return JSON.parse(localStorage.getItem(CACHE)||'{}');}catch{return {};}}
  function save(x){localStorage.setItem(CACHE,JSON.stringify(x));}
  function inject(){
    if(!$('#formDialog')?.open||$('#df_linkType')||!/trabalhador/i.test($('#dialogTitle')?.textContent||''))return;
    const l=document.createElement('label');l.className='full';l.innerHTML=`Tipo de vínculo<select id="df_linkType">${OPTIONS.map(([v,t])=>`<option value="${v}">${t}</option>`).join('')}</select>`;$('#dialogFields')?.appendChild(l);
  }
  async function apply(){
    if(!pending)return;const p=pending;pending=null;await new Promise(r=>setTimeout(r,120));const x=load(),rows=(x.app?.workers||[]).filter(w=>w.companyId===p.companyId&&String(w.name||'').trim()===p.name).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')));const w=rows[0];if(!w)return;w.linkType=p.linkType;w.updatedAt=new Date().toISOString();save(x);try{if(window.GestaoEpiAuth?.api){const r=await window.GestaoEpiAuth.api('epi_sync_merge',{client:'gestao-pc',payload:x});if(r?.ok&&r.payload)save(r.payload);}}catch(_){}$('#btnRefresh')?.click();
  }
  function init(){
    $('#btnNewWorker')?.addEventListener('click',()=>setTimeout(inject,30));
    $('#dialogSave')?.addEventListener('click',()=>{if(!$('#df_linkType'))return;pending={companyId:$('#df_companyId')?.value||'',name:($('#df_name')?.value||'').trim(),linkType:$('#df_linkType').value||'employee'};setTimeout(apply,0);},true);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();