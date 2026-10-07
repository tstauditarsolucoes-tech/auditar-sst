(()=>{
'use strict';
const PC=!!document.querySelector('.sidebar')&&!!document.querySelector('#syncStatus');
const APP='auditarEpiV1',STOCK='auditarEpiStockV1',CACHE='auditarEpiGestaoCacheV1';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
function read(){
 try{
  if(PC){
   const r=JSON.parse(localStorage.getItem(CACHE)||'{}');r.app=r.app||{};for(const k of ['companies','workers','epis','deliveries','auditLog'])r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];return r;
  }
  const app=JSON.parse(localStorage.getItem(APP)||'{}');for(const k of ['companies','workers','epis','deliveries','auditLog'])app[k]=Array.isArray(app[k])?app[k]:[];return {app,stock:JSON.parse(localStorage.getItem(STOCK)||'{}')||{}};
 }catch(_){return {app:{companies:[],workers:[],epis:[],deliveries:[],auditLog:[]},stock:{}}}
}
function user(){return window.GestaoEpiAuth?.user?.()||{}}
function fmt(v,time=false){if(!v)return '—';try{return new Intl.DateTimeFormat('pt-BR',time?{dateStyle:'short',timeStyle:'short'}:{dateStyle:'short'}).format(new Date(v))}catch{return String(v)}}
function authById(root,id){return (root.app.auditLog||[]).find(x=>x?.type==='epi_authorization'&&x.id===id)}
function directByDelivery(root,id){return (root.app.auditLog||[]).find(x=>x?.type==='epi_direct_delivery'&&x.deliveryId===id)}
function worker(root,id){return root.app.workers.find(x=>x.id===id)||{}}
function company(root,id){return root.app.companies.find(x=>x.id===id)||{}}
function epi(root,id){return root.app.epis.find(x=>x.id===id)||{}}
function toast(m){const t=$('#toast');if(t){t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2500)}else alert(m)}

function traceData(root,d){
 const a=d.authorizationId?authById(root,d.authorizationId):null,dir=directByDelivery(root,d.id),mode=d.deliveryFlow==='authorized'?'Entrega com liberação do TST':d.deliveryFlow==='direct'?'Entrega direta do almoxarifado':'Entrega padrão';
 return {
  mode,
  code:a?.code||'—',
  authorizedBy:a?.authorizedBy?.name||a?.authorizedBy?.username||'—',
  authorizedAt:a?.authorizedAt||a?.createdAt||'',
  deliveredBy:d.warehouseDeliveredBy?.name||d.warehouseDeliveredBy?.username||d.registeredBy?.name||d.registeredBy?.username||d.responsible||'—',
  deliveredAt:d.warehouseDeliveredAt||d.createdAt||'',
  reviewedBy:dir?.reviewedBy?.name||dir?.reviewedBy?.username||'—',
  reviewedAt:dir?.reviewedAt||'',
  reviewStatus:dir?.reviewStatus||''
 };
}
function decorateReceipt(id){
 const root=read(),d=root.app.deliveries.find(x=>x.id===id);if(!d)return;
 const target=PC?$('#pcReceiptPaper'):$('#receiptContent');if(!target)return;
 target.querySelector('.flow360-trace')?.remove();
 const t=traceData(root,d),box=document.createElement('div');box.className='flow360-trace';
 box.innerHTML=`<div class="flow360-trace-title">Rastreabilidade da entrega</div><div class="flow360-trace-grid"><div><b>Tipo de entrega</b><br>${esc(t.mode)}</div><div><b>Código da liberação</b><br>${esc(t.code)}</div><div><b>Liberado por</b><br>${esc(t.authorizedBy)}${t.authorizedAt?'<br><small>'+esc(fmt(t.authorizedAt,true))+'</small>':''}</div><div><b>Entregue por</b><br>${esc(t.deliveredBy)}${t.deliveredAt?'<br><small>'+esc(fmt(t.deliveredAt,true))+'</small>':''}</div>${d.deliveryFlow==='direct'?'<div><b>Revisão do TST</b><br>'+esc(t.reviewStatus==='reviewed'?'Revisada':'Pendente')+'</div><div><b>Revisado por</b><br>'+esc(t.reviewedBy)+(t.reviewedAt?'<br><small>'+esc(fmt(t.reviewedAt,true))+'</small>':'')+'</div>':''}</div>`;
 const sign=target.querySelector('.receipt-sign,.pc-receipt-sign');if(sign)target.insertBefore(box,sign);else target.appendChild(box);
}
function currentReceiptIdFromClick(e){
 const b=e.target.closest?.('[data-receipt],[data-pc-receipt]');return b?.dataset?.receipt||b?.dataset?.pcReceipt||'';
}
function bindReceipt(){
 document.addEventListener('click',e=>{const id=currentReceiptIdFromClick(e);if(id)setTimeout(()=>decorateReceipt(id),60)},false);
 document.addEventListener('auditar-epi-data-changed',()=>{const r=read(),id=r.app.deliveries[0]?.id;if((PC?$('#receiptDetailPc'):$('#receipt'))?.classList.contains('active')&&id)setTimeout(()=>decorateReceipt(id),80)});
}

function qrDataUrl(value){
 if(typeof window.qrcode!=='function')throw new Error('Gerador QR local indisponível.');
 const qr=window.qrcode(0,'M');qr.addData(String(value));qr.make();return qr.createDataURL(6,4);
}
function openQrLocal(id){
 const root=read(),a=authById(root,id);if(!a)return toast('Liberação não encontrada.');
 const code=a.code||id,modal=$('#flow350Modal'),body=$('#flow350ModalBody');if(!modal||!body)return;
 try{
  body.innerHTML=`<div class="flow350-qr"><h3>Liberação ${esc(code)}</h3><p>${esc(worker(root,a.workerId).name||'Trabalhador')}</p><img src="${qrDataUrl(code)}" alt="QR da liberação"><p><b>${esc(code)}</b></p><small>QR gerado localmente no aparelho. Nenhum dado é enviado para serviço externo.</small></div>`;modal.classList.add('open');
 }catch(e){toast(e.message||'Falha ao gerar QR local.')}
}
let scanStream=null,scanTimer=null;
function stopScan(){if(scanTimer){clearInterval(scanTimer);scanTimer=null}if(scanStream){scanStream.getTracks().forEach(t=>t.stop());scanStream=null}}
function findAuthorizationByCode(code){
 const root=read(),q=norm(code);return (root.app.auditLog||[]).find(x=>x?.type==='epi_authorization'&&(norm(x.code)===q||norm(x.id)===q));
}
function openAuthorizationInWarehouse(a){
 const flowNav=PC?$('.sidebar .nav[data-view="epiFlowV350"]'):$('[data-go="epiFlowV350"]');flowNav?.click();
 setTimeout(()=>{const tab=$('[data-flowtab="warehouse"]');tab?.click();setTimeout(()=>{const search=$('#flowWarehouseSearch');if(search){search.value=a.code||a.id;search.dispatchEvent(new Event('input',{bubbles:true}));search.focus()}},80)},100);
}
async function scanQrCamera(){
 if(!('BarcodeDetector'in window)){const code=prompt('A leitura por câmera não é suportada neste aparelho. Informe o código LIB-...:');if(!code)return;const a=findAuthorizationByCode(code);return a?openAuthorizationInWarehouse(a):toast('Liberação não encontrada.')}
 const modal=$('#flow350Modal'),body=$('#flow350ModalBody');if(!modal||!body)return;
 body.innerHTML='<h3>Ler QR da liberação</h3><video id="flow360QrVideo" autoplay playsinline style="width:100%;border-radius:12px;background:#111;min-height:220px"></video><p class="flow350-note">Aponte a câmera para o QR da liberação.</p>';modal.classList.add('open');
 try{
  scanStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});const video=$('#flow360QrVideo');video.srcObject=scanStream;await video.play();
  const detector=new BarcodeDetector({formats:['qr_code']});
  scanTimer=setInterval(async()=>{try{const rows=await detector.detect(video);const raw=rows?.[0]?.rawValue;if(!raw)return;const a=findAuthorizationByCode(raw);if(!a)return;stopScan();modal.classList.remove('open');openAuthorizationInWarehouse(a)}catch(_){}},450);
 }catch(e){stopScan();body.innerHTML='<div class="flow350-warn">Não foi possível abrir a câmera. Use o código da liberação ou um leitor externo.</div>'}
}
function bindQr(){
 document.addEventListener('click',e=>{
  const q=e.target.closest?.('[data-flow-qr]');if(q){e.preventDefault();e.stopImmediatePropagation();openQrLocal(q.dataset.flowQr);return}
  if(e.target.closest?.('#flowScanCode')){e.preventDefault();e.stopImmediatePropagation();scanQrCamera();return}
  if(e.target.closest?.('#flow350ModalClose'))stopScan();
 },true);
 const modal=$('#flow350Modal');modal?.addEventListener('click',e=>{if(e.target===modal)stopScan()});
}

function openFlowTab(tab){
 const n=PC?$('.sidebar .nav[data-view="epiFlowV350"]'):$('[data-go="epiFlowV350"]');n?.click();setTimeout(()=>$('[data-flowtab="'+tab+'"]')?.click(),100);
}
function decorateCentral(){
 const card=$('#flow350CentralKpi');if(card&&!card.querySelector('.flow360-open')){card.style.cursor='pointer';const b=document.createElement('button');b.className='flow360-open';b.textContent='Abrir fila';b.onclick=e=>{e.stopPropagation();openFlowTab('warehouse')};card.appendChild(b);card.onclick=()=>openFlowTab('warehouse')}
 const body=PC?$('#operationsPc340 .pc340-card'):$('#operationsCenterV340 .ops340-card');if(body&&!body.querySelector('.flow360-quick')){const div=document.createElement('div');div.className='flow360-quick';div.innerHTML='<button data-flow360-tab="warehouse">📦 Fila do almoxarifado</button><button data-flow360-tab="authorize">✅ Liberar EPI</button><button data-flow360-report>📊 Relatório TST × Almoxarifado</button>';body.appendChild(div)}
}
function bindCentral(){
 document.addEventListener('click',e=>{const b=e.target.closest?.('[data-flow360-tab]');if(b){e.preventDefault();openFlowTab(b.dataset.flow360Tab)}if(e.target.closest?.('[data-flow360-report]')){e.preventDefault();openReport()}},true);
 [700,1600,3000].forEach(ms=>setTimeout(decorateCentral,ms));document.addEventListener('auditar-epi-data-changed',()=>setTimeout(decorateCentral,100));document.addEventListener('gestao-epi-sync-applied',()=>setTimeout(decorateCentral,100));
}

function reportData(){
 const root=read(),auths=(root.app.auditLog||[]).filter(x=>x?.type==='epi_authorization'),directs=(root.app.auditLog||[]).filter(x=>x?.type==='epi_direct_delivery'),delivered=auths.filter(a=>String(a.status)==='delivered'),partial=auths.filter(a=>String(a.status)==='partial'),expired=auths.filter(a=>a.expiresAt&&Date.now()>Date.parse(a.expiresAt)&&!['delivered','cancelled'].includes(a.status)),cancelled=auths.filter(a=>a.status==='cancelled');
 const lead=delivered.map(a=>{const end=a.lastDeliveredAt?Date.parse(a.lastDeliveredAt):0,start=Date.parse(a.authorizedAt||a.createdAt||0);return end&&start?Math.max(0,end-start):null}).filter(x=>x!=null);
 const avg=lead.length?Math.round(lead.reduce((s,x)=>s+x,0)/lead.length/60000):0;
 const countBy=(rows,get)=>{const m=new Map();rows.forEach(x=>{const k=get(x)||'Não informado';m.set(k,(m.get(k)||0)+1)});return [...m.entries()].sort((a,b)=>b[1]-a[1])};
 return {root,auths,directs,delivered,partial,expired,cancelled,avg,
  byTst:countBy(auths,a=>a.authorizedBy?.name||a.authorizedBy?.username),
  byWarehouse:countBy(root.app.deliveries.filter(d=>d.deliveryFlow),d=>d.warehouseDeliveredBy?.name||d.warehouseDeliveredBy?.username||d.responsible),
  directReviewed:directs.filter(x=>x.reviewStatus==='reviewed').length
 };
}
function openReport(){
 const n=PC?$('.sidebar .nav[data-view="epiFlowV350"]'):$('[data-go="epiFlowV350"]');n?.click();
 setTimeout(()=>{const tabs=$('#flow350Tabs');if(tabs&&!tabs.querySelector('[data-flowtab="report360"]')){const b=document.createElement('button');b.dataset.flowtab='report360';b.textContent='Relatório';tabs.appendChild(b)}renderReport()},120);
}
function renderReport(){
 const d=reportData(),box=$('#flow350Content');if(!box)return;$$('#flow350Tabs [data-flowtab]').forEach(b=>b.classList.toggle('active',b.dataset.flowtab==='report360'));
 box.innerHTML=`<div class="flow360-report-actions"><button id="flow360PrintReport">🖨️ Imprimir / PDF</button><button id="flow360CsvReport">⇩ Exportar CSV</button></div><div id="flow360ReportPrint"><div class="flow350-kpis"><div class="flow350-kpi"><strong>${d.auths.length}</strong><span>Liberações</span></div><div class="flow350-kpi"><strong>${d.delivered.length}</strong><span>Concluídas</span></div><div class="flow350-kpi"><strong>${d.directs.length}</strong><span>Entregas diretas</span></div><div class="flow350-kpi"><strong>${d.avg}</strong><span>Min. médios até retirada</span></div></div><div class="flow350-card"><h3>Situação das liberações</h3><table class="flow360-table"><tr><th>Concluídas</th><th>Parciais</th><th>Vencidas</th><th>Canceladas</th><th>Diretas revisadas</th></tr><tr><td>${d.delivered.length}</td><td>${d.partial.length}</td><td>${d.expired.length}</td><td>${d.cancelled.length}</td><td>${d.directReviewed}/${d.directs.length}</td></tr></table></div><div class="flow350-card"><h3>Liberações por TST</h3>${rankHtml(d.byTst)}</div><div class="flow350-card"><h3>Entregas por almoxarifado</h3>${rankHtml(d.byWarehouse)}</div><div class="flow350-card"><h3>Últimas liberações</h3><div class="flow350-list">${d.auths.slice().sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||''))).slice(0,20).map(a=>'<div class="flow350-row"><div><b>'+esc(worker(d.root,a.workerId).name||'Trabalhador')+' • '+esc(a.code||a.id)+'</b><small>'+esc(a.reason||'Liberação')+' • '+fmt(a.createdAt,true)+' • status '+esc(a.status||'pending')+'</small></div></div>').join('')||'<div class="flow350-note">Sem registros.</div>'}</div></div></div>`;
 $('#flow360PrintReport').onclick=()=>window.print();$('#flow360CsvReport').onclick=()=>exportReportCsv(d);
}
function rankHtml(rows){return rows.length?'<div class="flow350-list">'+rows.map(([n,c])=>'<div class="flow350-row"><div><b>'+esc(n)+'</b><small>'+c+' registro(s)</small></div></div>').join('')+'</div>':'<div class="flow350-note">Sem dados no período.</div>'}
function exportReportCsv(d){
 const lines=[['Indicador','Valor'],['Liberações',d.auths.length],['Concluídas',d.delivered.length],['Parciais',d.partial.length],['Vencidas',d.expired.length],['Canceladas',d.cancelled.length],['Entregas diretas',d.directs.length],['Diretas revisadas',d.directReviewed],['Tempo médio até retirada (min)',d.avg],[],['Liberações por TST','Quantidade'],...d.byTst,[],['Entregas por almoxarifado','Quantidade'],...d.byWarehouse];
 const csv=lines.map(r=>r.map(v=>'"'+String(v??'').replace(/"/g,'""')+'"').join(';')).join('\n'),blob=new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='relatorio-tst-almoxarifado-'+new Date().toISOString().slice(0,10)+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)
}
function bindReportTab(){
 document.addEventListener('click',e=>{const b=e.target.closest?.('[data-flowtab="report360"]');if(b){e.preventDefault();e.stopImmediatePropagation();renderReport()}},true);
}

function style(){
 if($('#flow360Style'))return;const s=document.createElement('style');s.id='flow360Style';s.textContent=`
.flow360-trace{margin:14px 0;border:1px solid #cfe0dc;border-radius:10px;padding:10px;font-size:11px}.flow360-trace-title{font-weight:900;margin-bottom:8px;color:#173d39}.flow360-trace-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.flow360-trace-grid>div{border:1px solid #e3ecea;padding:8px;border-radius:8px}.flow360-open{display:block;margin-top:7px;border:0;border-radius:8px;padding:6px 9px;font-weight:900;background:#0f766e;color:#fff}.flow360-quick{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.flow360-quick button,.flow360-report-actions button{border:1px solid #cfe0dc;background:#fff;border-radius:9px;padding:8px 10px;font-weight:850;color:#285f58}.flow360-report-actions{display:flex;gap:8px;justify-content:flex-end;margin-bottom:10px}.flow360-table{width:100%;border-collapse:collapse;font-size:11px}.flow360-table th,.flow360-table td{border:1px solid #dce8e5;padding:8px;text-align:center}@media(max-width:700px){.flow360-trace-grid{grid-template-columns:1fr}}@media print{.flow360-report-actions,#flow350Tabs,.view-head,.pc-modern-head,.sidebar,.topbar{display:none!important}#flow360ReportPrint,#flow360ReportPrint *{visibility:visible!important}#flow360ReportPrint{position:absolute;inset:0;padding:10mm;background:#fff}}
`;document.head.appendChild(s)
}
function boot(){style();bindReceipt();bindQr();bindCentral();bindReportTab()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();