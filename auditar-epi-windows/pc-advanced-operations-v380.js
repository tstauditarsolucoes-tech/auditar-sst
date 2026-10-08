(()=>{
'use strict';
const PC=!!document.querySelector('.sidebar')&&!!document.querySelector('#syncStatus');
const APP='auditarEpiV1',STOCK='auditarEpiStockV1',CACHE='auditarEpiGestaoCacheV1',REV='auditarEpiServerRevision';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
const uid=p=>p+'_'+Date.now()+'_'+Math.random().toString(36).slice(2,8);
const now=()=>new Date().toISOString();
let tab='overview',deliveryCapture=null;

function blankApp(){return {companies:[],workers:[],epis:[],deliveries:[],purchases:[],batches:[],epiKits:[],returns:[],refusals:[],inventoryCounts:[],auditLog:[]}}
function blankStock(){return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{},warehouses:[],warehouseMinimums:{}}}
function read(){
 try{
  if(PC){
   const r=JSON.parse(localStorage.getItem(CACHE)||'{}');r.app={...blankApp(),...(r.app||{})};r.stock={...blankStock(),...(r.stock||{})};
   for(const k of Object.keys(blankApp()))r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];
   r.stock.movements=Array.isArray(r.stock.movements)?r.stock.movements:[];r.stock.warehouses=Array.isArray(r.stock.warehouses)?r.stock.warehouses:[];r.stock.minimums=r.stock.minimums||{};return r;
  }
  const app={...blankApp(),...JSON.parse(localStorage.getItem(APP)||'{}')},stock={...blankStock(),...JSON.parse(localStorage.getItem(STOCK)||'{}')};
  for(const k of Object.keys(blankApp()))app[k]=Array.isArray(app[k])?app[k]:[];stock.movements=Array.isArray(stock.movements)?stock.movements:[];stock.warehouses=Array.isArray(stock.warehouses)?stock.warehouses:[];stock.minimums=stock.minimums||{};
  return {version:1,revision:Number(localStorage.getItem(REV)||0),updatedAt:now(),app,stock};
 }catch(_){return {version:1,revision:0,updatedAt:'',app:blankApp(),stock:blankStock()}}
}
function write(r){
 r.updatedAt=now();
 if(PC)localStorage.setItem(CACHE,JSON.stringify(r));else{localStorage.setItem(APP,JSON.stringify(r.app));localStorage.setItem(STOCK,JSON.stringify(r.stock));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'advanced-v380'}}))}
}
function user(){return window.GestaoEpiAuth?.user?.()||{}}
function admin(){return user()?.role==='admin'}
function canOperate(){return user()?.role!=='consulta'}
function moduleAllowed(id){return window.GestaoEpiModulesV380?.allowed?.(id)!==false}
function toast(m){const t=$('#toast');if(t){t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2700)}else alert(m)}
async function sync(){
 try{
  const api=window.GestaoEpiAuth?.api;if(!api)return false;const root=read(),res=await api('epi_sync_merge',{deviceId:window.GestaoEpiAuth?.deviceId?.()||'',client:PC?'gestao':'campo',payload:root});
  if(!res?.ok)throw new Error(res?.message||'Falha na sincronização.');const remote=res.payload||root;
  if(PC)localStorage.setItem(CACHE,JSON.stringify(remote));else{localStorage.setItem(APP,JSON.stringify(remote.app||{}));localStorage.setItem(STOCK,JSON.stringify(remote.stock||{}));localStorage.setItem(REV,String(res.revision||remote.revision||0))}
  document.dispatchEvent(new CustomEvent('gestao-epi-sync-applied'));return true;
 }catch(e){toast(e?.message||'Falha ao sincronizar.');return false}
}
function who(){const u=user();return {username:String(u.username||''),name:String(u.name||u.username||''),role:String(u.role||'')}}
function comp(r,id){return r.app.companies.find(x=>x.id===id)||{}}
function worker(r,id){return r.app.workers.find(x=>x.id===id)||{}}
function epi(r,id){return r.app.epis.find(x=>x.id===id)||{}}
function fmt(v){if(!v)return'—';try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short'}).format(new Date(v))}catch{return String(v)}}
function totalBalance(r,c,e){return (r.stock.movements||[]).filter(m=>m.companyId===c&&m.epiId===e).reduce((s,m)=>s+Number(m.delta||0),0)}
function whBalance(r,c,e,w){return (r.stock.movements||[]).filter(m=>m.companyId===c&&m.epiId===e&&String(m.warehouseId||'')===String(w||'')).reduce((s,m)=>s+Number(m.delta||0),0)}
function warehouses(r,c){return (r.stock.warehouses||[]).filter(w=>w.companyId===c&&w.active!==false).sort((a,b)=>(b.isDefault?1:0)-(a.isDefault?1:0)||String(a.name).localeCompare(String(b.name)))}
function defaultWarehouse(r,c){const ws=warehouses(r,c);return ws.find(w=>w.isDefault)||ws[0]||null}
function recalls(r){return (r.app.auditLog||[]).filter(x=>x?.type==='epi_recall')}
function auths(r){return (r.app.auditLog||[]).filter(x=>x?.type==='epi_authorization')}
function upsertAudit(r,row){const a=r.app.auditLog||(r.app.auditLog=[]),i=a.findIndex(x=>x.id===row.id);if(i>=0)a[i]=row;else a.unshift(row)}
function minStock(r,c,e){return Number(r.stock.minimums?.[c+'::'+e]??5)}

function lotRows(r,c='',epiId=''){
 const map=new Map();
 for(const m of r.stock.movements||[]){
  if(c&&m.companyId!==c)continue;if(epiId&&m.epiId!==epiId)continue;
  const batchId=String(m.batchId||''),lot=String(m.lot||'');if(!batchId&&!lot)continue;
  const key=[m.companyId,m.epiId,batchId||'lot:'+lot].join('|');
  let x=map.get(key);if(!x)x={companyId:m.companyId,epiId:m.epiId,batchId,lot,physicalExpiry:String(m.physicalExpiry||''),purchaseId:String(m.purchaseId||''),invoiceNumber:String(m.invoiceNumber||''),balance:0,createdAt:String(m.createdAt||'')};
  x.balance+=Number(m.delta||0);if(!x.physicalExpiry&&m.physicalExpiry)x.physicalExpiry=String(m.physicalExpiry);if(!x.lot&&m.lot)x.lot=String(m.lot);if(!x.batchId&&m.batchId)x.batchId=String(m.batchId);map.set(key,x);
 }
 return [...map.values()].filter(x=>x.balance>0).sort((a,b)=>String(a.physicalExpiry||'9999').localeCompare(String(b.physicalExpiry||'9999')));
}
function allocateLots(r,c,e,qty,warehouseId=''){
 const rows=lotRows(r,c,e).filter(x=>{
  if(!warehouseId)return true;
  const hasWh=(r.stock.movements||[]).some(m=>m.companyId===c&&m.epiId===e&&(m.batchId===x.batchId||(!x.batchId&&m.lot===x.lot))&&String(m.warehouseId||'')===String(warehouseId));
  return hasWh;
 });
 let left=Number(qty||0),out=[];
 for(const x of rows){if(left<=0)break;let avail=x.balance;if(warehouseId){avail=(r.stock.movements||[]).filter(m=>m.companyId===c&&m.epiId===e&&(m.batchId===x.batchId||(!x.batchId&&m.lot===x.lot))&&String(m.warehouseId||'')===String(warehouseId)).reduce((s,m)=>s+Number(m.delta||0),0)}if(avail<=0)continue;const take=Math.min(left,avail);out.push({qty:take,batchId:x.batchId,purchaseId:x.purchaseId,lot:x.lot,physicalExpiry:x.physicalExpiry,invoiceNumber:x.invoiceNumber});left-=take}
 if(left>0)out.push({qty:left,batchId:'',purchaseId:'',lot:'',physicalExpiry:'',invoiceNumber:''});
 return out;
}

function forecastRows(r,c,days=60){
 const cutoff=Date.now()-days*86400000,ids=new Set();(r.stock.movements||[]).filter(m=>m.companyId===c).forEach(m=>ids.add(m.epiId));r.app.epis.filter(e=>e.active!==false).forEach(e=>ids.add(e.id));
 return [...ids].map(id=>{const e=epi(r,id),bal=totalBalance(r,c,id),used=(r.stock.movements||[]).filter(m=>m.companyId===c&&m.epiId===id&&String(m.type||'')==='OUT'&&Date.parse(m.createdAt||0)>=cutoff).reduce((s,m)=>s+Math.abs(Math.min(0,Number(m.delta||0))),0),daily=used/days,min=minStock(r,c,id),daysLeft=daily>0?Math.max(0,bal/daily):null,reorder=daily>0?Math.max(0,Math.ceil(daily*30+min-bal)):0;return{epi:e,balance:bal,used,daily,daysLeft,reorder,min}}).filter(x=>x.balance||x.used).sort((a,b)=>(a.daysLeft??99999)-(b.daysLeft??99999));
}
function auditIssues(r,c=''){
 const out=[],cs=c?[c]:r.app.companies.filter(x=>x.active!==false).map(x=>x.id);
 for(const companyId of cs){
  const ids=new Set();(r.stock.movements||[]).filter(m=>m.companyId===companyId).forEach(m=>ids.add(m.epiId));
  for(const eId of ids){const bal=totalBalance(r,companyId,eId),min=minStock(r,companyId,eId);if(bal<0)out.push({sev:'critical',title:'Saldo total negativo',detail:epi(r,eId).name+' • '+bal,companyId});else if(bal<=min)out.push({sev:'warn',title:'Estoque no mínimo ou abaixo',detail:epi(r,eId).name+' • saldo '+bal+' / mín. '+min,companyId})}
  const ws=warehouses(r,companyId);for(const w of ws)for(const eId of ids){const b=whBalance(r,companyId,eId,w.id);if(b<0)out.push({sev:'critical',title:'Almoxarifado com saldo negativo',detail:w.name+' • '+epi(r,eId).name+' • '+b,companyId})}
  if(ws.length>1){const since=Math.min(...ws.map(w=>Date.parse(w.createdAt||now())));for(const d of r.app.deliveries.filter(d=>d.companyId===companyId&&Date.parse(d.createdAt||0)>=since&&!d.cancelled)){if(!d.warehouseId)out.push({sev:'warn',title:'Entrega sem almoxarifado identificado',detail:worker(r,d.workerId).name+' • '+fmt(d.createdAt),companyId})}}
  for(const d of r.app.deliveries.filter(d=>d.companyId===companyId&&!d.cancelled)){const ev=!!(d.signature||d.biometricEvidenceId||d.biometricEvidenceHash||d.biometricVerified||d.confirmationMethod||d.confirmationType);if(!ev)out.push({sev:'warn',title:'Entrega sem evidência identificada',detail:worker(r,d.workerId).name+' • '+fmt(d.createdAt),companyId})}
  for(const l of lotRows(r,companyId)){if(l.physicalExpiry&&Date.parse(l.physicalExpiry)<Date.now())out.push({sev:'critical',title:'Lote vencido com saldo',detail:epi(r,l.epiId).name+' • lote '+(l.lot||l.batchId)+' • '+l.balance,companyId})}
  for(const rc of recalls(r).filter(x=>x.companyId===companyId&&x.status!=='closed'))out.push({sev:'critical',title:'Recolhimento em aberto',detail:epi(r,rc.epiId).name+' • '+(rc.lot||'todos os lotes'),companyId});
 }
 return out;
}
function affectedByRecall(r,rc){
 const map=new Map();
 for(const d of r.app.deliveries||[]){if(d.cancelled||d.companyId!==rc.companyId)continue;for(const i of d.items||[]){if(i.epiId!==rc.epiId)continue;if(rc.batchId&&String(i.batchId||'')!==String(rc.batchId))continue;if(rc.lot&&!rc.batchId&&String(i.lot||'')!==String(rc.lot))continue;const w=worker(r,d.workerId);if(!w.id)continue;const old=map.get(w.id)||{worker:w,qty:0,last:d.createdAt};old.qty+=Number(i.qty||0);if(String(d.createdAt)>String(old.last))old.last=d.createdAt;map.set(w.id,old)}}
 return [...map.values()].sort((a,b)=>String(a.worker.name).localeCompare(String(b.worker.name)));
}
function kitFor(r,c,role){return (r.app.epiKits||[]).find(k=>k.companyId===c&&k.active!==false&&norm(k.roleName)===norm(role))}

function styles(){
 if($('#adv380Style'))return;const s=document.createElement('style');s.id='adv380Style';s.textContent=`
.adv380-wrap{display:grid;gap:12px}.adv380-tabs{display:flex;gap:6px;overflow:auto;padding-bottom:2px}.adv380-tabs button{border:1px solid #cfe0dc;background:#fff;border-radius:999px;padding:8px 11px;font-weight:850;color:#315f59;white-space:nowrap}.adv380-tabs button.active{background:#0f766e;color:#fff;border-color:#0f766e}.adv380-card{background:#fff;border:1px solid #dce8e5;border-radius:15px;padding:14px}.adv380-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.adv380-grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.adv380-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}.adv380-kpi{background:#fff;border:1px solid #dce8e5;border-radius:13px;padding:11px}.adv380-kpi strong{display:block;font-size:23px;color:#173d39}.adv380-kpi span{font-size:9px;color:#718480;text-transform:uppercase}.adv380-card label{display:grid;gap:5px;font-size:11px;font-weight:850;color:#46615d}.adv380-card input,.adv380-card select,.adv380-card textarea{width:100%;box-sizing:border-box;border:1px solid #cfe0dc;border-radius:9px;padding:9px;background:#fff}.adv380-actions{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end;margin-top:10px}.adv380-btn{border:1px solid #cfe0dc;background:#fff;border-radius:9px;padding:8px 10px;font-weight:850;color:#285f58}.adv380-btn.primary{background:#0f766e;color:#fff;border-color:#0f766e}.adv380-btn.danger{background:#fff0ee;color:#b42318;border-color:#f2c3bd}.adv380-list{display:grid;gap:8px}.adv380-row{border:1px solid #e1ebe8;border-radius:11px;padding:10px;display:grid;grid-template-columns:1fr auto;gap:9px;align-items:center}.adv380-row b{display:block}.adv380-row small{display:block;color:#6d817d;margin-top:3px;line-height:1.4}.adv380-table{width:100%;border-collapse:collapse;font-size:11px}.adv380-table th,.adv380-table td{padding:8px;border-bottom:1px solid #e4ecea;text-align:left;vertical-align:top}.adv380-table th{font-size:9px;text-transform:uppercase;color:#607872;background:#f6f9f8}.adv380-pill{display:inline-block;border-radius:999px;padding:4px 7px;font-size:9px;font-weight:900}.adv380-pill.ok{background:#ecfdf3;color:#166534}.adv380-pill.warn{background:#fff8e6;color:#8a6418}.adv380-pill.critical{background:#fff0ee;color:#b42318}.adv380-note{padding:9px;border-radius:10px;background:#f4f9f8;color:#5d7671;font-size:11px;line-height:1.45}.adv380-delivery-extra{grid-column:1/-1;border-top:1px dashed #d7e5e2;padding-top:9px}.adv380-delivery-extra .adv380-kit{margin-top:6px;width:max-content}@media(max-width:900px){.adv380-kpis{grid-template-columns:repeat(2,1fr)}.adv380-grid,.adv380-grid.three{grid-template-columns:1fr}.adv380-row{grid-template-columns:1fr}}
`;document.head.appendChild(s)
}
function nav(){
 if(PC){const n=$('.sidebar nav');if(n&&!n.querySelector('[data-view="advancedStockV380"]')){const b=document.createElement('button');b.className='nav pc-new';b.dataset.view='advancedStockV380';b.innerHTML='🏬 <span>Estoque avançado</span>';const ref=n.querySelector('[data-view="stock"]');ref?.insertAdjacentElement('afterend',b)||n.appendChild(b)}}
 else{const g=$('#moreFunctions .more323-grid');if(g&&!g.querySelector('[data-go="advancedStockV380"]')){const b=document.createElement('button');b.className='more323-card';b.dataset.go='advancedStockV380';b.innerHTML='<span>🏬</span><b>Estoque avançado</b><small>Almoxarifados, previsão, lotes e auditoria</small>';g.appendChild(b)}}
 const n=PC?$('.sidebar [data-view="advancedStockV380"]'):$('[data-go="advancedStockV380"]');if(n)n.style.display=(moduleAllowed('advanced_stock')||moduleAllowed('kits'))?'':'none';
}
function view(){
 if($('#advancedStockV380'))return;const main=PC?$('.main'):($('.app-shell')||document.body);if(!main)return;const s=document.createElement('section');s.id='advancedStockV380';s.className='view'+(PC?' pc-modern-view':'');s.innerHTML=`${PC?'<div class="pc-modern-head"><div><h2>Estoque avançado</h2><p>Controle profundo sem complicar a rotina do balcão.</p></div></div>':'<div class="view-head"><button class="back" data-go="moreFunctions">←</button><div><h2>Estoque avançado</h2><p>Almoxarifados, previsão, lotes e auditoria.</p></div></div>'}<div class="adv380-wrap"><div class="adv380-tabs" id="adv380Tabs"><button data-advtab="overview">Visão geral</button><button data-advtab="warehouses">Almoxarifados</button><button data-advtab="forecast">Previsão</button><button data-advtab="lots">Lotes e recolhimento</button><button data-advtab="audit">Auditoria</button><button data-advtab="kits">Kits por função</button></div><div id="adv380Body"></div></div>`;main.appendChild(s)
}
function open(){
 if(!moduleAllowed('advanced_stock')&&!moduleAllowed('kits'))return toast('Estoque avançado não está habilitado para esta conta.');
 view();if(PC){$$('.view').forEach(v=>v.classList.toggle('active',v.id==='advancedStockV380'));$$('.sidebar .nav').forEach(n=>n.classList.toggle('active',n.dataset.view==='advancedStockV380'));if($('#viewTitle'))$('#viewTitle').textContent='Estoque avançado';if($('#viewSub'))$('#viewSub').textContent='Almoxarifados, previsão, lotes, recolhimento e kits.'}else{$$('.view').forEach(v=>v.classList.remove('active'));$('#advancedStockV380').classList.add('active');window.scrollTo(0,0)}render()
}
function tabAllowed(t){if(t==='kits')return moduleAllowed('kits');return moduleAllowed('advanced_stock')}
function render(){
 if(!tabAllowed(tab))tab=moduleAllowed('advanced_stock')?'overview':'kits';$$('#adv380Tabs [data-advtab]').forEach(b=>{b.style.display=tabAllowed(b.dataset.advtab)?'':'none';b.classList.toggle('active',b.dataset.advtab===tab)});
 if(tab==='warehouses')renderWarehouses();else if(tab==='forecast')renderForecast();else if(tab==='lots')renderLots();else if(tab==='audit')renderAudit();else if(tab==='kits')renderKits();else renderOverview()
}
function companyOptions(r,selected=''){return '<option value="">Selecione a empresa</option>'+r.app.companies.filter(c=>c.active!==false).map(c=>`<option value="${esc(c.id)}" ${c.id===selected?'selected':''}>${esc(c.name)}</option>`).join('')}
function renderOverview(){
 const r=read(),issues=auditIssues(r),rows=forecastRows(r,r.app.companies[0]?.id||'',60),risk=rows.filter(x=>x.daysLeft!=null&&x.daysLeft<=30).length,expired=lotRows(r).filter(x=>x.physicalExpiry&&Date.parse(x.physicalExpiry)<Date.now()).length,openR=recalls(r).filter(x=>x.status!=='closed').length;
 $('#adv380Body').innerHTML=`<div class="adv380-kpis"><div class="adv380-kpi"><strong>${(r.stock.warehouses||[]).filter(x=>x.active!==false).length}</strong><span>Almoxarifados</span></div><div class="adv380-kpi"><strong>${issues.filter(x=>x.sev==='critical').length}</strong><span>Críticos</span></div><div class="adv380-kpi"><strong>${risk}</strong><span>Risco ≤ 30 dias</span></div><div class="adv380-kpi"><strong>${expired}</strong><span>Lotes vencidos</span></div><div class="adv380-kpi"><strong>${openR}</strong><span>Recolhimentos</span></div></div><div class="adv380-card"><h3>Como usar sem complicar</h3><div class="adv380-note">Se a empresa tiver um único almoxarifado, defina-o como padrão e a entrega selecionará automaticamente. A previsão usa o consumo real. Lotes são associados automaticamente pela validade mais próxima quando houver informação disponível.</div></div><div class="adv380-card"><h3>Prioridades</h3><div class="adv380-list">${issues.slice(0,12).map(x=>`<div class="adv380-row"><div><b>${esc(x.title)}</b><small>${esc(comp(r,x.companyId).name||'Empresa')} • ${esc(x.detail)}</small></div><span class="adv380-pill ${x.sev}">${x.sev==='critical'?'Crítico':'Atenção'}</span></div>`).join('')||'<div class="adv380-note">Nenhuma divergência crítica identificada.</div>'}</div></div>`;
}
function renderWarehouses(){
 const r=read(),prev=$('#adv380Company')?.value||r.app.companies[0]?.id||'';
 $('#adv380Body').innerHTML=`<div class="adv380-card"><div class="adv380-grid"><label>Empresa<select id="adv380Company">${companyOptions(r,prev)}</select></label><label>Novo almoxarifado<input id="adv380WhName" placeholder="Ex.: Almoxarifado Central"></label></div><div class="adv380-actions"><button class="adv380-btn primary" id="adv380AddWh">＋ Adicionar almoxarifado</button></div></div><div class="adv380-card"><h3>Almoxarifados</h3><div id="adv380WhList"></div></div><div class="adv380-card"><h3>Transferir estoque</h3><div class="adv380-grid three"><label>Origem<select id="adv380TransferFrom"></select></label><label>Destino<select id="adv380TransferTo"></select></label><label>EPI<select id="adv380TransferEpi"></select></label><label>Quantidade<input id="adv380TransferQty" type="number" min="1" value="1"></label><label style="grid-column:span 2">Observação<input id="adv380TransferNote" placeholder="Opcional"></label></div><div id="adv380TransferHint" class="adv380-note" style="margin-top:9px"></div><div class="adv380-actions"><button class="adv380-btn primary" id="adv380Transfer">Transferir</button></div></div>`;
 const refresh=()=>{const root=read(),c=$('#adv380Company').value,ws=warehouses(root,c);$('#adv380WhList').innerHTML=ws.length?'<div class="adv380-list">'+ws.map(w=>`<div class="adv380-row"><div><b>${esc(w.name)}</b><small>${w.isDefault?'Padrão para novas entregas':'Almoxarifado ativo'}</small></div><div class="adv380-actions"><button class="adv380-btn" data-wh-default="${esc(w.id)}">${w.isDefault?'✓ Padrão':'Definir padrão'}</button><button class="adv380-btn danger" data-wh-archive="${esc(w.id)}">Arquivar</button></div></div>`).join('')+'</div>':'<div class="adv380-note">Nenhum almoxarifado cadastrado. Se não usar multiestoque, não precisa cadastrar.</div>';const opts='<option value="">Não alocado / legado</option>'+ws.map(w=>`<option value="${esc(w.id)}">${esc(w.name)}</option>`).join('');$('#adv380TransferFrom').innerHTML=opts;$('#adv380TransferTo').innerHTML='<option value="">Selecione</option>'+ws.map(w=>`<option value="${esc(w.id)}">${esc(w.name)}</option>`).join('');$('#adv380TransferEpi').innerHTML='<option value="">Selecione</option>'+root.app.epis.filter(e=>e.active!==false).map(e=>`<option value="${esc(e.id)}">${esc(e.name)}${e.ca?' • CA '+esc(e.ca):''}</option>`).join('');bindWhButtons();updateTransferHint()};
 $('#adv380Company').onchange=refresh;$('#adv380AddWh').onclick=addWarehouse;$('#adv380TransferFrom').onchange=updateTransferHint;$('#adv380TransferEpi').onchange=updateTransferHint;$('#adv380Transfer').onclick=transferStock;refresh()
}
function bindWhButtons(){
 $$('[data-wh-default]').forEach(b=>b.onclick=()=>setDefaultWarehouse(b.dataset.whDefault));$$('[data-wh-archive]').forEach(b=>b.onclick=()=>archiveWarehouse(b.dataset.whArchive))
}
async function addWarehouse(){
 if(!admin())return toast('Somente o Administrador pode cadastrar almoxarifados.');const r=read(),c=$('#adv380Company').value,name=$('#adv380WhName').value.trim();if(!c)return toast('Selecione a empresa.');if(!name)return toast('Informe o nome do almoxarifado.');const ws=warehouses(r,c);if(ws.some(w=>norm(w.name)===norm(name)))return toast('Esse almoxarifado já existe.');r.stock.warehouses.push({id:uid('wh'),companyId:c,name,active:true,isDefault:ws.length===0,createdAt:now(),updatedAt:now(),createdBy:who()});write(r);await sync();toast('Almoxarifado cadastrado.');renderWarehouses();injectDeliveryExtras()
}
async function setDefaultWarehouse(id){const r=read(),w=r.stock.warehouses.find(x=>x.id===id);if(!w)return;r.stock.warehouses.filter(x=>x.companyId===w.companyId).forEach(x=>{x.isDefault=x.id===id;x.updatedAt=now()});write(r);await sync();toast('Almoxarifado padrão atualizado.');renderWarehouses();injectDeliveryExtras()}
async function archiveWarehouse(id){if(!confirm('Arquivar este almoxarifado? O histórico será preservado.'))return;const r=read(),w=r.stock.warehouses.find(x=>x.id===id);if(!w)return;w.active=false;w.isDefault=false;w.updatedAt=now();const left=warehouses(r,w.companyId);if(left.length&&!left.some(x=>x.isDefault))left[0].isDefault=true;write(r);await sync();toast('Almoxarifado arquivado.');renderWarehouses();injectDeliveryExtras()}
function updateTransferHint(){const r=read(),c=$('#adv380Company')?.value||'',e=$('#adv380TransferEpi')?.value||'',from=$('#adv380TransferFrom')?.value||'',h=$('#adv380TransferHint');if(h)h.textContent=c&&e?'Disponível na origem: '+whBalance(r,c,e,from):'Selecione origem e EPI para conferir o saldo.'}
async function transferStock(){
 if(!canOperate())return toast('Seu perfil é somente consulta.');const r=read(),c=$('#adv380Company').value,from=$('#adv380TransferFrom').value,to=$('#adv380TransferTo').value,e=$('#adv380TransferEpi').value,qty=Math.max(0,Number($('#adv380TransferQty').value||0)),note=$('#adv380TransferNote').value.trim();if(!c||!to||!e||!qty)return toast('Informe empresa, destino, EPI e quantidade.');if(from===to)return toast('Origem e destino precisam ser diferentes.');const avail=whBalance(r,c,e,from);if(qty>avail)return toast('Saldo insuficiente na origem. Disponível: '+avail);const id=uid('tr'),at=now(),base={companyId:c,epiId:e,transferId:id,createdAt:at,updatedAt:at,createdBy:who()};r.stock.movements.unshift({...base,id:id+'_out',type:'TRANSFER_OUT',delta:-qty,warehouseId:from,note:note||'Transferência entre almoxarifados'},{...base,id:id+'_in',type:'TRANSFER_IN',delta:qty,warehouseId:to,note:note||'Transferência entre almoxarifados'});write(r);await sync();toast('Transferência registrada sem alterar o estoque total.');renderWarehouses()
}
function renderForecast(){
 const r=read(),c=$('#adv380ForecastCompany')?.value||r.app.companies[0]?.id||'',days=Number($('#adv380ForecastDays')?.value||60);
 $('#adv380Body').innerHTML=`<div class="adv380-card"><div class="adv380-grid"><label>Empresa<select id="adv380ForecastCompany">${companyOptions(r,c)}</select></label><label>Base de consumo<select id="adv380ForecastDays"><option value="30">Últimos 30 dias</option><option value="60" selected>Últimos 60 dias</option><option value="90">Últimos 90 dias</option></select></label></div></div><div class="adv380-card"><h3>Previsão de estoque</h3><div id="adv380ForecastTable"></div></div>`;const draw=()=>{const root=read(),company=$('#adv380ForecastCompany').value,d=Number($('#adv380ForecastDays').value),rows=company?forecastRows(root,company,d):[];$('#adv380ForecastTable').innerHTML=rows.length?`<div style="overflow:auto"><table class="adv380-table"><thead><tr><th>EPI</th><th>Saldo</th><th>Consumo no período</th><th>Dias estimados</th><th>Sugestão de compra</th></tr></thead><tbody>${rows.map(x=>`<tr><td><b>${esc(x.epi.name||'EPI')}</b><br><small>${x.epi.ca?'CA '+esc(x.epi.ca):''}</small></td><td>${x.balance}</td><td>${x.used}</td><td>${x.daysLeft==null?'Sem consumo':Math.round(x.daysLeft)+' dias'} ${x.daysLeft!=null&&x.daysLeft<=30?'<span class="adv380-pill warn">Atenção</span>':''}</td><td>${x.reorder>0?'<b>'+x.reorder+'</b> un.':'—'}</td></tr>`).join('')}</tbody></table></div>`:'<div class="adv380-note">Ainda não há consumo suficiente para gerar previsão.</div>'};$('#adv380ForecastCompany').onchange=draw;$('#adv380ForecastDays').onchange=draw;draw()
}
function renderLots(){
 const r=read(),c=$('#adv380LotCompany')?.value||r.app.companies[0]?.id||'';
 $('#adv380Body').innerHTML=`<div class="adv380-card"><label>Empresa<select id="adv380LotCompany">${companyOptions(r,c)}</select></label></div><div class="adv380-card"><h3>Lotes em estoque</h3><div id="adv380LotsTable"></div></div><div class="adv380-card"><h3>Novo recolhimento</h3><div class="adv380-grid"><label>Lote / EPI<select id="adv380RecallLot"></select></label><label>EPI substituto (opcional)<select id="adv380RecallReplacement"></select></label><label style="grid-column:1/-1">Motivo<input id="adv380RecallReason" placeholder="Ex.: problema de qualidade, lote recolhido pelo fabricante"></label></div><div class="adv380-actions"><button class="adv380-btn primary" id="adv380CreateRecall">Criar recolhimento</button></div></div><div class="adv380-card"><h3>Recolhimentos</h3><div id="adv380RecallList"></div></div>`;const draw=()=>{const root=read(),company=$('#adv380LotCompany').value,rows=company?lotRows(root,company):[];$('#adv380LotsTable').innerHTML=rows.length?`<div style="overflow:auto"><table class="adv380-table"><thead><tr><th>EPI</th><th>Lote</th><th>Validade física</th><th>Saldo do lote</th></tr></thead><tbody>${rows.map(x=>`<tr><td>${esc(epi(root,x.epiId).name||'EPI')}</td><td>${esc(x.lot||x.batchId||'—')}</td><td>${fmt(x.physicalExpiry)} ${x.physicalExpiry&&Date.parse(x.physicalExpiry)<Date.now()?'<span class="adv380-pill critical">Vencido</span>':''}</td><td>${x.balance}</td></tr>`).join('')}</tbody></table></div>`:'<div class="adv380-note">Nenhum lote com saldo identificado.</div>';$('#adv380RecallLot').innerHTML='<option value="">Selecione</option>'+rows.map((x,i)=>`<option value="${i}">${esc(epi(root,x.epiId).name||'EPI')} • ${esc(x.lot||x.batchId||'lote')} • saldo ${x.balance}</option>`).join('');$('#adv380RecallLot').dataset.rows=JSON.stringify(rows);$('#adv380RecallReplacement').innerHTML='<option value="">Sem substituto definido</option>'+root.app.epis.filter(e=>e.active!==false).map(e=>`<option value="${esc(e.id)}">${esc(e.name)}${e.ca?' • CA '+esc(e.ca):''}</option>`).join('');renderRecallList(root,company)};$('#adv380LotCompany').onchange=draw;$('#adv380CreateRecall').onclick=createRecall;draw()
}
function renderRecallList(r,c){
 const rows=recalls(r).filter(x=>!c||x.companyId===c).sort((a,b)=>String(b.createdAt).localeCompare(String(a.createdAt)));$('#adv380RecallList').innerHTML=rows.length?'<div class="adv380-list">'+rows.map(rc=>{const affected=affectedByRecall(r,rc);return`<div class="adv380-row"><div><b>${esc(epi(r,rc.epiId).name||'EPI')} • ${esc(rc.lot||'todos os lotes')}</b><small>${esc(rc.reason||'Recolhimento')} • ${affected.length} trabalhador(es) afetado(s) • status ${rc.status==='closed'?'encerrado':'aberto'}${rc.replacementEpiId?'<br>Substituto: '+esc(epi(r,rc.replacementEpiId).name||'EPI'):''}</small></div><div class="adv380-actions"><button class="adv380-btn" data-recall-show="${esc(rc.id)}">Ver pessoas</button>${rc.status!=='closed'&&rc.replacementEpiId?'<button class="adv380-btn primary" data-recall-release="'+esc(rc.id)+'">Liberar substituições</button>':''}${rc.status!=='closed'?'<button class="adv380-btn danger" data-recall-close="'+esc(rc.id)+'">Encerrar</button>':''}</div></div>`}).join('')+'</div>':'<div class="adv380-note">Nenhum recolhimento registrado.</div>';$$('[data-recall-show]').forEach(b=>b.onclick=()=>showRecallAffected(b.dataset.recallShow));$$('[data-recall-release]').forEach(b=>b.onclick=()=>releaseRecall(b.dataset.recallRelease));$$('[data-recall-close]').forEach(b=>b.onclick=()=>closeRecall(b.dataset.recallClose))
}
async function createRecall(){
 if(!admin())return toast('Somente o Administrador pode abrir recolhimento.');const r=read(),c=$('#adv380LotCompany').value,idx=Number($('#adv380RecallLot').value),rows=JSON.parse($('#adv380RecallLot').dataset.rows||'[]'),lot=rows[idx],reason=$('#adv380RecallReason').value.trim(),replacement=$('#adv380RecallReplacement').value;if(!c||!lot)return toast('Selecione o lote/EPI.');if(!reason)return toast('Informe o motivo do recolhimento.');const row={id:uid('recall'),type:'epi_recall',companyId:c,epiId:lot.epiId,batchId:lot.batchId||'',lot:lot.lot||'',physicalExpiry:lot.physicalExpiry||'',replacementEpiId:replacement||'',reason,status:'open',createdAt:now(),updatedAt:now(),createdBy:who()};upsertAudit(r,row);write(r);await sync();toast('Recolhimento criado.');renderLots()
}
function showRecallAffected(id){const r=read(),rc=recalls(r).find(x=>x.id===id);if(!rc)return;const rows=affectedByRecall(r,rc);alert(rows.length?rows.map(x=>x.worker.name+' • '+(x.worker.role||'sem cargo')+' • qtd. '+x.qty).join('\n'):'Nenhum trabalhador identificado com esse lote.')}
async function releaseRecall(id){
 const r=read(),rc=recalls(r).find(x=>x.id===id);if(!rc?.replacementEpiId)return;const people=affectedByRecall(r,rc);if(!people.length)return toast('Nenhum trabalhador afetado identificado.');const existing=new Set(auths(r).filter(a=>a.sourceRecallId===rc.id).map(a=>a.workerId)),todo=people.filter(x=>!existing.has(x.worker.id));if(!todo.length)return toast('As substituições já foram liberadas.');const bal=totalBalance(r,rc.companyId,rc.replacementEpiId),reservedQty=auths(r).filter(a=>a.companyId===rc.companyId&&['pending','partial'].includes(String(a.status||''))).reduce((s,a)=>s+(a.items||[]).filter(i=>(i.substitution?.status==='approved'?i.substitution.toEpiId:i.epiId)===rc.replacementEpiId).reduce((q,i)=>q+Math.max(0,Number(i.qty||0)-Number(i.deliveredQty||0)),0),0),need=todo.length;if(bal-reservedQty<need&&!confirm('O estoque disponível parece insuficiente para todas as substituições. Deseja criar as liberações mesmo assim?'))return;const at=now();for(const p of todo){const aid=uid('auth');upsertAudit(r,{id:aid,type:'epi_authorization',code:'LIB-'+aid.replace(/[^A-Za-z0-9]/g,'').slice(-8).toUpperCase(),companyId:rc.companyId,workerId:p.worker.id,items:[{epiId:rc.replacementEpiId,qty:1,deliveredQty:0}],reason:'Substituição por recolhimento de lote',note:'Recolhimento '+(rc.lot||rc.batchId||rc.id)+' • '+rc.reason,status:'pending',authorizedBy:who(),authorizedAt:at,createdAt:at,updatedAt:at,expiresAt:new Date(Date.now()+7*86400000).toISOString(),sourceRecallId:rc.id})}rc.replacementReleasedAt=at;rc.updatedAt=at;upsertAudit(r,rc);write(r);await sync();toast(todo.length+' substituição(ões) liberada(s).');renderLots()
}
async function closeRecall(id){if(!confirm('Encerrar este recolhimento?'))return;const r=read(),rc=recalls(r).find(x=>x.id===id);if(!rc)return;rc.status='closed';rc.closedAt=now();rc.closedBy=who();rc.updatedAt=now();upsertAudit(r,rc);write(r);await sync();toast('Recolhimento encerrado.');renderLots()}
function renderAudit(){
 const r=read(),c=$('#adv380AuditCompany')?.value||'',issues=auditIssues(r,c);
 $('#adv380Body').innerHTML=`<div class="adv380-card"><div class="adv380-grid"><label>Empresa<select id="adv380AuditCompany"><option value="">Todas as empresas</option>${r.app.companies.filter(x=>x.active!==false).map(x=>`<option value="${esc(x.id)}" ${x.id===c?'selected':''}>${esc(x.name)}</option>`).join('')}</select></label><div class="adv380-note"><b>${issues.filter(x=>x.sev==='critical').length}</b> crítico(s) • <b>${issues.filter(x=>x.sev==='warn').length}</b> atenção(ões)</div></div></div><div class="adv380-card"><h3>Auditoria automática de divergências</h3><div id="adv380AuditList" class="adv380-list">${issues.map(x=>`<div class="adv380-row"><div><b>${esc(x.title)}</b><small>${esc(comp(r,x.companyId).name||'Empresa')} • ${esc(x.detail)}</small></div><span class="adv380-pill ${x.sev}">${x.sev==='critical'?'Crítico':'Atenção'}</span></div>`).join('')||'<div class="adv380-note">Nenhuma divergência identificada nos critérios automáticos.</div>'}</div></div>`;$('#adv380AuditCompany').onchange=renderAudit
}
function renderKits(){
 const r=read(),c=$('#adv380KitCompany')?.value||r.app.companies[0]?.id||'';
 $('#adv380Body').innerHTML=`<div class="adv380-card"><div class="adv380-grid"><label>Empresa<select id="adv380KitCompany">${companyOptions(r,c)}</select></label><label>Função<select id="adv380KitRole"></select></label></div><div id="adv380KitItems" style="margin-top:10px"></div><div class="adv380-actions"><button class="adv380-btn primary" id="adv380KitSave">Salvar kit da função</button></div></div><div class="adv380-card"><h3>Kits configurados</h3><div id="adv380KitList"></div></div>`;const fillRoles=()=>{const root=read(),company=$('#adv380KitCompany').value,roles=[...new Set(root.app.workers.filter(w=>w.companyId===company&&w.active!==false&&w.role).map(w=>String(w.role).trim()))].sort();$('#adv380KitRole').innerHTML='<option value="">Selecione</option>'+roles.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');renderKitItems();renderKitList()};$('#adv380KitCompany').onchange=fillRoles;$('#adv380KitRole').onchange=renderKitItems;$('#adv380KitSave').onclick=saveKit;fillRoles()
}
function renderKitItems(){
 const r=read(),c=$('#adv380KitCompany')?.value||'',role=$('#adv380KitRole')?.value||'',box=$('#adv380KitItems');if(!box)return;if(!role){box.innerHTML='<div class="adv380-note">Selecione uma função.</div>';return}const kit=kitFor(r,c,role),legacy=comp(r,c).epiRoleRules?.[norm(role)]?.epiIds||[],items=new Map((kit?.items||[]).map(i=>[i.epiId,Number(i.qty||1)]));if(!kit)legacy.forEach(id=>items.set(id,1));box.innerHTML='<div class="adv380-grid">'+r.app.epis.filter(e=>e.active!==false).map(e=>`<label class="adv380-row" style="grid-template-columns:auto 1fr 75px"><input type="checkbox" data-kit-epi="${esc(e.id)}" ${items.has(e.id)?'checked':''}><span><b>${esc(e.name)}</b><small>${e.ca?'CA '+esc(e.ca):''}</small></span><input type="number" min="1" value="${items.get(e.id)||1}" data-kit-qty="${esc(e.id)}"></label>`).join('')+'</div>'
}
async function saveKit(){
 if(!admin())return toast('Somente o Administrador pode alterar kits.');const r=read(),c=$('#adv380KitCompany').value,role=$('#adv380KitRole').value;if(!c||!role)return toast('Selecione empresa e função.');const items=$$('[data-kit-epi]:checked').map(x=>({epiId:x.dataset.kitEpi,qty:Math.max(1,Number($('[data-kit-qty="'+CSS.escape(x.dataset.kitEpi)+'"]')?.value||1))}));if(!items.length)return toast('Selecione pelo menos um EPI.');let k=kitFor(r,c,role);if(!k){k={id:uid('kit'),companyId:c,roleName:role,active:true,createdAt:now()};r.app.epiKits.unshift(k)}k.items=items;k.updatedAt=now();k.updatedBy=who();write(r);await sync();toast('Kit da função salvo.');renderKits();injectDeliveryExtras()
}
function renderKitList(){
 const r=read(),c=$('#adv380KitCompany')?.value||'',box=$('#adv380KitList');if(!box)return;const rows=(r.app.epiKits||[]).filter(k=>k.companyId===c&&k.active!==false);box.innerHTML=rows.length?'<div class="adv380-list">'+rows.map(k=>`<div class="adv380-row"><div><b>${esc(k.roleName)}</b><small>${(k.items||[]).map(i=>esc(epi(r,i.epiId).name||'EPI')+' x'+Number(i.qty||1)).join(' • ')}</small></div><span class="adv380-pill ok">${(k.items||[]).length} EPI(s)</span></div>`).join('')+'</div>':'<div class="adv380-note">Nenhum kit configurado.</div>'
}

function injectDeliveryExtras(){
 if(!moduleAllowed('advanced_stock')&&!moduleAllowed('kits'))return;
 if(PC){
  const card=$('#newDeliveryPc .pc-card.pc-grid');if(card&&!$('#pcDeliveryWarehouse')){const wrap=document.createElement('div');wrap.className='adv380-delivery-extra';wrap.innerHTML='<div class="adv380-grid"><label id="pcDeliveryWarehouseLabel">Retirar de<select id="pcDeliveryWarehouse"></select></label><div style="align-self:end"><button class="adv380-btn adv380-kit" id="pc380ApplyKit" type="button">⚡ Aplicar kit da função</button></div></div>';card.appendChild(wrap);$('#pcDeliveryCompany')?.addEventListener('change',fillDeliveryWarehouses);$('#pcDeliveryWorker')?.addEventListener('change',updateKitButton);$('#pc380ApplyKit').onclick=applyKit;fillDeliveryWarehouses();updateKitButton()}
 }else{
  const card=$('#delivery .card.form-grid');if(card&&!$('#deliveryWarehouse')){const wrap=document.createElement('div');wrap.className='adv380-delivery-extra';wrap.innerHTML='<div class="adv380-grid"><label id="deliveryWarehouseLabel">Retirar de<select id="deliveryWarehouse"></select></label><div style="align-self:end"><button class="secondary adv380-kit" id="adv380ApplyKit" type="button">⚡ Aplicar kit da função</button></div></div>';card.insertBefore(wrap,$('#deliveryMore')||null);$('#deliveryCompany')?.addEventListener('change',fillDeliveryWarehouses);$('#deliveryWorker')?.addEventListener('change',updateKitButton);$('#adv380ApplyKit').onclick=applyKit;fillDeliveryWarehouses();updateKitButton()}
 }
}
function fillDeliveryWarehouses(){
 const r=read(),c=PC?$('#pcDeliveryCompany')?.value||'':$('#deliveryCompany')?.value||'',sel=PC?$('#pcDeliveryWarehouse'):$('#deliveryWarehouse'),lab=PC?$('#pcDeliveryWarehouseLabel'):$('#deliveryWarehouseLabel');if(!sel||!lab)return;const ws=warehouses(r,c);lab.style.display=moduleAllowed('advanced_stock')&&ws.length?'grid':'none';sel.innerHTML=ws.map(w=>`<option value="${esc(w.id)}">${esc(w.name)}${w.isDefault?' • padrão':''}</option>`).join('');const d=defaultWarehouse(r,c);if(d)sel.value=d.id
}
function updateKitButton(){
 const r=read(),c=PC?$('#pcDeliveryCompany')?.value||'':$('#deliveryCompany')?.value||'',wId=PC?$('#pcDeliveryWorker')?.value||'':$('#deliveryWorker')?.value||'',w=worker(r,wId),k=w?.role?kitFor(r,c,w.role):null,b=PC?$('#pc380ApplyKit'):$('#adv380ApplyKit');if(b){b.style.display=moduleAllowed('kits')&&k?'inline-flex':'none';if(k)b.textContent='⚡ Aplicar kit: '+k.roleName}
}
function applyKit(){
 const r=read(),c=PC?$('#pcDeliveryCompany')?.value||'':$('#deliveryCompany')?.value||'',wId=PC?$('#pcDeliveryWorker')?.value||'':$('#deliveryWorker')?.value||'',w=worker(r,wId),k=w?.role?kitFor(r,c,w.role):null;if(!k)return toast('Não há kit configurado para a função deste trabalhador.');
 const box=PC?$('#pcDeliveryItems'):$('#deliveryItems');if(!box)return;box.innerHTML='';
 for(const item of k.items||[]){(PC?$('#pcAddDeliveryItem'):$('#btnAddItem'))?.click();const row=PC?$$('#pcDeliveryItems .pc-delivery-item').slice(-1)[0]:$$('#deliveryItems .delivery-item').slice(-1)[0];if(row){const se=PC?row.querySelector('.pc-item-epi'):row.querySelector('.item-epi'),q=PC?row.querySelector('.pc-item-qty'):row.querySelector('.item-qty');if(se)se.value=item.epiId;if(q)q.value=Number(item.qty||1)}}
 toast('Kit aplicado. Revise antes de finalizar.')
}
function captureDelivery(e){
 const btn=e.target.closest?.(PC?'#pcSaveDelivery':'#btnSaveDelivery');if(!btn)return;
 const root=read(),companyId=PC?$('#pcDeliveryCompany')?.value||'':$('#deliveryCompany')?.value||'',workerId=PC?$('#pcDeliveryWorker')?.value||'':$('#deliveryWorker')?.value||'',sel=PC?$('#pcDeliveryWarehouse'):$('#deliveryWarehouse'),warehouseId=sel&&sel.closest('label')?.style.display!=='none'?sel.value||'':'';
 deliveryCapture={before:new Set(root.app.deliveries.map(d=>d.id)),companyId,workerId,warehouseId};
 queueMicrotask(enrichDeliveryAfterSave);
}
function enrichDeliveryAfterSave(){
 const cap=deliveryCapture;deliveryCapture=null;if(!cap)return;const r=read(),d=r.app.deliveries.find(x=>!cap.before.has(x.id)&&x.companyId===cap.companyId&&x.workerId===cap.workerId)||r.app.deliveries.find(x=>x.companyId===cap.companyId&&x.workerId===cap.workerId&&Date.now()-Date.parse(x.createdAt||0)<5000);if(!d)return;
 if(cap.warehouseId)d.warehouseId=cap.warehouseId;
 const expanded=[];for(const item of d.items||[]){const chunks=allocateLots(r,d.companyId,item.epiId,item.qty,cap.warehouseId);for(const ch of chunks)expanded.push({...item,...ch,epiId:item.epiId,warehouseId:cap.warehouseId||''})}
 if(expanded.length)d.items=expanded;d.updatedAt=now();write(r)
}
function central(){
 const r=read(),issues=auditIssues(r),target=PC?$('#operationsPc340 .pc340-kpis'):$('#operationsCenterV340 .ops340-kpis');if(!target)return;let c=$('#adv380CentralKpi');if(!c){c=document.createElement('div');c.id='adv380CentralKpi';c.className=PC?'pc340-kpi':'ops340-kpi';target.appendChild(c);c.style.cursor='pointer';c.onclick=open}c.innerHTML='<strong>'+issues.filter(x=>x.sev==='critical').length+'</strong><span>divergências críticas de estoque</span>'
}
function bind(){
 document.addEventListener('click',e=>{if(e.target.closest(PC?'[data-view="advancedStockV380"]':'[data-go="advancedStockV380"]')){e.preventDefault();e.stopImmediatePropagation();open();return}const t=e.target.closest('[data-advtab]');if(t){tab=t.dataset.advtab;render()}},true);
 document.addEventListener('click',captureDelivery,true);
 document.addEventListener('gestao-epi-sync-applied',()=>setTimeout(()=>{nav();injectDeliveryExtras();central();if($('#advancedStockV380')?.classList.contains('active'))render()},120));
 document.addEventListener('auditar-epi-data-changed',()=>setTimeout(()=>{injectDeliveryExtras();central()},120));
}
function boot(){styles();nav();view();bind();[500,1200,2600,4500].forEach(ms=>setTimeout(()=>{nav();view();injectDeliveryExtras();central()},ms));window.GestaoEpiAdvancedV380={lotRows,forecastRows,auditIssues,warehouses,totalBalance,whBalance}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();