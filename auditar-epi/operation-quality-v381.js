(()=>{
'use strict';
/* Gestão EPI v3.8.1: UI aditiva, sem escrita em banco, estoque ou autenticação. */
const PC=!!document.querySelector('.sidebar')&&!!document.querySelector('#syncStatus');
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=x=>String(x||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
function root(){try{const x=JSON.parse(localStorage.getItem(PC?'auditarEpiGestaoCacheV1':'auditarEpiV1')||'{}');return PC?(x.app||{}):x}catch(_){return {}}}
function data(){const r=root();for(const k of ['companies','workers','epis','deliveries'])if(!Array.isArray(r[k]))r[k]=[];return r}
function toast(m){const t=$('#toast');if(t){t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3300)}}
function allowed(k){return window.GestaoEpiModulesV380?.allowed?.(k)!==false}
function shell(){return PC?$('.main'):$('.app-shell')}
function fmt(d){try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(d))}catch(_){return String(d||'')}}
function navigate(id){const b=$(PC?'[data-pc-go="'+id+'"]':'[data-go="'+id+'"]')||(PC?$('.sidebar .nav[data-view="'+id+'"]'):null);if(b)b.click();return !!b}
function style(){
 if($('#opi381Style'))return;
 const s=document.createElement('style');s.id='opi381Style';
 s.textContent='.opi381{padding-bottom:105px}.opi381 h2{font-size:22px;margin:5px 0}.opi381 p{color:#5c7771;font-size:13px}.opi381-card{border:1px solid #d9e9e5;border-radius:15px;background:white;padding:14px;margin:10px 0}.opi381-filters{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}.opi381-filters label{display:grid;gap:6px;font-weight:700;font-size:13px}.opi381-filters input,.opi381-filters select{font-size:15px;min-height:43px}.opi381-result{background:#fff;border:1px solid #dfebe7;border-radius:13px;padding:12px;margin:9px 0;display:flex;align-items:center;justify-content:space-between;gap:11px}.opi381-result b{font-size:15px;display:block}.opi381-result small{font-size:12px;color:#647e78;display:block;margin-top:4px;overflow-wrap:anywhere}.opi381-btn{border:1px solid #b8d9cf;border-radius:10px;background:#e9f6f1;color:#0c6657;padding:10px 13px;font-size:14px;font-weight:800;cursor:pointer;min-height:42px}.opi381-btn.primary{background:#087d67;border-color:#087d67;color:white}.opi381-status{font-size:12px;color:#5e7972;padding:7px}.opi381-quick{display:flex;gap:8px;margin-bottom:12px}.opi381-quick button{flex:1}.opi381-evidence{font-size:11px;font-weight:700;color:#12644c;background:#e8f8f2;padding:3px 9px;border-radius:16px;display:inline-block;margin-top:5px}.opi381-evidence.missing{background:#fff2dd;color:#92631a}@media(max-width:750px){.opi381-filters{grid-template-columns:1fr}.opi381-result{display:block}.opi381-result button{width:100%;margin-top:10px}}body.pc380-text-large .opi381-result small{font-size:14px!important}body.pc380-text-comfortable .opi381-result small{font-size:13px!important}';
 document.head.appendChild(s);
}
function ensure(){
 if(!shell())return;
 if(!$('#opi381Proofs')){
  const s=document.createElement('section');s.id='opi381Proofs';s.className='view opi381'+(PC?' pc-modern-view':'');
  s.innerHTML='<h2>Central de comprovantes</h2><p>Histórico, evidências e acesso aos comprovantes já registrados.</p><div class="opi381-card opi381-filters"><label>Empresa<select id="opi381Company"></select></label><label>Buscar trabalhador ou EPI<input id="opi381Query" placeholder="Nome, matrícula, EPI ou CA"></label><label>Período<select id="opi381Period"><option value="0">Todos</option><option value="30">Últimos 30 dias</option><option value="90">Últimos 90 dias</option></select></label><label>Evidência<select id="opi381Evidence"><option value="all">Todas</option><option value="face">Biometria</option><option value="signature">Assinatura</option><option value="missing">Sem evidência</option></select></label></div><div class="opi381-status" id="opi381Count"></div><div id="opi381List"></div>';
  shell().appendChild(s);for(const id of ['#opi381Company','#opi381Query','#opi381Period','#opi381Evidence'])$(id).addEventListener('input',renderProofs);
 }
 if(!$('#opi381Express')){
  const s=document.createElement('section');s.id='opi381Express';s.className='view opi381'+(PC?' pc-modern-view':'');
  s.innerHTML='<h2>Entrega Expressa</h2><p>Identifique o trabalhador e continue no formulário de entrega já validado, sem pular assinatura ou biometria.</p><div class="opi381-card opi381-filters"><label>Empresa<select id="opi381ExpressCompany"></select></label><label>Buscar trabalhador<input id="opi381ExpressQuery" placeholder="Nome, CPF ou matrícula"></label></div><div id="opi381ExpressList"></div><p>Selecionar não entrega nem baixa estoque. Revise os itens antes de finalizar.</p>';
  shell().appendChild(s);for(const id of ['#opi381ExpressCompany','#opi381ExpressQuery'])$(id).addEventListener('input',renderExpress);
 }
 if(PC){
  const nav=$('.sidebar nav');if(nav){
   for(const [id,label] of [['opi381Proofs','🧾 Central de comprovantes'],['opi381Express','⚡ Entrega Expressa']]){
    if(nav.querySelector('[data-view="'+id+'"]'))continue;
    const b=document.createElement('button');b.className='nav pc-new';b.dataset.view=id;b.textContent=label;nav.appendChild(b);
   }
  }
  if($('#dashboard')&&!$('#opi381Quick')){$('#dashboard').insertAdjacentHTML('afterbegin','<div class="opi381-quick" id="opi381Quick"><button class="opi381-btn primary" data-opi381-open="opi381Express">⚡ Entrega Expressa</button><button class="opi381-btn" data-opi381-open="opi381Proofs">🧾 Comprovantes</button></div>')}
 }else{
  const grid=$('#moreFunctions .more323-grid')||$('#home .menu-grid');
  if(grid&&!grid.querySelector('[data-go="opi381Proofs"]')){
   const b=document.createElement('button');b.dataset.go='opi381Proofs';b.className=grid.classList.contains('more323-grid')?'more323-card':'menu-card';b.innerHTML='<span>🧾</span><b>Comprovantes</b><small>Consultar histórico e evidências</small>';grid.appendChild(b);
  }
  if(grid&&!grid.querySelector('[data-go="opi381Express"]')){
   const b=document.createElement('button');b.dataset.go='opi381Express';b.className=grid.classList.contains('more323-grid')?'more323-card':'menu-card';b.innerHTML='<span>⚡</span><b>Entrega Expressa</b><small>Selecionar trabalhador</small>';grid.appendChild(b);
  }
 }
}
function options(){const a=data(),preferred=PC?$('#globalCompany')?.value||'':'';return '<option value="">Todas as empresas</option>'+a.companies.filter(x=>!preferred||x.id===preferred).map(c=>'<option value="'+esc(c.id)+'">'+esc(c.name||'Empresa')+'</option>').join('')}
function show(id){
 if(!allowed(id==='opi381Proofs'?'history':'delivery'))return toast('Módulo indisponível para seu perfil.');
 ensure();$$('.view').forEach(v=>v.classList.toggle('active',v.id===id));
 if(PC){$$('.sidebar .nav').forEach(n=>n.classList.toggle('active',n.dataset.view===id));if($('#viewTitle'))$('#viewTitle').textContent=id==='opi381Proofs'?'Central de comprovantes':'Entrega Expressa'}
 else window.scrollTo(0,0);
 const select=$(id==='opi381Proofs'?'#opi381Company':'#opi381ExpressCompany');const old=select.value;select.innerHTML=options();if(old)select.value=old;
 if(id==='opi381Proofs')renderProofs();else renderExpress();
}
function evidence(d){if(d.biometricVerified||d.confirmationMethod==='face-biometric')return 'face';if(/^data:image\/(?:png|jpeg|webp);base64,/i.test(d.signature||''))return 'signature';return 'missing'}
function renderProofs(){
 const a=data(),box=$('#opi381List');if(!box)return;
 const comp=$('#opi381Company').value,query=norm($('#opi381Query').value),period=Number($('#opi381Period').value),ev=$('#opi381Evidence').value;
 const rows=a.deliveries.filter(d=>{
  const w=a.workers.find(x=>x.id===d.workerId)||{};
  const epis=(d.items||[]).map(i=>a.epis.find(e=>e.id===i.epiId)).filter(Boolean).map(e=>[e.name,e.ca].join(' ')).join(' ');
  return !d.cancelled&&(!comp||comp===d.companyId)&&(!period||Date.parse(d.createdAt||0)>=Date.now()-period*86400000)&&(ev==='all'||ev===evidence(d))&&(!query||norm([w.name,w.reg,epis].join(' ')).includes(query));
 }).sort((x,y)=>String(y.createdAt).localeCompare(String(x.createdAt))).slice(0,150);
 $('#opi381Count').textContent=rows.length+' registro(s) encontrados (máximo de 150 exibidos).';
 box.innerHTML=rows.length?rows.map(d=>{const w=a.workers.find(x=>x.id===d.workerId)||{},c=a.companies.find(x=>x.id===d.companyId)||{},ev=evidence(d);return '<div class="opi381-result"><div><b>'+esc(w.name||'Trabalhador')+'</b><small>'+esc(c.name||'Empresa')+' • '+esc(fmt(d.createdAt))+' • '+(d.items||[]).length+' EPI(s)</small><span class="opi381-evidence '+(ev==='missing'?'missing':'')+'">'+(ev==='face'?'Biometria facial':ev==='signature'?'Assinatura':'Evidência não identificada')+'</span></div><button class="opi381-btn" data-opi381-receipt="'+esc(d.id)+'">Ver comprovante</button></div>'}).join(''):'<div class="opi381-card">Nenhum comprovante encontrado.</div>';
}
function renderExpress(){
 const a=data(),box=$('#opi381ExpressList');if(!box)return;const c=$('#opi381ExpressCompany').value,q=norm($('#opi381ExpressQuery').value);
 const rows=a.workers.filter(w=>w.active!==false&&(!c||w.companyId===c)&&(!q||norm([w.name,w.cpf,w.reg].join(' ')).includes(q))).slice(0,40);
 box.innerHTML=rows.length?rows.map(w=>'<div class="opi381-result"><div><b>'+esc(w.name||'Trabalhador')+'</b><small>'+esc([w.role,w.sector,w.reg].filter(Boolean).join(' • '))+'</small></div><button class="opi381-btn primary" data-opi381-worker="'+esc(w.id)+'">Selecionar</button></div>').join(''):'<div class="opi381-card">Trabalhador não encontrado.</div>';
}
function receipt(id){
 if(!allowed('history'))return toast('Histórico não habilitado.');
 const b=document.createElement('button');b.type='button';b.hidden=true;
 if(PC)b.dataset.pcReceipt=id;else b.dataset.receipt=id;
 document.body.appendChild(b);try{b.click()}finally{b.remove()}
}
function express(id){
 if(!allowed('delivery'))return toast('Entregas desabilitadas.');
 const w=data().workers.find(x=>x.id===id);if(!w)return toast('Trabalhador não encontrado.');
 if(!navigate(PC?'newDeliveryPc':'delivery'))return toast('Formulário de entrega não disponível.');
 const company=$(PC?'#pcDeliveryCompany':'#deliveryCompany');
 if(company){company.value=w.companyId;company.dispatchEvent(new Event('change',{bubbles:true}))}
 setTimeout(()=>{
  const worker=$(PC?'#pcDeliveryWorker':'#deliveryWorker');
  if(worker){worker.value=w.id;worker.dispatchEvent(new Event('change',{bubbles:true}))}
  const search=$(PC?'#pcDeliverySearch':'#deliveryWorkerSearch');
  if(search){search.value=w.name||'';search.dispatchEvent(new Event('input',{bubbles:true}));if(worker)worker.value=w.id}
  toast('Trabalhador selecionado. Confirme EPIs, quantidades e evidência.');
 },250);
}
function precheck(){
 const save=$(PC?'#pcSaveDelivery':'#btnSaveDelivery');if(!save||$('#opi381Check'))return;
 const panel=document.createElement('div');panel.className='opi381-card';panel.innerHTML='<b>Conferência rápida</b><p>Confere quantidade, CA informado e EPI repetido; não altera dados.</p><button type="button" class="opi381-btn" id="opi381Check">🔎 Conferir itens</button><div class="opi381-status" id="opi381CheckResult"></div>';save.before(panel);
 $('#opi381Check').onclick=()=>{
  const a=data(),issues=[],counter={};
  $$(PC?'#pcDeliveryItems .pc-delivery-item':'#deliveryItems .delivery-item').forEach(row=>{
   const id=row.querySelector(PC?'.pc-item-epi':'.item-epi')?.value||'',n=Number(row.querySelector(PC?'.pc-item-qty':'.item-qty')?.value||0);
   if(!id||!Number.isFinite(n)||n<=0)issues.push('EPI ou quantidade inválida');
   if(id){counter[id]=(counter[id]||0)+1;const epi=a.epis.find(x=>x.id===id);if(epi&&!epi.ca)issues.push((epi.name||'EPI')+' sem CA informado: conferir se precisa de CA')}
  });
  if(Object.values(counter).some(n=>n>1))issues.push('Há EPI repetido na entrega');
  if(!$(PC?'#pcDeliveryWorker':'#deliveryWorker')?.value)issues.push('Selecione o trabalhador');
  $('#opi381CheckResult').textContent=issues.length?issues.join(' • '):'Conferência básica OK. Finalize pelo botão normal para verificar assinatura/biometria e estoque.';
 };
}
function syncHint(){
 const host=PC?$('.sidebar-foot'):$('#ux300Status');if(!host)return;
 let e=$('#opi381Sync');if(!e){e=document.createElement('div');e.id='opi381Sync';e.className='opi381-status';host.appendChild(e)}
 e.textContent=navigator.onLine?'Rede disponível. Confira o status de sincronização antes de considerar os dados enviados.':'Sem rede. Registros pendentes precisam sincronizar quando houver conexão.';
}
function bind(){
 document.addEventListener('click',e=>{
  const t=e.target.closest?.('[data-opi381-open],[data-opi381-receipt],[data-opi381-worker],[data-view="opi381Proofs"],[data-view="opi381Express"],[data-go="opi381Proofs"],[data-go="opi381Express"]');
  if(!t)return;e.preventDefault();e.stopImmediatePropagation();
  if(t.dataset.opi381Receipt)receipt(t.dataset.opi381Receipt);
  else if(t.dataset.opi381Worker)express(t.dataset.opi381Worker);
  else show(t.dataset.opi381Open||t.dataset.view||t.dataset.go);
 },true);
 window.addEventListener('online',syncHint);window.addEventListener('offline',syncHint);
 document.addEventListener('auditar-epi-data-changed',()=>{if($('#opi381Proofs')?.classList.contains('active'))renderProofs()});
 document.addEventListener('gestao-epi-sync-applied',()=>{syncHint();if($('#opi381Proofs')?.classList.contains('active'))renderProofs()});
}
function boot(){style();ensure();precheck();syncHint();bind();[550,1600,3200].forEach(t=>setTimeout(()=>{ensure();precheck();syncHint()},t))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();