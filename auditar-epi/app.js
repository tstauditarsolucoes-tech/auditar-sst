(() => {
  const KEY = 'auditarEpiV1';
  const state = loadState();
  let signatureDirty = false;
  let currentReceiptId = null;

  function blankState(){ return {companies:[], workers:[], epis:[], deliveries:[]}; }
  function loadState(){
    try { return {...blankState(), ...JSON.parse(localStorage.getItem(KEY) || '{}')}; }
    catch { return blankState(); }
  }
  function saveState(){ localStorage.setItem(KEY, JSON.stringify(state)); refreshAll(); }
  function uid(prefix){ return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2,8)}`; }
  function esc(v=''){ return String(v).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
  function fmtDate(iso){ return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(iso)); }
  function toast(msg){ const el=$('#toast'); el.textContent=msg; el.classList.add('show'); setTimeout(()=>el.classList.remove('show'),2200); }
  function $(s, root=document){ return root.querySelector(s); }
  function $$(s, root=document){ return [...root.querySelectorAll(s)]; }

  function go(id){
    $$('.view').forEach(v=>v.classList.remove('active'));
    const target = document.getElementById(id); if(target) target.classList.add('active');
    if(id === 'delivery') prepareDelivery();
    if(id === 'history') renderHistory();
    window.scrollTo({top:0, behavior:'smooth'});
  }
  document.addEventListener('click', e => { const g=e.target.closest('[data-go]'); if(g) go(g.dataset.go); });

  function companyName(id){ return state.companies.find(x=>x.id===id)?.name || '—'; }
  function workerName(id){ return state.workers.find(x=>x.id===id)?.name || '—'; }
  function epiById(id){ return state.epis.find(x=>x.id===id); }
  function workerById(id){ return state.workers.find(x=>x.id===id); }
  function companyById(id){ return state.companies.find(x=>x.id===id); }

  function fillSelect(el, rows, placeholder, labelFn, selected=''){
    el.innerHTML = `<option value="">${placeholder}</option>` + rows.map(r=>`<option value="${r.id}" ${r.id===selected?'selected':''}>${esc(labelFn(r))}</option>`).join('');
  }

  function refreshAll(){
    $('#statCompanies').textContent=state.companies.length;
    $('#statWorkers').textContent=state.workers.length;
    $('#statEpis').textContent=state.epis.length;
    $('#statDeliveries').textContent=state.deliveries.length;
    fillSelect($('#workerCompany'), state.companies, 'Selecione a empresa', x=>x.name);
    fillSelect($('#workerFilterCompany'), state.companies, 'Todas as empresas', x=>x.name, $('#workerFilterCompany')?.value || '');
    fillSelect($('#deliveryCompany'), state.companies, 'Selecione a empresa', x=>x.name, $('#deliveryCompany')?.value || '');
    fillSelect($('#historyCompany'), state.companies, 'Todas as empresas', x=>x.name, $('#historyCompany')?.value || '');
    renderCompanies(); renderWorkers(); renderEpis(); renderDeliveryWorkers(); renderHistory();
    $$('.item-epi').forEach(sel => { const old=sel.value; fillSelect(sel,state.epis,'Selecione o EPI',x=>`${x.name}${x.ca?' • CA '+x.ca:''}`,old); });
  }

  $('#companyCnpj').addEventListener('input', e => {
    let v=e.target.value.replace(/\D/g,'').slice(0,14);
    v=v.replace(/^(\d{2})(\d)/,'$1.$2').replace(/^(\d{2})\.(\d{3})(\d)/,'$1.$2.$3').replace(/\.(\d{3})(\d)/,'.$1/$2').replace(/(\d{4})(\d)/,'$1-$2'); e.target.value=v;
  });
  $('#workerCpf').addEventListener('input', e => {
    let v=e.target.value.replace(/\D/g,'').slice(0,11); v=v.replace(/^(\d{3})(\d)/,'$1.$2').replace(/^(\d{3})\.(\d{3})(\d)/,'$1.$2.$3').replace(/\.(\d{3})(\d)/,'.$1-$2'); e.target.value=v;
  });

  $('#companyForm').addEventListener('submit', e=>{
    e.preventDefault(); const name=$('#companyName').value.trim(); if(!name) return;
    state.companies.push({id:uid('c'),name,cnpj:$('#companyCnpj').value.trim(),createdAt:new Date().toISOString()});
    e.target.reset(); saveState(); toast('Empresa salva.');
  });

  $('#workerForm').addEventListener('submit', e=>{
    e.preventDefault(); if(!$('#workerCompany').value) return toast('Selecione a empresa.');
    state.workers.push({id:uid('w'),companyId:$('#workerCompany').value,name:$('#workerName').value.trim(),cpf:$('#workerCpf').value.trim(),reg:$('#workerReg').value.trim(),role:$('#workerRole').value.trim(),sector:$('#workerSector').value.trim(),active:true,createdAt:new Date().toISOString()});
    const comp=$('#workerCompany').value; e.target.reset(); $('#workerCompany').value=comp; saveState(); toast('Colaborador salvo.');
  });

  $('#epiForm').addEventListener('submit', e=>{
    e.preventDefault(); state.epis.push({id:uid('e'),name:$('#epiName').value.trim(),ca:$('#epiCa').value.trim(),model:$('#epiModel').value.trim(),size:$('#epiSize').value.trim(),cycle:Number($('#epiCycle').value||0),createdAt:new Date().toISOString()});
    e.target.reset(); saveState(); toast('EPI salvo.');
  });

  function renderCompanies(){
    const el=$('#companyList');
    if(!state.companies.length) return el.innerHTML='<div class="empty">Nenhuma empresa cadastrada.</div>';
    el.innerHTML=state.companies.map(c=>`<div class="list-item"><div class="list-main"><b>${esc(c.name)}</b><small>${esc(c.cnpj||'CNPJ não informado')}</small></div><div class="list-actions"><button class="tiny delete" data-del-company="${c.id}">Excluir</button></div></div>`).join('');
  }
  function renderWorkers(){
    const el=$('#workerList'), comp=$('#workerFilterCompany').value;
    const rows=state.workers.filter(w=>!comp||w.companyId===comp);
    if(!rows.length) return el.innerHTML='<div class="empty">Nenhum colaborador encontrado.</div>';
    el.innerHTML=rows.map(w=>`<div class="list-item"><div class="list-main"><b>${esc(w.name)}</b><small>${esc(companyName(w.companyId))}${w.role?' • '+esc(w.role):''}${w.sector?' • '+esc(w.sector):''}</small></div><div class="list-actions"><button class="tiny delete" data-del-worker="${w.id}">Excluir</button></div></div>`).join('');
  }
  function renderEpis(){
    const el=$('#epiList'); if(!state.epis.length) return el.innerHTML='<div class="empty">Nenhum EPI cadastrado.</div>';
    el.innerHTML=state.epis.map(x=>`<div class="list-item"><div class="list-main"><b>${esc(x.name)}</b><small>${x.ca?'CA '+esc(x.ca):'CA não informado'}${x.model?' • '+esc(x.model):''}${x.size?' • Tam. '+esc(x.size):''}</small></div><div class="list-actions"><button class="tiny delete" data-del-epi="${x.id}">Excluir</button></div></div>`).join('');
  }
  document.addEventListener('click', e=>{
    const c=e.target.dataset.delCompany, w=e.target.dataset.delWorker, p=e.target.dataset.delEpi;
    if(c){ if(state.workers.some(x=>x.companyId===c)||state.deliveries.some(x=>x.companyId===c)) return toast('Empresa possui registros vinculados.'); state.companies=state.companies.filter(x=>x.id!==c); saveState(); }
    if(w){ if(state.deliveries.some(x=>x.workerId===w)) return toast('Colaborador possui entregas registradas.'); state.workers=state.workers.filter(x=>x.id!==w); saveState(); }
    if(p){ if(state.deliveries.some(d=>d.items.some(i=>i.epiId===p))) return toast('EPI já utilizado em entrega.'); state.epis=state.epis.filter(x=>x.id!==p); saveState(); }
  });
  $('#workerFilterCompany').addEventListener('change',renderWorkers);

  function renderDeliveryWorkers(){
    const comp=$('#deliveryCompany').value; const rows=state.workers.filter(w=>!comp||w.companyId===comp); const old=$('#deliveryWorker').value;
    fillSelect($('#deliveryWorker'),rows,'Selecione o colaborador',w=>`${w.name}${w.role?' • '+w.role:''}`,old);
  }
  $('#deliveryCompany').addEventListener('change',renderDeliveryWorkers);

  function addDeliveryItem(){
    const frag=$('#deliveryItemTemplate').content.cloneNode(true); const row=frag.querySelector('.delivery-item'); const sel=frag.querySelector('.item-epi');
    fillSelect(sel,state.epis,'Selecione o EPI',x=>`${x.name}${x.ca?' • CA '+x.ca:''}`);
    row.querySelector('.item-remove').addEventListener('click',()=>{ if($$('.delivery-item').length<=1) return toast('Mantenha pelo menos um EPI.'); row.remove(); });
    $('#deliveryItems').appendChild(frag);
  }
  $('#btnAddItem').addEventListener('click',addDeliveryItem);
  function prepareDelivery(){
    refreshAll(); if(!$('#deliveryItems').children.length) addDeliveryItem(); resizeCanvas(); clearSignature(false);
  }

  const canvas=$('#signature'), ctx=canvas.getContext('2d'); let drawing=false;
  function resizeCanvas(){
    const ratio=Math.max(window.devicePixelRatio||1,1), rect=canvas.getBoundingClientRect();
    const data=signatureDirty?canvas.toDataURL():null; canvas.width=Math.max(1,Math.floor(rect.width*ratio)); canvas.height=Math.floor(190*ratio); ctx.setTransform(ratio,0,0,ratio,0,0); ctx.lineCap='round'; ctx.lineJoin='round'; ctx.lineWidth=2.2; ctx.strokeStyle='#173d39';
    if(data){ const im=new Image(); im.onload=()=>ctx.drawImage(im,0,0,rect.width,190); im.src=data; }
  }
  function point(ev){ const r=canvas.getBoundingClientRect(), t=ev.touches?.[0]||ev; return {x:t.clientX-r.left,y:t.clientY-r.top}; }
  function start(ev){ ev.preventDefault(); drawing=true; const p=point(ev); ctx.beginPath(); ctx.moveTo(p.x,p.y); }
  function move(ev){ if(!drawing)return; ev.preventDefault(); const p=point(ev); ctx.lineTo(p.x,p.y); ctx.stroke(); signatureDirty=true; }
  function end(){ drawing=false; }
  ['pointerdown'].forEach(n=>canvas.addEventListener(n,start)); ['pointermove'].forEach(n=>canvas.addEventListener(n,move)); ['pointerup','pointerleave','pointercancel'].forEach(n=>canvas.addEventListener(n,end));
  function clearSignature(show=true){ ctx.clearRect(0,0,canvas.width,canvas.height); signatureDirty=false; if(show) toast('Assinatura limpa.'); }
  $('#btnClearSignature').addEventListener('click',()=>clearSignature()); window.addEventListener('resize',()=>setTimeout(resizeCanvas,100));

  $('#btnSaveDelivery').addEventListener('click',()=>{
    const companyId=$('#deliveryCompany').value, workerId=$('#deliveryWorker').value;
    if(!companyId) return toast('Selecione a empresa.'); if(!workerId) return toast('Selecione o colaborador.'); if(!signatureDirty) return toast('Colete a assinatura do colaborador.');
    const items=$$('.delivery-item').map(row=>({epiId:row.querySelector('.item-epi').value,qty:Number(row.querySelector('.item-qty').value||0)})).filter(x=>x.epiId&&x.qty>0);
    if(!items.length) return toast('Adicione pelo menos um EPI válido.');
    const delivery={id:uid('d'),companyId,workerId,reason:$('#deliveryReason').value,responsible:$('#deliveryResponsible').value.trim(),notes:$('#deliveryNotes').value.trim(),items,signature:canvas.toDataURL('image/png'),createdAt:new Date().toISOString()};
    state.deliveries.unshift(delivery); saveState(); currentReceiptId=delivery.id; resetDelivery(); showReceipt(delivery.id); toast('Entrega registrada com sucesso.');
  });
  function resetDelivery(){ $('#deliveryResponsible').value=''; $('#deliveryNotes').value=''; $('#deliveryReason').selectedIndex=0; $('#deliveryItems').innerHTML=''; clearSignature(false); }

  function renderHistory(){
    const el=$('#historyList'); if(!el) return; const comp=$('#historyCompany').value, q=$('#historySearch').value.trim().toLowerCase();
    const rows=state.deliveries.filter(d=>(!comp||d.companyId===comp)&&(!q||workerName(d.workerId).toLowerCase().includes(q)));
    if(!rows.length) return el.innerHTML='<div class="empty">Nenhuma entrega encontrada.</div>';
    el.innerHTML=rows.map(d=>`<div class="list-item"><div class="list-main"><b>${esc(workerName(d.workerId))}</b><small>${esc(companyName(d.companyId))} • ${fmtDate(d.createdAt)} • ${d.items.length} EPI(s)</small></div><div class="list-actions"><button class="tiny" data-receipt="${d.id}">Comprovante</button></div></div>`).join('');
  }
  $('#historyCompany').addEventListener('change',renderHistory); $('#historySearch').addEventListener('input',renderHistory);
  document.addEventListener('click',e=>{ if(e.target.dataset.receipt) showReceipt(e.target.dataset.receipt); });

  function showReceipt(id){
    const d=state.deliveries.find(x=>x.id===id); if(!d)return; currentReceiptId=id; const w=workerById(d.workerId), c=companyById(d.companyId);
    const itemRows=d.items.map(i=>{ const e=epiById(i.epiId)||{}; return `<tr><td>${esc(e.name||'EPI')}</td><td>${esc(e.ca||'—')}</td><td>${esc(e.model||'—')}</td><td>${i.qty}</td></tr>`; }).join('');
    $('#receiptContent').innerHTML=`
      <div class="receipt-head"><h1>COMPROVANTE DE ENTREGA DE EPI</h1><p>Registro eletrônico de fornecimento de Equipamento de Proteção Individual</p></div>
      <div class="receipt-meta">
        <div><b>Empresa</b><br>${esc(c?.name||'—')}<br><small>${esc(c?.cnpj||'')}</small></div>
        <div><b>Data e hora</b><br>${fmtDate(d.createdAt)}</div>
        <div><b>Colaborador</b><br>${esc(w?.name||'—')}<br><small>${w?.cpf?'CPF '+esc(w.cpf):''}</small></div>
        <div><b>Cargo / Setor</b><br>${esc(w?.role||'—')}${w?.sector?' / '+esc(w.sector):''}</div>
      </div>
      <table class="receipt-table"><thead><tr><th>EPI</th><th>CA</th><th>Modelo</th><th>Qtd.</th></tr></thead><tbody>${itemRows}</tbody></table>
      <div class="receipt-declaration"><b>Motivo:</b> ${esc(d.reason)}<br>${d.responsible?`<b>Responsável pela entrega:</b> ${esc(d.responsible)}<br>`:''}${d.notes?`<b>Observação:</b> ${esc(d.notes)}<br>`:''}<br>Declaro que recebi os equipamentos acima relacionados e fui informado de que devo utilizá-los de acordo com as orientações e procedimentos de segurança aplicáveis, conservar os equipamentos e comunicar necessidade de substituição quando houver perda de eficácia, dano ou outra condição que impeça o uso seguro.</div>
      <div class="receipt-sign"><img src="${d.signature}" alt="Assinatura do colaborador"><div class="sign-line">${esc(w?.name||'Colaborador')}<br>Assinatura do colaborador</div></div>`;
    go('receipt');
  }
  $('#btnPrint').addEventListener('click',()=>window.print());

  $('#btnBackup').addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=`auditar-epi-backup-${new Date().toISOString().slice(0,10)}.json`; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000); toast('Backup gerado.');
  });

  if('serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js').catch(()=>{});
  refreshAll(); resizeCanvas();
})();
