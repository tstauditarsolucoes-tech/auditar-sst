(()=>{
'use strict';
const PC=!!document.querySelector('.sidebar')&&!!document.querySelector('#syncStatus');
const APP='auditarEpiV1',STOCK='auditarEpiStockV1',CACHE='auditarEpiGestaoCacheV1',REV='auditarEpiServerRevision',CTX='epiFlowDeliveryCtxV350';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
const now=()=>new Date().toISOString(),uid=p=>p+'_'+Date.now()+'_'+Math.random().toString(36).slice(2,8);
const FlowCore=window.GestaoEpiFlowCore||{};
let currentTab='dashboard',usersCache=[],deliveryBypassOnce=false,scanStream=null,scanFrame=0;

function blankApp(){return {companies:[],workers:[],epis:[],deliveries:[],auditLog:[]}}
function blankStock(){return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}}}
function readRoot(){
  try{
    if(PC){
      const r=JSON.parse(localStorage.getItem(CACHE)||'{}');r.app={...blankApp(),...(r.app||{})};r.stock={...blankStock(),...(r.stock||{})};
      for(const k of ['companies','workers','epis','deliveries','auditLog'])r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];
      r.stock.movements=Array.isArray(r.stock.movements)?r.stock.movements:[];r.stock.minimums=r.stock.minimums||{};return r;
    }
    const app={...blankApp(),...JSON.parse(localStorage.getItem(APP)||'{}')},stock={...blankStock(),...JSON.parse(localStorage.getItem(STOCK)||'{}')};
    for(const k of ['companies','workers','epis','deliveries','auditLog'])app[k]=Array.isArray(app[k])?app[k]:[];
    stock.movements=Array.isArray(stock.movements)?stock.movements:[];stock.minimums=stock.minimums||{};
    return {version:1,revision:Number(localStorage.getItem(REV)||0),updatedAt:now(),app,stock};
  }catch(_){return {version:1,revision:0,updatedAt:'',app:blankApp(),stock:blankStock()}}
}
function writeRoot(r){
  r.updatedAt=now();r.app.auditLog=Array.isArray(r.app.auditLog)?r.app.auditLog:[];
  if(PC)localStorage.setItem(CACHE,JSON.stringify(r));
  else{localStorage.setItem(APP,JSON.stringify(r.app));localStorage.setItem(STOCK,JSON.stringify(r.stock));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'epi-flow-v360'}}))}
}
function user(){return window.GestaoEpiAuth?.user?.()||null}
function tenant(){return window.GestaoEpiAuth?.tenant?.()||null}
function who(){const u=user();return {username:String(u?.username||''),name:String(u?.name||u?.username||''),role:String(u?.role||'')}}
function toast(m){const e=$('#toast');if(!e)return alert(m);e.textContent=m;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2800)}
async function syncNow(){
  try{
    const api=window.GestaoEpiAuth?.api;if(!api)return false;
    const root=readRoot(),res=await api('epi_sync_merge',{deviceId:window.GestaoEpiAuth?.deviceId?.()||'',client:PC?'gestao':'campo',payload:root});
    if(!res?.ok)throw new Error(res?.message||'Falha na sincronização.');
    const remote=res.payload||root;
    if(PC)localStorage.setItem(CACHE,JSON.stringify(remote));
    else{localStorage.setItem(APP,JSON.stringify(remote.app||{}));localStorage.setItem(STOCK,JSON.stringify(remote.stock||{}));localStorage.setItem(REV,String(res.revision||remote.revision||0));}
    document.dispatchEvent(new CustomEvent('gestao-epi-sync-applied'));return true;
  }catch(e){toast(e?.message||'Não foi possível sincronizar.');return false}
}
function records(type){return readRoot().app.auditLog.filter(x=>x&&x.type===type)}
function upsert(root,row){const a=root.app.auditLog,i=a.findIndex(x=>x.id===row.id);if(i>=0)a[i]=row;else a.unshift(row)}
function auths(root=readRoot()){return root.app.auditLog.filter(x=>x?.type==='epi_authorization')}
function profiles(root=readRoot()){return root.app.auditLog.filter(x=>x?.type==='epi_user_profile')}
function settings(root=readRoot(),companyId=''){return root.app.auditLog.find(x=>x?.type==='epi_flow_settings'&&x.companyId===companyId)||{id:'flowset_'+companyId,type:'epi_flow_settings',companyId,directDeliveryAllowed:true,defaultExpiryDays:5,reserveStock:true}}
function policy(root,companyId,epiId){return root.app.auditLog.find(x=>x?.type==='epi_policy'&&x.companyId===companyId&&x.epiId===epiId)||{authorizationRequired:false}}
function profile(){
  const u=user();if(!u)return 'none';if(u.role==='admin')return 'both';if(u.role==='consulta')return 'none';
  const p=profiles().find(x=>norm(x.username)===norm(u.username));return String(p?.profile||'both');
}
const canTst=()=>['tst','both'].includes(profile())||user()?.role==='admin';
const canWarehouse=()=>['warehouse','both'].includes(profile())||user()?.role==='admin';

function statusOf(a){return FlowCore.statusOf?FlowCore.statusOf(a):(a?.status||'pending')}
function effectiveEpi(item){return FlowCore.effectiveEpi?FlowCore.effectiveEpi(item):(item?.substitution?.status==='approved'&&item.substitution.toEpiId?item.substitution.toEpiId:item?.epiId)}
function remaining(item){return FlowCore.remaining?FlowCore.remaining(item):Math.max(0,Number(item?.qty||0)-Number(item?.deliveredQty||0))}
function stockBalance(root,c,e){return FlowCore.stockBalance?FlowCore.stockBalance(root.stock.movements,c,e):(root.stock.movements||[]).filter(m=>m.companyId===c&&m.epiId===e).reduce((s,m)=>s+Number(m.delta||0),0)}
function reservedQty(root,c,e,except=''){return FlowCore.reservedQty?FlowCore.reservedQty(auths(root),c,e,except):auths(root).filter(a=>a.id!==except&&a.companyId===c&&['pending','partial'].includes(statusOf(a))).reduce((sum,a)=>sum+(a.items||[]).reduce((q,i)=>effectiveEpi(i)===e?q+remaining(i):q,0),0)}
function available(root,c,e,except=''){return FlowCore.available?FlowCore.available(root.stock.movements,auths(root),c,e,except):stockBalance(root,c,e)-reservedQty(root,c,e,except)}
function companyName(root,id){return root.app.companies.find(x=>x.id===id)?.name||'Empresa'}
function workerName(root,id){return root.app.workers.find(x=>x.id===id)?.name||'Trabalhador'}
function epiName(root,id){const e=root.app.epis.find(x=>x.id===id);return e?e.name+(e.ca?' • CA '+e.ca:''):'EPI'}
function fmt(v,time=false){if(!v)return '—';try{return new Intl.DateTimeFormat('pt-BR',time?{dateStyle:'short',timeStyle:'short'}:{dateStyle:'short'}).format(new Date(v))}catch{return String(v)}}
function codeFor(id){return 'LIB-'+String(id||'').replace(/[^A-Za-z0-9]/g,'').slice(-8).toUpperCase()}

function installStyles(){
 if($('#flow350Style'))return;const s=document.createElement('style');s.id='flow350Style';s.textContent=`
.flow350-wrap{display:grid;gap:12px}.flow350-tabs{display:flex;gap:6px;overflow:auto}.flow350-tabs button{border:1px solid #cfe0dc;background:#fff;border-radius:999px;padding:8px 11px;font-weight:850;white-space:nowrap}.flow350-tabs button.active{background:#0f766e;color:#fff;border-color:#0f766e}.flow350-card{background:#fff;border:1px solid #dce8e5;border-radius:14px;padding:12px}.flow350-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.flow350-grid .full{grid-column:1/-1}.flow350-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.flow350-kpi{background:#fff;border:1px solid #dce8e5;border-radius:13px;padding:10px}.flow350-kpi strong{font-size:21px;color:#173d39}.flow350-kpi span{display:block;font-size:9px;color:#718480;text-transform:uppercase}.flow350-list{display:grid;gap:8px}.flow350-row{border:1px solid #e0e9e7;border-radius:12px;padding:10px;display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center}.flow350-row b{display:block}.flow350-row small{display:block;color:#6d817d;margin-top:3px;line-height:1.4}.flow350-actions{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.flow350-actions button,.flow350-btn{border:1px solid #cfe0dc;background:#fff;color:#285f58;border-radius:9px;padding:7px 9px;font-weight:850}.flow350-actions .primary,.flow350-btn.primary{background:#0f766e;color:#fff;border-color:#0f766e}.flow350-actions .danger{background:#fff0ee;color:#b42318;border-color:#f4c3bc}.flow350-pill{display:inline-block;border-radius:999px;padding:4px 7px;font-size:9px;font-weight:900}.flow350-pill.pending{background:#edf6ff;color:#24588d}.flow350-pill.partial{background:#fff8e6;color:#8a6418}.flow350-pill.delivered{background:#ecfdf3;color:#166534}.flow350-pill.expired,.flow350-pill.cancelled{background:#fff0ee;color:#b42318}.flow350-item{border:1px solid #e4ecea;border-radius:10px;padding:8px;margin-top:7px}.flow350-itemline{display:grid;grid-template-columns:1fr 90px 42px;gap:7px;align-items:end}.flow350-modal{position:fixed;inset:0;z-index:35000;background:rgba(9,38,35,.72);display:none;align-items:center;justify-content:center;padding:18px}.flow350-modal.open{display:flex}.flow350-modal-card{background:#fff;border-radius:18px;padding:18px;width:min(520px,100%);max-height:88vh;overflow:auto}.flow350-qr{text-align:center}.flow350-qr img{width:220px;height:220px;max-width:100%}.flow350-note{padding:9px;border-radius:10px;background:#f4f9f8;color:#5d7671;font-size:11px}.flow350-warn{padding:9px;border-radius:10px;background:#fff8e6;color:#8a6418;font-size:11px}.flow350-scan-video{width:100%;max-height:360px;border-radius:14px;background:#10201e}.flow350-report-table{width:100%;border-collapse:collapse;font-size:10px}.flow350-report-table th,.flow350-report-table td{border-bottom:1px solid #e3ecea;padding:8px;text-align:left;vertical-align:top}.flow350-report-table th{background:#f5f9f8;position:sticky;top:0}.flow350-report-scroll{overflow:auto;max-height:420px}.flow350-central-actions{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 0}.flow350-central-actions button{border:1px solid #cfe0dc;background:#fff;color:#0f766e;border-radius:9px;padding:8px 10px;font-weight:900}.flow350-central-actions .primary{background:#0f766e;color:#fff;border-color:#0f766e}@media(max-width:700px){.flow350-grid,.flow350-kpis{grid-template-columns:1fr 1fr}.flow350-row{grid-template-columns:1fr}.flow350-actions{justify-content:flex-start}.flow350-itemline{grid-template-columns:1fr 76px 38px}}`;document.head.appendChild(s)
}
function injectNavigation(){
 if(PC){const nav=$('.sidebar');if(nav&&!nav.querySelector('[data-view="epiFlowV350"]')){const b=document.createElement('button');b.className='nav';b.type='button';b.dataset.view='epiFlowV350';b.innerHTML='📦 <span>Liberação de EPI</span>';nav.appendChild(b)}}
 else{const grid=$('#moreFunctions .more323-grid');if(grid&&!grid.querySelector('[data-go="epiFlowV350"]')){const b=document.createElement('button');b.className='more323-card';b.dataset.go='epiFlowV350';b.innerHTML='<span>📦</span><b>Liberação de EPI</b><small>TST, almoxarifado e retirada</small>';grid.appendChild(b)}}
}
function injectView(){
 if($('#epiFlowV350'))return;
 const main=PC?$('.main'):($('.app-shell')||document.body),sec=document.createElement('section');sec.id='epiFlowV350';sec.className='view'+(PC?' pc-modern-view':'');
 sec.innerHTML=`${PC?'<div class="pc-modern-head"><div><h2>Liberação e Almoxarifado</h2><p>Autorizações, reservas, retirada e entrega direta.</p></div></div>':'<div class="view-head"><button class="back" data-go="moreFunctions">←</button><div><h2>Liberação e Almoxarifado</h2><p>Autorizações, reservas, retirada e entrega direta.</p></div></div>'}<div class="flow350-wrap"><div class="flow350-tabs" id="flow350Tabs"><button data-flowtab="dashboard">Painel</button><button data-flowtab="authorize">Liberar EPI</button><button data-flowtab="warehouse">Almoxarifado</button><button data-flowtab="report">Relatório</button><button data-flowtab="settings">Configuração</button></div><div id="flow350Content"></div></div>`;
 main.appendChild(sec);
 const modal=document.createElement('div');modal.id='flow350Modal';modal.className='flow350-modal';modal.innerHTML='<div class="flow350-modal-card"><div id="flow350ModalBody"></div><div style="margin-top:12px;text-align:right"><button class="flow350-btn" id="flow350ModalClose">Fechar</button></div></div>';document.body.appendChild(modal);$('#flow350ModalClose').onclick=()=>{stopScan();modal.classList.remove('open')};modal.onclick=e=>{if(e.target===modal){stopScan();modal.classList.remove('open')}};
 $$('#flow350Tabs [data-flowtab]').forEach(b=>b.onclick=()=>{currentTab=b.dataset.flowtab;render()});
}
function open(){
 injectNavigation();injectView();if(PC){$$('.view').forEach(v=>v.classList.toggle('active',v.id==='epiFlowV350'));$$('.sidebar .nav').forEach(n=>n.classList.toggle('active',n.dataset.view==='epiFlowV350'));if($('#viewTitle'))$('#viewTitle').textContent='Liberação de EPI';if($('#viewSub'))$('#viewSub').textContent='TST, almoxarifado e retirada.';}
 else{$$('.view').forEach(v=>v.classList.remove('active'));$('#epiFlowV350').classList.add('active');window.scrollTo(0,0)}
 render();
}
function tabsVisibility(){
 const p=profile();const admin=user()?.role==='admin';
 const map={dashboard:true,authorize:canTst(),warehouse:canWarehouse(),report:canTst()||admin,settings:admin};
 $$('#flow350Tabs [data-flowtab]').forEach(b=>b.style.display=map[b.dataset.flowtab]?'':'none');
 if(!map[currentTab])currentTab='dashboard';
}
function render(){if(!$('#epiFlowV350')?.classList.contains('active'))return;tabsVisibility();$('#flow350Tabs [data-flowtab]').forEach(b=>b.classList.toggle('active',b.dataset.flowtab===currentTab));if(currentTab==='authorize')renderAuthorize();else if(currentTab==='warehouse')renderWarehouse();else if(currentTab==='report')renderReport();else if(currentTab==='settings')renderSettings();else renderDashboard()}

function activeAuths(root=readRoot()){return auths(root).filter(a=>['pending','partial'].includes(statusOf(a)))}
function directReviews(root=readRoot()){return root.app.auditLog.filter(x=>x?.type==='epi_direct_delivery'&&x.reviewStatus!=='reviewed')}
function substitutionPending(root=readRoot()){const out=[];auths(root).forEach(a=>(a.items||[]).forEach((i,idx)=>{if(i.substitution?.status==='pending')out.push({a,i,idx})}));return out}
function renderDashboard(){
 const root=readRoot(),openA=activeAuths(root),expired=auths(root).filter(a=>statusOf(a)==='expired'),direct=directReviews(root),subs=substitutionPending(root);
 $('#flow350Content').innerHTML=`<div class="flow350-kpis"><div class="flow350-kpi"><strong>${openA.length}</strong><span>Aguardando retirada</span></div><div class="flow350-kpi"><strong>${direct.length}</strong><span>Entregas diretas para revisão</span></div><div class="flow350-kpi"><strong>${expired.length}</strong><span>Liberações vencidas</span></div><div class="flow350-kpi"><strong>${subs.length}</strong><span>Substituições pendentes</span></div></div><div class="flow350-card"><h3>Resumo operacional</h3><div class="flow350-list">${openA.slice(0,12).map(a=>authCard(root,a,true)).join('')||'<div class="flow350-note">Nenhuma liberação aguardando retirada.</div>'}</div></div>${canTst()?renderDirectReviewHtml(root,direct):''}${canTst()?renderSubstitutionHtml(root,subs):''}`;
 bindCommonActions();
}
function renderDirectReviewHtml(root,rows){return `<div class="flow350-card"><h3>Entregas diretas para revisão do TST</h3><div class="flow350-list">${rows.map(x=>`<div class="flow350-row"><div><b>${esc(workerName(root,x.workerId))}</b><small>${fmt(x.createdAt,true)} • ${esc(x.reason||'Entrega direta')} • ${(x.items||[]).map(i=>esc(epiName(root,i.epiId))+' x'+Number(i.qty||0)).join(', ')}</small></div><div class="flow350-actions"><button class="primary" data-flow-review="${esc(x.id)}">Marcar revisado</button></div></div>`).join('')||'<div class="flow350-note">Nenhuma entrega direta aguardando revisão.</div>'}</div></div>`}
function renderSubstitutionHtml(root,rows){return `<div class="flow350-card"><h3>Substituições solicitadas</h3><div class="flow350-list">${rows.map(x=>`<div class="flow350-row"><div><b>${esc(workerName(root,x.a.workerId))}</b><small>${esc(epiName(root,x.i.epiId))} → ${esc(epiName(root,x.i.substitution.toEpiId))}<br>${esc(x.i.substitution.reason||'Sem motivo informado')}</small></div><div class="flow350-actions"><button class="primary" data-flow-sub-approve="${esc(x.a.id)}|${x.idx}">Aprovar</button><button class="danger" data-flow-sub-reject="${esc(x.a.id)}|${x.idx}">Rejeitar</button></div></div>`).join('')||'<div class="flow350-note">Nenhuma substituição aguardando aprovação.</div>'}</div></div>`}


function reportDeliveryRows(root,since){
 const amap=new Map(auths(root).map(a=>[a.id,a]));
 return root.app.deliveries.filter(d=>d.cancelled!==true&&['authorized','direct'].includes(d.deliveryFlow)&&(!since||Date.parse(d.createdAt||0)>=since)).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||''))).map(d=>{
   const a=amap.get(d.authorizationId)||null;
   return {date:d.createdAt,worker:workerName(root,d.workerId),flow:d.deliveryFlow==='authorized'?'Com liberação TST':'Direta pelo almoxarifado',code:a?.code||'',authorizedBy:a?.authorizedBy?.name||a?.authorizedBy?.username||'',deliveredBy:d.warehouseDeliveredBy?.name||d.warehouseDeliveredBy?.username||d.responsible||'',units:(d.items||[]).reduce((s,i)=>s+Number(i.qty||0),0),reason:d.reason||''};
 });
}
function renderReport(){
 if(!canTst()&&user()?.role!=='admin')return renderDashboard();
 const root=readRoot(),days=Number(sessionStorage.getItem('epiFlowReportDaysV360')||30),since=days?Date.now()-days*86400000:0,stats=FlowCore.reportStats?FlowCore.reportStats(root,since):{authorizations:0,pending:0,partial:0,delivered:0,expired:0,cancelled:0,direct:0,directPendingReview:0,authorizedUnits:0,deliveredUnits:0,avgPickupHours:null},rows=reportDeliveryRows(root,since);
 const by=new Map();rows.forEach(r=>{const k=r.deliveredBy||'Não informado';by.set(k,(by.get(k)||0)+r.units)});const ranking=[...by.entries()].sort((a,b)=>b[1]-a[1]).slice(0,8);
 $('#flow350Content').innerHTML=`<div class="flow350-card"><div class="flow350-grid"><label>Período<select id="flowReportDays"><option value="7" ${days===7?'selected':''}>Últimos 7 dias</option><option value="30" ${days===30?'selected':''}>Últimos 30 dias</option><option value="90" ${days===90?'selected':''}>Últimos 90 dias</option><option value="0" ${days===0?'selected':''}>Todo o histórico</option></select></label><div class="flow350-actions" style="align-self:end"><button id="flowReportCsv">Baixar CSV</button><button class="primary" id="flowReportPrint">Imprimir / PDF</button></div></div></div><div class="flow350-kpis"><div class="flow350-kpi"><strong>${stats.authorizations}</strong><span>Liberações</span></div><div class="flow350-kpi"><strong>${stats.delivered}</strong><span>Concluídas</span></div><div class="flow350-kpi"><strong>${stats.direct}</strong><span>Entregas diretas</span></div><div class="flow350-kpi"><strong>${stats.directPendingReview}</strong><span>Diretas sem revisão</span></div></div><div class="flow350-card"><h3>Indicadores TST × Almoxarifado</h3><div class="flow350-grid"><div class="flow350-note">Pendentes: <b>${stats.pending}</b> • Parciais: <b>${stats.partial}</b> • Vencidas: <b>${stats.expired}</b> • Canceladas: <b>${stats.cancelled}</b></div><div class="flow350-note">Unidades liberadas: <b>${stats.authorizedUnits}</b> • retiradas: <b>${stats.deliveredUnits}</b> • tempo médio até retirada: <b>${stats.avgPickupHours==null?'—':stats.avgPickupHours.toFixed(1)+' h'}</b></div></div></div><div class="flow350-card"><h3>Quem realizou as entregas</h3><div class="flow350-list">${ranking.map(([name,units])=>`<div class="flow350-row"><div><b>${esc(name)}</b><small>Unidades entregues no período</small></div><strong>${units}</strong></div>`).join('')||'<div class="flow350-note">Sem entregas no período.</div>'}</div></div><div class="flow350-card"><h3>Movimentações</h3><div class="flow350-report-scroll"><table class="flow350-report-table"><thead><tr><th>Data</th><th>Trabalhador</th><th>Fluxo</th><th>Liberação</th><th>Liberado por</th><th>Entregue por</th><th>Qtd.</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(fmt(r.date,true))}</td><td>${esc(r.worker)}</td><td>${esc(r.flow)}</td><td>${esc(r.code||'—')}</td><td>${esc(r.authorizedBy||'—')}</td><td>${esc(r.deliveredBy||'—')}</td><td>${r.units}</td></tr>`).join('')||'<tr><td colspan="7">Sem movimentações no período.</td></tr>'}</tbody></table></div></div>`;
 $('#flowReportDays').onchange=e=>{sessionStorage.setItem('epiFlowReportDaysV360',e.target.value);renderReport()};
 $('#flowReportPrint').onclick=()=>window.print();$('#flowReportCsv').onclick=()=>downloadFlowReportCsv(rows,days);
}
function downloadFlowReportCsv(rows,days){
 const q=v=>'"'+String(v??'').replace(/"/g,'""')+'"',lines=[['Data','Trabalhador','Fluxo','Código da liberação','Liberado por','Entregue por','Quantidade','Motivo'].map(q).join(';')];
 rows.forEach(r=>lines.push([fmt(r.date,true),r.worker,r.flow,r.code,r.authorizedBy,r.deliveredBy,r.units,r.reason].map(q).join(';')));
 const blob=new Blob(['\ufeff'+lines.join('\n')],{type:'text/csv;charset=utf-8'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='relatorio-tst-almoxarifado-'+(days||'historico')+'d-'+new Date().toISOString().slice(0,10)+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1500);
}

function renderAuthorize(){
 if(!canTst())return renderDashboard();
 const r=readRoot(),companies=r.app.companies.filter(c=>c.active!==false),c0=companies[0]?.id||'';
 $('#flow350Content').innerHTML=`<div class="flow350-card"><h3>Nova liberação de EPI</h3><div class="flow350-grid"><label>Empresa<select id="flowAuthCompany">${companies.map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('')}</select></label><label>Trabalhador<select id="flowAuthWorker"></select></label><label>Motivo<select id="flowAuthReason"><option>Admissão</option><option>Troca periódica</option><option>Desgaste</option><option>Dano</option><option>Perda</option><option>Emergência</option><option>Entrega adicional</option><option>Reposição</option></select></label><label>Validade da liberação (dias)<input id="flowAuthDays" type="number" min="1" max="30" value="${Number(settings(r,c0).defaultExpiryDays||5)}"></label><label class="full">Observação<input id="flowAuthNote" placeholder="Opcional"></label></div><div style="margin-top:10px"><div style="display:flex;justify-content:space-between;align-items:center"><b>EPIs liberados</b><button class="flow350-btn" id="flowAddItem">＋ EPI</button></div><div id="flowAuthItems"></div></div><div class="flow350-actions" style="margin-top:12px"><button class="primary" id="flowCreateAuth">✓ Criar liberação</button></div></div><div class="flow350-card"><h3>Liberações recentes</h3><div class="flow350-list">${auths(r).slice().sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||''))).slice(0,20).map(a=>authCard(r,a,false)).join('')||'<div class="flow350-note">Nenhuma liberação criada.</div>'}</div></div>`;
 const fillWorkers=()=>{const c=$('#flowAuthCompany').value;$('#flowAuthWorker').innerHTML=r.app.workers.filter(w=>w.active!==false&&w.companyId===c).map(w=>`<option value="${esc(w.id)}">${esc(w.name)}${w.role?' • '+esc(w.role):''}</option>`).join('');$('#flowAuthDays').value=Number(settings(r,c).defaultExpiryDays||5);renderAuthItems()};
 $('#flowAuthCompany').onchange=fillWorkers;$('#flowAddItem').onclick=()=>addAuthItem();$('#flowCreateAuth').onclick=createAuthorization;fillWorkers();addAuthItem();bindCommonActions();
}
function renderAuthItems(){
 const box=$('#flowAuthItems');if(!box)return;box.querySelectorAll('.flow350-item').forEach(row=>refreshItemAvailability(row));
}
function addAuthItem(){
 const box=$('#flowAuthItems');if(!box)return;const r=readRoot(),c=$('#flowAuthCompany')?.value||'',row=document.createElement('div');row.className='flow350-item';row.innerHTML=`<div class="flow350-itemline"><label>EPI<select class="flow-auth-epi">${r.app.epis.filter(e=>e.active!==false).map(e=>`<option value="${esc(e.id)}">${esc(e.name)}${e.ca?' • CA '+esc(e.ca):''}</option>`).join('')}</select></label><label>Qtd.<input class="flow-auth-qty" type="number" min="1" value="1"></label><button type="button" class="flow350-btn flow-remove-item">×</button></div><small class="flow-item-stock"></small></div>`;box.appendChild(row);row.querySelector('.flow-remove-item').onclick=()=>{if(box.children.length>1)row.remove()};row.querySelector('.flow-auth-epi').onchange=()=>refreshItemAvailability(row);refreshItemAvailability(row)
}
function refreshItemAvailability(row){const r=readRoot(),c=$('#flowAuthCompany')?.value||'',e=row.querySelector('.flow-auth-epi')?.value||'',set=settings(r,c),physical=stockBalance(r,c,e),reserved=reservedQty(r,c,e),avail=physical-reserved;row.querySelector('.flow-item-stock').textContent=set.reserveStock!==false?`Saldo físico ${physical} • reservado ${reserved} • disponível ${avail}`:`Saldo físico ${physical} • reserva desativada`}
async function createAuthorization(){
 const r=readRoot(),companyId=$('#flowAuthCompany')?.value||'',workerId=$('#flowAuthWorker')?.value||'',days=Math.max(1,Math.min(30,Number($('#flowAuthDays')?.value||5))),items=$$('#flowAuthItems .flow350-item').map(row=>({epiId:row.querySelector('.flow-auth-epi')?.value||'',qty:Math.max(0,Number(row.querySelector('.flow-auth-qty')?.value||0)),deliveredQty:0})).filter(i=>i.epiId&&i.qty>0);
 if(!companyId||!workerId||!items.length)return toast('Informe empresa, trabalhador e pelo menos um EPI.');
 const set=settings(r,companyId);
 for(const i of items){if(set.reserveStock!==false&&i.qty>available(r,companyId,i.epiId))return toast('Estoque disponível insuficiente para '+epiName(r,i.epiId)+'.')}
 const id=uid('auth'),created=now(),exp=new Date(Date.now()+days*86400000).toISOString(),u=who(),row={id,type:'epi_authorization',code:codeFor(id),companyId,workerId,items,reason:$('#flowAuthReason')?.value||'',note:$('#flowAuthNote')?.value.trim()||'',status:'pending',authorizedBy:u,authorizedAt:created,createdAt:created,updatedAt:created,expiresAt:exp};
 upsert(r,row);writeRoot(r);await syncNow();toast('Liberação criada e enviada ao almoxarifado.');renderAuthorize()
}
function authCard(root,a,compact){
 const st=statusOf(a),items=(a.items||[]).map(i=>{const rem=remaining(i),eid=effectiveEpi(i);return `<div class="flow350-item"><b>${esc(epiName(root,eid))}</b><small>Liberado ${Number(i.qty||0)} • entregue ${Number(i.deliveredQty||0)} • restante ${rem}${i.substitution?.status==='pending'?' • substituição solicitada':''}</small></div>`}).join('');
 return `<div class="flow350-row"><div><b>${esc(workerName(root,a.workerId))} • ${esc(a.code||codeFor(a.id))}</b><small>${esc(companyName(root,a.companyId))} • ${esc(a.reason||'Liberação')} • validade ${fmt(a.expiresAt)}<br>Liberado por ${esc(a.authorizedBy?.name||a.authorizedBy?.username||'—')}</small>${compact?'':items}</div><div class="flow350-actions"><span class="flow350-pill ${st}">${st==='pending'?'Aguardando':st==='partial'?'Parcial':st==='delivered'?'Entregue':st==='expired'?'Vencida':'Cancelada'}</span>${canWarehouse()&&['pending','partial'].includes(st)?`<button class="primary" data-flow-deliver="${esc(a.id)}">Entregar</button><button data-flow-sub="${esc(a.id)}">Substituição</button>`:''}${canTst()&&['pending','partial'].includes(st)?`<button class="danger" data-flow-cancel="${esc(a.id)}">Cancelar</button>`:''}<button data-flow-qr="${esc(a.id)}">QR</button></div></div>`
}

function renderWarehouse(){
 if(!canWarehouse())return renderDashboard();
 const r=readRoot(),rows=activeAuths(r).sort((a,b)=>String(a.expiresAt||'').localeCompare(String(b.expiresAt||'')));
 $('#flow350Content').innerHTML=`<div class="flow350-card"><div class="flow350-grid"><label>Buscar liberação<input id="flowWarehouseSearch" placeholder="Nome, matrícula ou código LIB-..."></label><div style="display:flex;gap:7px;align-items:end"><button class="flow350-btn primary" id="flowDirectDelivery">＋ Entrega direta</button><button class="flow350-btn" id="flowScanCode">⌁ Ler código</button></div></div></div><div class="flow350-card"><h3>Fila do almoxarifado</h3><div id="flowWarehouseList" class="flow350-list"></div></div>`;
 const renderList=()=>{const q=norm($('#flowWarehouseSearch')?.value||'');$('#flowWarehouseList').innerHTML=rows.filter(a=>{const w=r.app.workers.find(x=>x.id===a.workerId)||{};return !q||[a.code,w.name,w.reg,w.cpf].some(v=>norm(v).includes(q))}).map(a=>authCard(r,a,false)).join('')||'<div class="flow350-note">Nenhuma liberação aguardando retirada.</div>';bindCommonActions()};
 $('#flowWarehouseSearch').oninput=renderList;$('#flowDirectDelivery').onclick=()=>startDirectDelivery();$('#flowScanCode').onclick=()=>scanCode();renderList()
}
function startDirectDelivery(){const p=profile();if(!canWarehouse())return;sessionStorage.setItem(CTX,JSON.stringify({mode:'direct',createdAt:now(),startedBy:who()}));openDelivery()}
function authorizationByCode(code){const r=readRoot();return auths(r).find(x=>norm(x.code)===norm(code)||norm(x.id)===norm(code))||null}
function acceptScannedCode(code){const a=authorizationByCode(code);if(!a)return toast('Liberação não encontrada.');if(!['pending','partial'].includes(statusOf(a)))return toast('Essa liberação não está disponível para retirada.');stopScan();$('#flow350Modal')?.classList.remove('open');startAuthorizedDelivery(a.id)}
function stopScan(){if(scanFrame)cancelAnimationFrame(scanFrame);scanFrame=0;if(scanStream){scanStream.getTracks().forEach(t=>t.stop());scanStream=null}}
function manualCode(){const code=prompt('Informe o código da liberação (LIB-...):');if(code)acceptScannedCode(code)}
async function scanCode(){
 if(!navigator.mediaDevices?.getUserMedia||typeof window.jsQR!=='function')return manualCode();
 const body=$('#flow350ModalBody');body.innerHTML='<div><h3>Ler QR da liberação</h3><p class="flow350-note">A leitura acontece localmente no aparelho. Nenhuma imagem é enviada.</p><video id="flowQrVideo" class="flow350-scan-video" playsinline muted></video><canvas id="flowQrCanvas" hidden></canvas><div class="flow350-actions" style="margin-top:10px"><button id="flowQrManual">Digitar código</button></div></div>';$('#flow350Modal').classList.add('open');$('#flowQrManual').onclick=manualCode;
 try{
   scanStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});const video=$('#flowQrVideo'),canvas=$('#flowQrCanvas'),ctx=canvas.getContext('2d',{willReadFrequently:true});video.srcObject=scanStream;await video.play();
   const tick=()=>{if(!scanStream||!video.videoWidth){scanFrame=requestAnimationFrame(tick);return}canvas.width=video.videoWidth;canvas.height=video.videoHeight;ctx.drawImage(video,0,0,canvas.width,canvas.height);const img=ctx.getImageData(0,0,canvas.width,canvas.height),qr=window.jsQR(img.data,img.width,img.height,{inversionAttempts:'dontInvert'});if(qr?.data)return acceptScannedCode(qr.data);scanFrame=requestAnimationFrame(tick)};tick();
 }catch(e){stopScan();toast('Não foi possível abrir a câmera. Use o código da liberação.');manualCode()}
}
function startAuthorizedDelivery(id){
 const r=readRoot(),a=auths(r).find(x=>x.id===id);if(!a)return;if(!['pending','partial'].includes(statusOf(a)))return toast('Liberação indisponível.');
 sessionStorage.setItem(CTX,JSON.stringify({mode:'authorized',authorizationId:id,companyId:a.companyId,workerId:a.workerId,startedAt:now(),startedBy:who()}));openDelivery(()=>prefillDelivery(a))
}
function openDelivery(cb){
 if(PC){const b=$('.sidebar .nav[data-view="newDeliveryPc"]');if(b)b.click();else{const v=$('#newDeliveryPc');if(v){$$('.view').forEach(x=>x.classList.toggle('active',x===v));v.classList.add('active')}}}
 else{const b=$('[data-go="delivery"]');if(b)b.click();else{$$('.view').forEach(v=>v.classList.remove('active'));$('#delivery')?.classList.add('active')}}
 setTimeout(()=>cb?.(),180)
}
function prefillDelivery(a){
 if(PC){
   const c=$('#pcDeliveryCompany');if(c){c.value=a.companyId;c.dispatchEvent(new Event('change',{bubbles:true}))}
   setTimeout(()=>{const w=$('#pcDeliveryWorker');if(w){w.value=a.workerId;w.dispatchEvent(new Event('change',{bubbles:true}))}const box=$('#pcDeliveryItems');if(box)box.innerHTML='';(a.items||[]).filter(i=>remaining(i)>0).forEach(i=>{$('#pcAddDeliveryItem')?.click();const row=$$('#pcDeliveryItems .pc-delivery-item').slice(-1)[0];if(row){row.querySelector('.pc-item-epi').value=effectiveEpi(i);row.querySelector('.pc-item-qty').value=remaining(i)}});if($('#pcDeliveryReason'))$('#pcDeliveryReason').value=[...$('#pcDeliveryReason').options].find(o=>norm(o.value||o.textContent).includes(norm(a.reason)))?.value||$('#pcDeliveryReason').value;if($('#pcDeliveryResponsible'))$('#pcDeliveryResponsible').value=who().name;},120)
 }else{
   const c=$('#deliveryCompany');if(c){c.value=a.companyId;c.dispatchEvent(new Event('change',{bubbles:true}))}
   setTimeout(()=>{const w=$('#deliveryWorker');if(w){w.value=a.workerId;w.dispatchEvent(new Event('change',{bubbles:true}))}const box=$('#deliveryItems');if(box)box.innerHTML='';(a.items||[]).filter(i=>remaining(i)>0).forEach(i=>{$('#btnAddItem')?.click();const row=$$('#deliveryItems .delivery-item').slice(-1)[0];if(row){row.querySelector('.item-epi').value=effectiveEpi(i);row.querySelector('.item-qty').value=remaining(i)}});if($('#deliveryReason')){const o=[...$('#deliveryReason').options].find(o=>norm(o.value||o.textContent).includes(norm(a.reason)));if(o)$('#deliveryReason').value=o.value}if($('#deliveryResponsible'))$('#deliveryResponsible').value=who().name;},120)
 }
}
function getDeliveryDraft(){
 if(PC)return {companyId:$('#pcDeliveryCompany')?.value||'',workerId:$('#pcDeliveryWorker')?.value||'',reason:$('#pcDeliveryReason')?.value||'',items:$$('#pcDeliveryItems .pc-delivery-item').map(r=>({epiId:r.querySelector('.pc-item-epi')?.value||'',qty:Number(r.querySelector('.pc-item-qty')?.value||0)})).filter(i=>i.epiId&&i.qty>0)};
 return {companyId:$('#deliveryCompany')?.value||'',workerId:$('#deliveryWorker')?.value||'',reason:$('#deliveryReason')?.value||'',items:$$('#deliveryItems .delivery-item').map(r=>({epiId:r.querySelector('.item-epi')?.value||'',qty:Number(r.querySelector('.item-qty')?.value||0)})).filter(i=>i.epiId&&i.qty>0)}
}
function validateAgainstRoot(root,draft,ctx){
 const set=settings(root,draft.companyId);
 if(ctx?.mode==='authorized'){
   const a=auths(root).find(x=>x.id===ctx.authorizationId),fit=FlowCore.deliveryFitsAuthorization?FlowCore.deliveryFitsAuthorization(a,draft):{ok:!!a};
   if(!fit.ok)return {ok:false,message:fit.reason==='QUANTIDADE_ACIMA_LIBERADA'?'Quantidade acima do restante liberado.':'A liberação mudou ou já foi atendida em outro dispositivo.'};
 }else{
   if(set.directDeliveryAllowed===false)return {ok:false,message:'Esta empresa exige liberação do TST antes da entrega.'};
   for(const di of draft.items){if(policy(root,draft.companyId,di.epiId).authorizationRequired)return {ok:false,message:epiName(root,di.epiId)+' exige liberação prévia do TST.'}}
 }
 return {ok:true};
}
async function acquireAuthorizationClaim(authorizationId,draft){
 const api=window.GestaoEpiAuth?.api;
 if(api){
   try{
     const server=await api('tenant_epi_authorization_claim',{authorizationId,items:draft.items,workerId:draft.workerId,companyId:draft.companyId,deviceId:window.GestaoEpiAuth?.deviceId?.()||''});
     if(server?.ok&&server.claimId)return {ok:true,claimId:server.claimId,mode:'server-atomic'};
     if(server?.code==='AUTHORIZATION_BUSY')return {ok:false,message:'Essa liberação está sendo atendida em outro dispositivo.'};
   }catch(_){}
 }
 const claimId='claim_'+authorizationId+'_'+Date.now()+'_'+Math.random().toString(36).slice(2,7),root=readRoot(),row={id:claimId,type:'epi_authorization_claim',authorizationId,companyId:draft.companyId,workerId:draft.workerId,items:draft.items,deviceId:window.GestaoEpiAuth?.deviceId?.()||'',requestedBy:who(),status:'claiming',createdAt:now(),updatedAt:now(),expiresAt:new Date(Date.now()+45000).toISOString()};
 upsert(root,row);writeRoot(root);if(!(await syncNow()))return {ok:false,message:'Não foi possível conferir a liberação no servidor.'};
 await new Promise(r=>setTimeout(r,650));await syncNow();const latest=readRoot(),winner=FlowCore.chooseClaimWinner?FlowCore.chooseClaimWinner(latest.app.auditLog,authorizationId):latest.app.auditLog.find(x=>x.id===claimId);
 if(!winner||winner.id!==claimId){const own=latest.app.auditLog.find(x=>x.id===claimId);if(own){own.status='lost';own.updatedAt=now();upsert(latest,own);writeRoot(latest);syncNow()}return {ok:false,message:'Essa liberação foi assumida por outro dispositivo. Atualize a fila.'}}
 return {ok:true,claimId,mode:'client-handshake'};
}
async function preflightAndResume(btn,draft,ctx){
 const original=btn.textContent;btn.disabled=true;btn.textContent='Conferindo…';let resumed=false;
 try{
   let concurrency='offline',claimId='';
   if(navigator.onLine){
     if(!(await syncNow()))throw new Error('Não foi possível atualizar os dados antes da entrega.');
     const check=validateAgainstRoot(readRoot(),draft,ctx);if(!check.ok)throw new Error(check.message);
     if(ctx?.mode==='authorized'){const claim=await acquireAuthorizationClaim(ctx.authorizationId,draft);if(!claim.ok)throw new Error(claim.message);claimId=claim.claimId||'';concurrency=claim.mode||'online'}
     else concurrency='online-preflight';
   }else{
     const check=validateAgainstRoot(readRoot(),draft,ctx);if(!check.ok)throw new Error(check.message);
     if(ctx?.mode==='authorized'&&!confirm('O aparelho está offline. Não é possível conferir se outro almoxarife iniciou esta retirada. Deseja continuar mesmo assim?'))return;
   }
   const fresh=getDeliveryDraft(),latestCheck=validateAgainstRoot(readRoot(),fresh,ctx);if(!latestCheck.ok)throw new Error(latestCheck.message);
   sessionStorage.setItem('epiFlowDeliveryCaptureV360',JSON.stringify({...ctx,...fresh,claimId,concurrencyCheck:concurrency,capturedAt:Date.now()}));
   deliveryBypassOnce=true;resumed=true;btn.disabled=false;btn.textContent=original;btn.click();setTimeout(finalizeDelivery,240);
 }catch(e){toast(e?.message||'Não foi possível liberar a entrega.')}
 finally{if(!resumed){btn.disabled=false;btn.textContent=original}}
}
function validateBeforeDelivery(e){
 const btn=e.target.closest?.(PC?'#pcSaveDelivery':'#btnSaveDelivery');if(!btn)return;
 if(deliveryBypassOnce){deliveryBypassOnce=false;return}
 if(user()?.role==='campo'&&!canWarehouse()){e.preventDefault();e.stopImmediatePropagation();return toast('Seu perfil operacional é TST. A entrega deve ser concluída pelo almoxarifado.')}
 if(!canWarehouse())return;
 const draft=getDeliveryDraft();if(!draft.companyId||!draft.workerId||!draft.items.length)return;
 let ctx;try{ctx=JSON.parse(sessionStorage.getItem(CTX)||'null')}catch{ctx=null}
 if(!ctx||ctx.mode!=='authorized'){ctx={mode:'direct',createdAt:now(),startedBy:who()};sessionStorage.setItem(CTX,JSON.stringify(ctx))}
 const check=validateAgainstRoot(readRoot(),draft,ctx);if(!check.ok){e.preventDefault();e.stopImmediatePropagation();return toast(check.message)}
 e.preventDefault();e.stopImmediatePropagation();preflightAndResume(btn,draft,ctx);
}
async function finalizeDelivery(){
 let cap;try{cap=JSON.parse(sessionStorage.getItem('epiFlowDeliveryCaptureV360')||'null')}catch{cap=null}if(!cap)return;
 const r=readRoot(),d=r.app.deliveries.slice().sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||''))).find(x=>x.companyId===cap.companyId&&x.workerId===cap.workerId&&Math.abs(Date.parse(x.createdAt||0)-cap.capturedAt)<15000);
 if(!d)return;
 const u=who();d.deliveryFlow=cap.mode==='authorized'?'authorized':'direct';d.authorizationId=cap.authorizationId||'';d.warehouseDeliveredBy=u;d.warehouseDeliveredAt=now();d.deliveryConcurrencyCheck=cap.concurrencyCheck||'unknown';d.deliveryClaimId=cap.claimId||'';d.updatedAt=now();
 if(cap.mode==='authorized'){
   const a=auths(r).find(x=>x.id===cap.authorizationId);if(a){(d.items||[]).forEach(di=>{const ai=(a.items||[]).find(i=>effectiveEpi(i)===di.epiId&&remaining(i)>0);if(ai)ai.deliveredQty=Math.min(Number(ai.qty||0),Number(ai.deliveredQty||0)+Number(di.qty||0))});a.status=statusOf(a);a.lastDeliveryId=d.id;a.lastDeliveredBy=u;a.lastDeliveredAt=now();a.updatedAt=now();upsert(r,a)}
 }else{
   upsert(r,{id:'direct_'+d.id,type:'epi_direct_delivery',deliveryId:d.id,companyId:d.companyId,workerId:d.workerId,items:d.items||[],reason:d.reason||'',reviewStatus:'pending',deliveredBy:u,createdAt:d.createdAt||now(),updatedAt:now()})
 }
 if(cap.claimId){const claim=r.app.auditLog.find(x=>x.id===cap.claimId);if(claim){claim.status='consumed';claim.deliveryId=d.id;claim.updatedAt=now();upsert(r,claim)}}writeRoot(r);document.dispatchEvent(new CustomEvent('epi-flow-delivery-finalized',{detail:{deliveryId:d.id}}));sessionStorage.removeItem('epiFlowDeliveryCaptureV360');sessionStorage.removeItem(CTX);await syncNow();if(PC)setTimeout(()=>location.reload(),350)
}

function renderSettings(){
 if(user()?.role!=='admin')return renderDashboard();
 const r=readRoot(),companies=r.app.companies.filter(c=>c.active!==false);
 $('#flow350Content').innerHTML=`<div class="flow350-card"><h3>Perfis operacionais</h3><p class="flow350-note">O perfil de segurança do login continua Admin/Campo/Consulta. Aqui você define apenas a função operacional do usuário Campo.</p><div id="flowUserProfiles" class="flow350-list">Carregando usuários…</div></div><div class="flow350-card"><h3>Política por empresa</h3><label>Empresa<select id="flowSetCompany">${companies.map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('')}</select></label><div id="flowCompanySettings" style="margin-top:10px"></div></div><div class="flow350-card"><h3>Política por EPI</h3><div id="flowEpiPolicies"></div></div>`;
 $('#flowSetCompany').onchange=renderCompanySettings;loadUsers();renderCompanySettings()
}
async function loadUsers(){
 const box=$('#flowUserProfiles');if(!box)return;try{const res=await window.GestaoEpiAuth?.api?.('tenant_list_users');if(!res?.ok)throw new Error(res?.message||'Falha');usersCache=res.users||[];const r=readRoot();box.innerHTML=usersCache.map(u=>{const p=profiles(r).find(x=>norm(x.username)===norm(u.username))?.profile||'both';return `<div class="flow350-row"><div><b>${esc(u.name||u.username)}</b><small>@${esc(u.username)} • ${esc(u.role)}</small></div><select data-flow-profile="${esc(u.username)}"><option value="tst" ${p==='tst'?'selected':''}>TST</option><option value="warehouse" ${p==='warehouse'?'selected':''}>Almoxarifado</option><option value="both" ${p==='both'?'selected':''}>TST + Almoxarifado</option></select></div>`}).join('');$$('[data-flow-profile]').forEach(s=>s.onchange=()=>saveProfile(s.dataset.flowProfile,s.value))}catch(e){box.innerHTML='<div class="flow350-warn">'+esc(e?.message||'Não foi possível carregar usuários.')+'</div>'}
}
async function saveProfile(username,p){
 const r=readRoot(),old=profiles(r).find(x=>norm(x.username)===norm(username)),row={id:old?.id||'profile_'+norm(username).replace(/[^a-z0-9]/g,'_'),type:'epi_user_profile',username,profile:p,updatedAt:now(),createdAt:old?.createdAt||now(),updatedBy:who()};upsert(r,row);writeRoot(r);await syncNow();toast('Perfil operacional atualizado.')
}
function renderCompanySettings(){
 const r=readRoot(),c=$('#flowSetCompany')?.value||'',set=settings(r,c);if(!c)return;
 $('#flowCompanySettings').innerHTML=`<div class="flow350-grid"><label>Entrega sem liberação<select id="flowDirectAllowed"><option value="1" ${set.directDeliveryAllowed!==false?'selected':''}>Permitida</option><option value="0" ${set.directDeliveryAllowed===false?'selected':''}>Bloqueada</option></select></label><label>Reserva de estoque<select id="flowReserveStock"><option value="1" ${set.reserveStock!==false?'selected':''}>Ativa</option><option value="0" ${set.reserveStock===false?'selected':''}>Desativada</option></select></label><label>Validade padrão da liberação (dias)<input id="flowDefaultDays" type="number" min="1" max="30" value="${Number(set.defaultExpiryDays||5)}"></label><div style="align-self:end"><button class="flow350-btn primary" id="flowSaveSettings">Salvar política</button></div></div>`;$('#flowSaveSettings').onclick=saveCompanySettings;
 $('#flowEpiPolicies').innerHTML='<div class="flow350-list">'+r.app.epis.filter(e=>e.active!==false).map(e=>{const p=policy(r,c,e.id);return `<div class="flow350-row"><div><b>${esc(e.name)}</b><small>${e.ca?'CA '+esc(e.ca):'Sem CA'}</small></div><select data-flow-epi-policy="${esc(e.id)}"><option value="0" ${!p.authorizationRequired?'selected':''}>Livre entrega</option><option value="1" ${p.authorizationRequired?'selected':''}>Exige liberação TST</option></select></div>`}).join('')+'</div>';$$('[data-flow-epi-policy]').forEach(s=>s.onchange=()=>saveEpiPolicy(c,s.dataset.flowEpiPolicy,s.value==='1'))
}
async function saveCompanySettings(){const r=readRoot(),c=$('#flowSetCompany')?.value||'',old=settings(r,c),row={...old,id:old.id||'flowset_'+c,type:'epi_flow_settings',companyId:c,directDeliveryAllowed:$('#flowDirectAllowed').value==='1',reserveStock:$('#flowReserveStock').value==='1',defaultExpiryDays:Math.max(1,Math.min(30,Number($('#flowDefaultDays').value||5))),updatedAt:now(),createdAt:old.createdAt||now(),updatedBy:who()};upsert(r,row);writeRoot(r);await syncNow();toast('Política da empresa salva.')}
async function saveEpiPolicy(c,e,required){const r=readRoot(),old=r.app.auditLog.find(x=>x.type==='epi_policy'&&x.companyId===c&&x.epiId===e),row={id:old?.id||'epipol_'+c+'_'+e,type:'epi_policy',companyId:c,epiId:e,authorizationRequired:required,updatedAt:now(),createdAt:old?.createdAt||now(),updatedBy:who()};upsert(r,row);writeRoot(r);await syncNow();toast(required?'EPI agora exige liberação do TST.':'EPI liberado para entrega direta.')}

function showQr(id){const r=readRoot(),a=auths(r).find(x=>x.id===id);if(!a)return;const code=a.code||codeFor(a.id),body=$('#flow350ModalBody');let data='';try{if(typeof window.qrcode==='function'){const qr=window.qrcode(0,'M');qr.addData(code);qr.make();data=qr.createDataURL(6,4)}}catch(_){}body.innerHTML=`<div class="flow350-qr"><h3>Liberação ${esc(code)}</h3><p>${esc(workerName(r,a.workerId))}</p>${data?'<img src="'+data+'" alt="QR da liberação gerado localmente">':'<div class="flow350-warn">QR indisponível neste build. Use o código abaixo.</div>'}<p><b>${esc(code)}</b></p><small>QR gerado localmente e offline. Ele contém somente o código da liberação, sem CPF ou dados sensíveis.</small></div>`;$('#flow350Modal').classList.add('open')}
async function cancelAuth(id){if(!confirm('Cancelar esta liberação?'))return;const r=readRoot(),a=auths(r).find(x=>x.id===id);if(!a)return;a.status='cancelled';a.cancelledAt=now();a.cancelledBy=who();a.updatedAt=now();upsert(r,a);writeRoot(r);await syncNow();render()}
function requestSub(id){
 const r=readRoot(),a=auths(r).find(x=>x.id===id);if(!a)return;const candidates=(a.items||[]).map((i,idx)=>({i,idx})).filter(x=>remaining(x.i)>0);if(!candidates.length)return toast('Nada pendente nesta liberação.');
 const base=candidates.length===1?candidates[0]:candidates[Math.max(0,Math.min(candidates.length-1,Number(prompt('Qual item deseja substituir? Informe 1 a '+candidates.length)||1)-1))];
 const term=prompt('Digite nome ou CA do EPI substituto:');if(!term)return;const matches=r.app.epis.filter(e=>e.active!==false&&[e.name,e.ca,e.model,e.size].some(v=>norm(v).includes(norm(term))));if(!matches.length)return toast('Nenhum EPI substituto encontrado.');const to=matches.length===1?matches[0]:matches[Math.max(0,Math.min(matches.length-1,Number(prompt(matches.slice(0,9).map((e,j)=>(j+1)+' - '+e.name+(e.ca?' • CA '+e.ca:'')).join('\n'))||1)-1))];if(!to)return;
 const reason=prompt('Motivo da substituição:')||'Indisponibilidade no almoxarifado';base.i.substitution={status:'pending',toEpiId:to.id,requestedAt:now(),requestedBy:who(),reason};a.updatedAt=now();upsert(r,a);writeRoot(r);syncNow().then(()=>{toast('Substituição enviada para aprovação do TST.');render()})
}
async function decideSub(key,approve){const [id,idxs]=String(key).split('|'),idx=Number(idxs),r=readRoot(),a=auths(r).find(x=>x.id===id),i=a?.items?.[idx];if(!i?.substitution)return;if(approve&&settings(r,a.companyId).reserveStock!==false&&remaining(i)>available(r,a.companyId,i.substitution.toEpiId,a.id))return toast('Estoque disponível insuficiente para aprovar o EPI substituto.');i.substitution.status=approve?'approved':'rejected';i.substitution.decidedAt=now();i.substitution.decidedBy=who();a.updatedAt=now();upsert(r,a);writeRoot(r);await syncNow();toast(approve?'Substituição aprovada.':'Substituição rejeitada.');render()}
async function reviewDirect(id){const r=readRoot(),x=r.app.auditLog.find(a=>a.id===id);if(!x)return;x.reviewStatus='reviewed';x.reviewedAt=now();x.reviewedBy=who();x.updatedAt=now();upsert(r,x);writeRoot(r);await syncNow();toast('Entrega direta revisada.');render()}

function bindCommonActions(){
 $$('[data-flow-deliver]').forEach(b=>b.onclick=()=>startAuthorizedDelivery(b.dataset.flowDeliver));
 $$('[data-flow-cancel]').forEach(b=>b.onclick=()=>cancelAuth(b.dataset.flowCancel));
 $$('[data-flow-qr]').forEach(b=>b.onclick=()=>showQr(b.dataset.flowQr));
 $$('[data-flow-sub]').forEach(b=>b.onclick=()=>requestSub(b.dataset.flowSub));
 $$('[data-flow-review]').forEach(b=>b.onclick=()=>reviewDirect(b.dataset.flowReview));
 $$('[data-flow-sub-approve]').forEach(b=>b.onclick=()=>decideSub(b.dataset.flowSubApprove,true));
 $$('[data-flow-sub-reject]').forEach(b=>b.onclick=()=>decideSub(b.dataset.flowSubReject,false));
}
function decorateCentral(){
 const r=readRoot(),open=activeAuths(r).length,direct=directReviews(r).length;
 const target=PC?$('#operationsPc340 .pc340-kpis'):$('#operationsCenterV340 .ops340-kpis');if(!target)return;let card=$('#flow350CentralKpi');if(!card){card=document.createElement('div');card.id='flow350CentralKpi';card.className=PC?'pc340-kpi':'ops340-kpi';target.appendChild(card)}card.innerHTML='<strong>'+open+'</strong><span>liberações pendentes'+(direct?' • '+direct+' direta(s) para revisão':'')+'</span>';card.style.cursor='pointer';card.title='Abrir fila de liberações';card.onclick=()=>{currentTab=canWarehouse()?'warehouse':'dashboard';open()};let actions=$('#flow350CentralActions');if(!actions){actions=document.createElement('div');actions.id='flow350CentralActions';actions.className='flow350-central-actions';target.insertAdjacentElement('afterend',actions)}actions.innerHTML=(canWarehouse()?'<button class="primary" id="flowCentralWarehouse">Abrir fila do almoxarifado</button>':'')+(canTst()?'<button id="flowCentralTst">Revisar entregas diretas</button>':'');$('#flowCentralWarehouse')?.addEventListener('click',()=>{currentTab='warehouse';open()});$('#flowCentralTst')?.addEventListener('click',()=>{currentTab='dashboard';open()});
}
function boot(){
 installStyles();injectNavigation();injectView();document.addEventListener('click',e=>{if(e.target.closest(PC?'.sidebar .nav[data-view="epiFlowV350"]':'[data-go="epiFlowV350"]')){e.preventDefault();open()}},true);
 document.addEventListener('click',validateBeforeDelivery,true);document.addEventListener('auditar-epi-data-changed',()=>{if($('#epiFlowV350')?.classList.contains('active'))setTimeout(render,120);setTimeout(decorateCentral,180)});document.addEventListener('gestao-epi-sync-applied',()=>{if($('#epiFlowV350')?.classList.contains('active'))setTimeout(render,120);setTimeout(decorateCentral,180)});
 [500,1500,3000].forEach(ms=>setTimeout(()=>{injectNavigation();injectView();decorateCentral()},ms));
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();