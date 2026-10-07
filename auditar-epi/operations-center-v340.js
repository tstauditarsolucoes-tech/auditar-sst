(()=>{
'use strict';
const APP='auditarEpiV1',STOCK='auditarEpiStockV1',REV='auditarEpiServerRevision';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
function read(k,f={}){try{return {...f,...JSON.parse(localStorage.getItem(k)||'{}')}}catch{return f}}
function fmt(v,withTime=false){if(!v)return '—';try{return new Intl.DateTimeFormat('pt-BR',withTime?{dateStyle:'short',timeStyle:'short'}:{dateStyle:'short'}).format(new Date(v))}catch{return String(v)}}
function parseDate(v){if(!v)return null;let m=String(v).trim().match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);if(m)return new Date(+m[3],+m[2]-1,+m[1],12);const d=new Date(v);return Number.isNaN(d.getTime())?null:d}
function daysTo(v){const d=parseDate(v);if(!d)return null;const n=new Date();n.setHours(12,0,0,0);d.setHours(12,0,0,0);return Math.ceil((d-n)/86400000)}
function field(note,key){const m=String(note||'').match(new RegExp('(?:^|\\|)\\s*'+key+'\\s*:\\s*([^|]+)','i'));return m?m[1].trim():''}
function state(){
 const app=read(APP,{companies:[],workers:[],epis:[],deliveries:[],epiAuthorizations:[]});for(const k of ['companies','workers','epis','deliveries','epiAuthorizations'])app[k]=Array.isArray(app[k])?app[k]:[];
 const stock=read(STOCK,{movements:[],minimums:{}});stock.movements=Array.isArray(stock.movements)?stock.movements:[];stock.minimums=stock.minimums||{};
 return {app,stock};
}
function holdings(a,st){
 const delivered=new Map(),returned=new Map();
 (a.deliveries||[]).filter(d=>d.cancelled!==true).forEach(d=>(d.items||[]).forEach(i=>{const k=d.workerId+'::'+i.epiId,cur=delivered.get(k)||{qty:0,last:null,workerId:d.workerId,epiId:i.epiId};cur.qty+=Number(i.qty||0);if(!cur.last||String(d.createdAt||'')>String(cur.last.createdAt||''))cur.last=d;delivered.set(k,cur)}));
 (st.movements||[]).forEach(m=>{if(!String(m.note||'').startsWith('DEVOLUÇÃO EPI'))return;const wid=m.workerId||field(m.note,'workerId');if(!wid||!m.epiId)return;const k=wid+'::'+m.epiId;returned.set(k,(returned.get(k)||0)+Number(field(m.note,'qtd')||0))});
 return [...delivered.entries()].map(([k,d])=>({...d,qty:Math.max(0,d.qty-(returned.get(k)||0))})).filter(x=>x.qty>0);
}
function balance(st,c,e){return (st.movements||[]).filter(m=>m.companyId===c&&m.epiId===e).reduce((s,m)=>s+Number(m.delta||0),0)}
function caIssue(e){if(!e.ca)return 'Sem CA';const st=norm(e.caValidationStatus||e.caStatus),days=daysTo(e.caValidity);if(/venc|expir|cancel|suspens|inativ|invalid|inval/.test(st)||(days!=null&&days<0))return 'CA vencido/irregular';if(!e.caValidity)return 'CA sem validade';if(!e.caCheckedAt)return 'CA sem consulta';if(days!=null&&days<=30)return 'CA vence em '+Math.max(0,days)+'d';return ''}
function buildPendencies(filter=''){
 const {app:a,stock:st}=state(),epis=new Map(a.epis.map(e=>[e.id,e])),workers=new Map(a.workers.map(w=>[w.id,w])),companies=new Map(a.companies.map(c=>[c.id,c])),out=[];
 const companyOk=id=>!filter||id===filter;
 a.workers.filter(w=>w.active!==false&&companyOk(w.companyId)).forEach(w=>{
  const bio=!!(w.biometric?.encryptedTemplate?.ciphertext||w.biometric?.embedding?.length||w.biometric?.ciphertext);
  if(!bio)out.push({kind:'Biometria',sev:'warn',companyId:w.companyId,title:w.name,detail:'Trabalhador sem biometria facial cadastrada',go:'workers'});
 });
 a.deliveries.filter(d=>d.cancelled!==true&&companyOk(d.companyId)).forEach(d=>{
  const hasEvidence=!!(d.signature||d.biometricEvidenceId||d.biometricEvidenceHash||d.biometricVerified||d.confirmationMethod);
  if(!hasEvidence)out.push({kind:'Entrega',sev:'bad',companyId:d.companyId,title:workers.get(d.workerId)?.name||'Trabalhador',detail:'Entrega sem assinatura ou evidência biométrica identificada • '+fmt(d.createdAt,true),go:'history'});
 });
 const used=new Set();
 a.deliveries.filter(d=>d.cancelled!==true&&companyOk(d.companyId)).forEach(d=>(d.items||[]).forEach(i=>used.add(i.epiId)));
 Object.keys(st.minimums||{}).forEach(k=>{const [c,e]=k.split('::');if(companyOk(c))used.add(e)});
 used.forEach(id=>{const e=epis.get(id);if(!e)return;const issue=caIssue(e);if(issue)out.push({kind:'CA',sev:/venc|irregular/i.test(issue)?'bad':'warn',companyId:'',title:e.name||'EPI',detail:(e.ca?'CA '+e.ca+' • ':'')+issue,go:'caCenterV330'})});
 for(const k of Object.keys(st.minimums||{})){const [c,eid]=k.split('::');if(!companyOk(c))continue;const min=Number(st.minimums[k]||0),saldo=balance(st,c,eid);if(saldo<=min){const e=epis.get(eid);out.push({kind:'Estoque',sev:saldo<=0?'bad':'warn',companyId:c,title:e?.name||'EPI',detail:'Saldo '+saldo+' • mínimo '+min,go:'stock'})}}
 const hs=holdings(a,st);
 hs.forEach(h=>{const w=workers.get(h.workerId),e=epis.get(h.epiId);if(!w||!e||!companyOk(w.companyId)||!Number(e.cycle||0)||!h.last?.createdAt)return;const due=new Date(h.last.createdAt);due.setDate(due.getDate()+Number(e.cycle));const days=Math.ceil((due-new Date())/86400000);if(days<0)out.push({kind:'Troca',sev:'bad',companyId:w.companyId,title:w.name+' • '+e.name,detail:'Troca vencida há '+Math.abs(days)+' dia(s)',go:'smartManagementV350'});else if(days<=15)out.push({kind:'Troca',sev:'warn',companyId:w.companyId,title:w.name+' • '+e.name,detail:'Troca prevista em '+days+' dia(s)',go:'smartManagementV350'})});
 app.epiAuthorizations.filter(x=>['pending','partial','substitution_requested'].includes(String(x.status||'pending'))&&companyOk(x.companyId)).forEach(x=>{const w=workers.get(x.workerId);out.push({kind:'Liberação',sev:x.status==='substitution_requested'?'bad':'warn',companyId:x.companyId,title:w?.name||'Trabalhador',detail:(x.status==='partial'?'Retirada parcial':x.status==='substitution_requested'?'Substituição aguardando TST':'Aguardando retirada')+' • '+String(x.code||''),go:'epiAuthorizationsV350'})});
 const syncTxt=$('#epiCloudStatus')?.textContent||'';if(!navigator.onLine||/falha|erro/i.test(syncTxt)||localStorage.getItem('gestaoEpiNeedsRefreshV222'))out.push({kind:'Sincronização',sev:!navigator.onLine?'warn':'bad',companyId:'',title:!navigator.onLine?'Dispositivo offline':'Sincronização requer atenção',detail:syncTxt||'Há atualização pendente',go:'operationsCenterV340'});
 return {rows:out.sort((x,y)=>(x.sev==='bad'?0:1)-(y.sev==='bad'?0:1)||x.kind.localeCompare(y.kind)),app:a,stock:st,companies};
}
function injectStyle(){if($('#ops340Style'))return;const s=document.createElement('style');s.id='ops340Style';s.textContent=`
.ops340-wrap{display:grid;gap:10px}.ops340-kpis{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.ops340-kpi,.ops340-card{background:#fff;border:1px solid #dce8e5;border-radius:14px;padding:12px}.ops340-kpi strong{display:block;font-size:22px;color:#173d39}.ops340-kpi span{font-size:10px;color:#718480}.ops340-toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:end}.ops340-toolbar label{flex:1;min-width:180px}.ops340-list{display:grid;gap:8px}.ops340-row{border:1px solid #e0e9e7;border-radius:12px;padding:10px;display:flex;justify-content:space-between;gap:10px;align-items:center}.ops340-row b{display:block}.ops340-row small{display:block;color:#6d817d;margin-top:3px}.ops340-pill{border-radius:999px;padding:5px 8px;font-size:10px;font-weight:900;white-space:nowrap}.ops340-pill.bad{background:#fff0ee;color:#b42318}.ops340-pill.warn{background:#fff8e6;color:#8a6418}.ops340-pill.ok{background:#ecfdf3;color:#166534}.ops340-sync-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.ops340-sync-grid>div{border:1px solid #e0e9e7;border-radius:10px;padding:9px}.ops340-sync-grid small{display:block;color:#788a86;font-size:9px}.ops340-sync-grid b{display:block;margin-top:2px}.ops340-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.ops340-actions button{border:0;border-radius:10px;padding:9px 11px;font-weight:900;background:#eaf6f3;color:#0f766e}.ops340-actions button.primary{background:#0f766e;color:#fff}@media(max-width:700px){.ops340-kpis{grid-template-columns:1fr 1fr}.ops340-row{align-items:flex-start}.ops340-sync-grid{grid-template-columns:1fr}}`;document.head.appendChild(s)}
function injectNav(){
 const grid=$('#moreFunctions .more323-grid');if(grid&&!grid.querySelector('[data-go="operationsCenterV340"]')){const b=document.createElement('button');b.className='more323-card';b.dataset.go='operationsCenterV340';b.innerHTML='<span>🎯</span><b>Central operacional</b><small>Pendências e diagnóstico de sincronização</small>';grid.appendChild(b)}
}
function injectView(){
 if($('#operationsCenterV340'))return;const main=$('.app-shell')||document.body,sec=document.createElement('section');sec.id='operationsCenterV340';sec.className='view';sec.innerHTML=`<div class="view-head"><button class="back" data-go="moreFunctions">←</button><div><h2>Central operacional</h2><p>Pendências que precisam de ação e diagnóstico da sincronização.</p></div></div><div class="ops340-wrap"><div class="ops340-toolbar"><label>Empresa<select id="ops340Company"></select></label><button id="ops340Refresh" class="secondary" type="button">↻ Atualizar</button></div><div id="ops340Body"></div></div>`;main.appendChild(sec);$('#ops340Company').addEventListener('change',render);$('#ops340Refresh').addEventListener('click',render)}
function fillCompanies(){const s=$('#ops340Company');if(!s)return;const old=s.value,a=state().app;s.innerHTML='<option value="">Todas as empresas</option>'+a.companies.filter(c=>c.active!==false).map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('');s.value=[...s.options].some(o=>o.value===old)?old:''}
function openGo(id){if(id==='operationsCenterV340')return;const x=document.querySelector('[data-go="'+CSS.escape(id)+'"]');if(x){x.click();return}const v=$('#'+id);if(v){$$('.view').forEach(e=>e.classList.remove('active'));v.classList.add('active')}}
function render(){
 const body=$('#ops340Body');if(!body)return;fillCompanies();const f=$('#ops340Company')?.value||'',d=buildPendencies(f),bad=d.rows.filter(x=>x.sev==='bad').length,warn=d.rows.filter(x=>x.sev==='warn').length;
 const sync=$('#epiCloudStatus')?.textContent||'Aguardando',user=window.GestaoEpiAuth?.user?.(),tenant=window.GestaoEpiAuth?.tenant?.(),rev=localStorage.getItem(REV)||'0',dev=window.GestaoEpiAuth?.deviceId?.()||'—';
 body.innerHTML=`<div class="ops340-kpis"><div class="ops340-kpi"><strong>${d.rows.length}</strong><span>pendências totais</span></div><div class="ops340-kpi"><strong>${bad}</strong><span>prioridade alta</span></div><div class="ops340-kpi"><strong>${warn}</strong><span>atenção</span></div></div><div class="ops340-card"><h3>Diagnóstico de sincronização</h3><div class="ops340-sync-grid"><div><small>Conexão</small><b>${navigator.onLine?'Online':'Offline'}</b></div><div><small>Status atual</small><b>${esc(sync)}</b></div><div><small>Revisão do servidor</small><b>${esc(rev)}</b></div><div><small>Dispositivo</small><b>${esc(dev)}</b></div><div><small>Usuário</small><b>${esc(user?.name||user?.username||'—')}</b></div><div><small>Empresa licenciada</small><b>${esc(tenant?.name||tenant?.code||'—')}</b></div></div><div class="ops340-actions"><button class="primary" id="ops340Retry">☁️ Tentar sincronizar agora</button><button id="ops340Copy">Copiar diagnóstico</button></div></div><div class="ops340-card"><h3>Pendências</h3><div class="ops340-list">${d.rows.map((r,i)=>`<div class="ops340-row"><div><b>${esc(r.title)}</b><small>${esc(r.kind)} • ${esc(r.detail)}</small></div><button class="ops340-pill ${r.sev}" data-ops340-go="${esc(r.go||'')}">${r.sev==='bad'?'Prioridade':'Atenção'}</button></div>`).join('')||'<div class="ops340-row"><div><b>Sem pendências principais</b><small>Os controles verificados estão regulares neste momento.</small></div><span class="ops340-pill ok">OK</span></div>'}</div></div>`;
 $('#ops340Retry')?.addEventListener('click',()=>$('#epiCloudButton')?.click());
 $('#ops340Copy')?.addEventListener('click',async()=>{const txt=`Gestão EPI • diagnóstico\nConexão: ${navigator.onLine?'Online':'Offline'}\nStatus: ${sync}\nRevisão: ${rev}\nDispositivo: ${dev}\nUsuário: ${user?.name||user?.username||'—'}\nPendências: ${d.rows.length}`;try{await navigator.clipboard.writeText(txt);const t=$('#toast');if(t){t.textContent='Diagnóstico copiado.';t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2200)}}catch(_){}});
 $$('[data-ops340-go]').forEach(b=>b.addEventListener('click',()=>openGo(b.dataset.ops340Go)));
}
function open(){
 $$('section.view').forEach(v=>v.classList.remove('active'));$('#operationsCenterV340')?.classList.add('active');window.scrollTo(0,0);render();
}
function boot(){injectStyle();injectNav();injectView();document.addEventListener('click',e=>{if(e.target.closest('[data-go="operationsCenterV340"]')){e.preventDefault();open()}},true);document.addEventListener('gestao-epi-sync-applied',()=>setTimeout(render,80));document.addEventListener('auditar-epi-data-changed',()=>setTimeout(render,120));window.addEventListener('online',()=>setTimeout(render,80));window.addEventListener('offline',()=>setTimeout(render,80));[500,1500,3000].forEach(ms=>setTimeout(()=>{injectNav();injectView()},ms))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();