(() => {
  const APP_KEY='auditarEpiV1';
  const SESSION_KEY='gestaoEpiBulkDeliveryV1';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let batch=null,lastDeliveryCount=0;

  function load(){try{return JSON.parse(localStorage.getItem(APP_KEY)||'{}');}catch{return {};}}
  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);}
  function canDeliver(){const r=document.body.dataset.epiRole;return !r||r==='admin'||r==='campo';}
  function workerLabel(w){return `${w.name||'Sem nome'}${w.role?' • '+w.role:''}${w.sector?' • '+w.sector:''}`;}

  function styles(){
    if($('#bulkDeliveryStyle'))return;const s=document.createElement('style');s.id='bulkDeliveryStyle';s.textContent=`
      .bulk-btn{width:100%;margin-top:8px}.bulk-modal{position:fixed;inset:0;z-index:25500;background:rgba(8,35,32,.74);display:none;align-items:center;justify-content:center;padding:18px}.bulk-modal.open{display:flex}.bulk-card{width:min(560px,100%);max-height:90vh;overflow:auto;background:#fff;border-radius:22px;padding:20px;box-shadow:0 24px 70px rgba(0,0,0,.22)}.bulk-card h2{margin:0;color:#173d39}.bulk-card>p{color:#617b77;font-size:12px;line-height:1.45}.bulk-toolbar{display:flex;gap:8px;margin:12px 0}.bulk-toolbar input{flex:1;min-height:44px;border:1px solid #cededa;border-radius:12px;padding:0 11px}.bulk-toolbar button{border:1px solid #cfe0dd;background:#fff;border-radius:11px;padding:0 12px;font-weight:850}.bulk-list{border:1px solid #e1ebe9;border-radius:14px;max-height:48vh;overflow:auto}.bulk-row{display:flex;gap:10px;align-items:flex-start;padding:11px;border-bottom:1px solid #edf2f1}.bulk-row:last-child{border-bottom:0}.bulk-row input{width:20px;height:20px;margin-top:1px}.bulk-row b{display:block;color:#234b47}.bulk-row small{display:block;color:#708783;margin-top:2px}.bulk-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:14px}.bulk-actions button{min-height:46px;padding:0 15px;border-radius:12px;border:1px solid #cfe0dd;background:#fff;font-weight:900}.bulk-actions .primary{border:0;background:#0f766e;color:#fff}.bulk-progress{display:none;margin:10px 0;padding:10px 12px;border-radius:12px;background:#eaf7f5;color:#17665e;font-size:12px;font-weight:850}.bulk-progress.show{display:block}.bulk-cancel{margin-left:8px;border:0;background:transparent;color:#a33;text-decoration:underline;font-weight:800}
    `;document.head.appendChild(s);
  }

  function modal(){
    if($('#bulkDeliveryModal'))return $('#bulkDeliveryModal');
    const d=document.createElement('div');d.id='bulkDeliveryModal';d.className='bulk-modal';d.innerHTML=`<div class="bulk-card"><h2>Entrega em lote</h2><p>Selecione os colaboradores que receberão os mesmos EPIs. A confirmação será feita individualmente para cada pessoa.</p><div class="bulk-toolbar"><input id="bulkSearch" placeholder="Buscar nome, CPF, matrícula ou cargo"><button id="bulkAll" type="button">Marcar todos</button></div><div id="bulkList" class="bulk-list"></div><div class="bulk-actions"><button id="bulkClose" type="button">Cancelar</button><button id="bulkStart" class="primary" type="button">Usar selecionados</button></div></div>`;document.body.appendChild(d);$('#bulkClose').onclick=()=>d.classList.remove('open');$('#bulkSearch').addEventListener('input',renderList);$('#bulkAll').onclick=()=>{const visible=$$('#bulkList .bulk-row').filter(x=>x.style.display!=='none');const all=visible.length&&visible.every(x=>x.querySelector('input').checked);visible.forEach(x=>x.querySelector('input').checked=!all);};$('#bulkStart').onclick=startBatch;return d;
  }

  function renderList(){
    const companyId=$('#deliveryCompany')?.value||'',q=($('#bulkSearch')?.value||'').trim().toLowerCase(),root=load();const rows=(root.workers||[]).filter(w=>w.companyId===companyId&&w.active!==false);
    const box=$('#bulkList');if(!box)return;box.innerHTML=rows.length?rows.map(w=>`<label class="bulk-row" data-search="${esc([w.name,w.cpf,w.reg,w.role,w.sector].join(' ').toLowerCase())}"><input type="checkbox" value="${esc(w.id)}"><span><b>${esc(w.name||'Colaborador')}</b><small>${esc([w.role,w.sector,w.cpf,w.reg].filter(Boolean).join(' • '))}</small></span></label>`).join(''):'<div style="padding:18px;color:#718682">Nenhum colaborador nesta empresa.</div>';if(q)$$('#bulkList .bulk-row').forEach(r=>r.style.display=r.dataset.search.includes(q)?'':'none');
  }

  function openBatch(){
    if(!canDeliver())return toast('Seu acesso não permite registrar entregas.');
    if(!$('#deliveryCompany')?.value)return toast('Selecione a empresa primeiro.');
    const d=modal();$('#bulkSearch').value='';renderList();d.classList.add('open');
  }

  function captureCommon(){
    return {companyId:$('#deliveryCompany').value,reason:$('#deliveryReason').value,responsible:$('#deliveryResponsible').value,notes:$('#deliveryNotes').value,items:$$('.delivery-item').map(row=>({epiId:row.querySelector('.item-epi')?.value||'',qty:row.querySelector('.item-qty')?.value||'1'})).filter(x=>x.epiId)};
  }
  function validateCommon(common){if(!common.items.length){toast('Adicione pelo menos um EPI antes de iniciar o lote.');return false;}return true;}

  function startBatch(){
    const ids=$$('#bulkList input[type="checkbox"]:checked').map(x=>x.value);if(ids.length<2)return toast('Selecione pelo menos 2 colaboradores.');const common=captureCommon();if(!validateCommon(common))return;
    batch={ids,index:0,common,startedAt:new Date().toISOString()};sessionStorage.setItem(SESSION_KEY,JSON.stringify(batch));$('#bulkDeliveryModal').classList.remove('open');lastDeliveryCount=(load().deliveries||[]).length;prepareCurrent();
  }

  function ensureProgress(){
    let p=$('#bulkProgress');if(!p){p=document.createElement('div');p.id='bulkProgress';p.className='bulk-progress';const card=$('#delivery .card');if(card)card.parentNode.insertBefore(p,card);p.addEventListener('click',e=>{if(e.target.closest('.bulk-cancel'))cancelBatch();});}return p;
  }
  function renderProgress(){const p=ensureProgress();if(!p)return;if(!batch){p.classList.remove('show');return;}const root=load(),w=(root.workers||[]).find(x=>x.id===batch.ids[batch.index]);p.innerHTML=`Entrega em lote: <b>${batch.index+1}/${batch.ids.length}</b> • Agora: ${esc(w?.name||'Colaborador')}<button class="bulk-cancel" type="button">Cancelar lote</button>`;p.classList.add('show');}

  function repopulateCommon(){
    const c=batch.common;$('#deliveryCompany').value=c.companyId;$('#deliveryCompany').dispatchEvent(new Event('change',{bubbles:true}));setTimeout(()=>{
      $('#deliveryReason').value=c.reason;$('#deliveryResponsible').value=c.responsible;$('#deliveryNotes').value=c.notes;const holder=$('#deliveryItems');if(holder)holder.innerHTML='';c.items.forEach((it,idx)=>{if(idx>0)$('#btnAddItem')?.click();else if(!$('.delivery-item'))$('#btnAddItem')?.click();const rows=$$('.delivery-item'),row=rows[idx]||rows[rows.length-1];if(row){row.querySelector('.item-epi').value=it.epiId;row.querySelector('.item-qty').value=it.qty;}});const sel=$('#deliveryWorker');if(sel){sel.value=batch.ids[batch.index];sel.dispatchEvent(new Event('change',{bubbles:true}));}renderProgress();},70);
  }

  function prepareCurrent(){if(!batch)return;repopulateCommon();setTimeout(()=>$('#deliveryWorker')?.scrollIntoView({behavior:'smooth',block:'center'}),120);}

  function cancelBatch(){batch=null;sessionStorage.removeItem(SESSION_KEY);renderProgress();toast('Entrega em lote cancelada.');}

  function afterSave(){
    if(!batch)return;setTimeout(()=>{
      const count=(load().deliveries||[]).length;if(count<=lastDeliveryCount)return;lastDeliveryCount=count;
      if(batch.index>=batch.ids.length-1){const total=batch.ids.length;batch=null;sessionStorage.removeItem(SESSION_KEY);renderProgress();toast(`Lote concluído: ${total} entregas registradas.`);return;}
      batch.index++;sessionStorage.setItem(SESSION_KEY,JSON.stringify(batch));const back=$('[data-go="delivery"]');if(!$('#delivery')?.classList.contains('active')){document.querySelector('[data-go="delivery"]')?.click();}setTimeout(prepareCurrent,90);
    },300);
  }

  function injectButton(){
    const box=$('#delivery .worker-search-box');if(!box||$('#btnBulkDelivery')||!canDeliver())return;const b=document.createElement('button');b.id='btnBulkDelivery';b.type='button';b.className='secondary bulk-btn';b.textContent='👥 Entrega em lote';b.onclick=openBatch;box.appendChild(b);
  }

  function restore(){try{batch=JSON.parse(sessionStorage.getItem(SESSION_KEY)||'null');}catch{batch=null;}if(batch){lastDeliveryCount=(load().deliveries||[]).length;renderProgress();}}
  function init(){styles();injectButton();restore();$('#btnSaveDelivery')?.addEventListener('click',afterSave,true);$('#deliveryCompany')?.addEventListener('change',()=>{if($('#bulkDeliveryModal')?.classList.contains('open'))renderList();});document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(injectButton,50));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();