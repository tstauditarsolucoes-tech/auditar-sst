(() => {
  const CACHE_KEY='auditarEpiGestaoCacheV1';
  const OPTIONS=[['employee','Funcionário'],['pending','Aguardando admissão'],['third_party','Terceirizado'],['temporary','Temporário'],['visitor','Visitante / prestador']];
  const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
  const label=v=>OPTIONS.find(x=>x[0]===(v||'employee'))?.[1]||'Funcionário';
  const optionsHtml=()=>OPTIONS.map(([v,t])=>`<option value="${v}">${t}</option>`).join('');
  let pending=null;

  function readCache(){try{return JSON.parse(localStorage.getItem(CACHE_KEY)||'{}');}catch{return {};}}
  function injectStyle(){if($('#workerLinkGestaoStyle'))return;const s=document.createElement('style');s.id='workerLinkGestaoStyle';s.textContent='.gestao-link-badge{display:inline-block;margin-top:4px;padding:3px 7px;border-radius:999px;background:#edf7f5;color:#17665e;font-size:10px;font-weight:850}';document.head.appendChild(s);}

  function injectDialogField(){
    const dlg=$('#formDialog');if(!dlg?.open||$('#df_linkType'))return;
    const title=$('#dialogTitle')?.textContent||'';if(!/trabalhador/i.test(title))return;
    const fields=$('#dialogFields');if(!fields)return;const lab=document.createElement('label');lab.className='full';lab.innerHTML=`Tipo de vínculo<select id="df_linkType">${optionsHtml()}</select>`;fields.appendChild(lab);$('#df_linkType').value='employee';
  }

  function capturePending(){
    const dlg=$('#formDialog');if(!dlg?.open||!$('#df_linkType'))return;
    pending={companyId:$('#df_companyId')?.value||'',name:($('#df_name')?.value||'').trim(),linkType:$('#df_linkType').value||'employee',at:Date.now()};
  }

  const baseFetch=window.fetch.bind(window);
  window.fetch=async function(input,init){
    if(pending&&init?.body){
      try{const body=JSON.parse(init.body);if(body.action==='epi_sync_merge'&&body.payload?.app?.workers){const rows=body.payload.app.workers.filter(w=>w.companyId===pending.companyId&&String(w.name||'').trim()===pending.name);const w=rows.sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')))[0];if(w){w.linkType=pending.linkType;w.updatedAt=new Date().toISOString();init={...init,body:JSON.stringify(body)};pending=null;}}}catch(_){}
    }
    return baseFetch(input,init);
  };

  function decorateTable(){
    const table=$('#workerTable table');if(!table)return;const cache=readCache(),workers=cache?.app?.workers||[];
    table.querySelectorAll('tbody tr').forEach(row=>{const first=row.cells?.[0];if(!first||first.querySelector('.gestao-link-badge'))return;const name=first.textContent.trim();const w=workers.find(x=>String(x.name||'').trim()===name);if(!w)return;first.insertAdjacentHTML('beforeend',`<div><span class="gestao-link-badge">${label(w.linkType)}</span></div>`);});
  }

  function init(){injectStyle();$('#btnNewWorker')?.addEventListener('click',()=>setTimeout(injectDialogField,20));$('#dialogSave')?.addEventListener('click',capturePending,true);const target=$('#workerTable');if(target)new MutationObserver(decorateTable).observe(target,{childList:true,subtree:true});decorateTable();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();