(()=>{
'use strict';
const APP_KEY='auditarEpiV1';
const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clean=(v='')=>String(v??'').replace(/\s+/g,' ').trim();
const norm=(v='')=>clean(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const digits=v=>String(v??'').replace(/\D/g,'');
let filter='all',busy=false;

function app(){try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')}}catch{return {companies:[],workers:[],epis:[],deliveries:[]}}}
function save(a){localStorage.setItem(APP_KEY,JSON.stringify(a));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'ca-center-v330'}}))}
function toast(m){const e=$('#toast');if(!e)return alert(m);e.textContent=m;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2800)}
function token(){return window.GestaoEpiAuth?.token?.()||''}
function parseDate(v){
  const s=clean(v);if(!s)return null;
  let m=s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if(m){const d=new Date(Number(m[3]),Number(m[2])-1,Number(m[1]),12);return Number.isNaN(d.getTime())?null:d}
  m=s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if(m){const d=new Date(Number(m[1]),Number(m[2])-1,Number(m[3]),12);return Number.isNaN(d.getTime())?null:d}
  const d=new Date(s);return Number.isNaN(d.getTime())?null:d;
}
function fmtDate(v){
  const d=parseDate(v);if(!d)return clean(v)||'—';
  return d.toLocaleDateString('pt-BR');
}
function daysTo(v){
  const d=parseDate(v);if(!d)return null;
  const now=new Date();now.setHours(12,0,0,0);d.setHours(12,0,0,0);
  return Math.ceil((d-now)/86400000);
}
function info(e){
  const ca=digits(e.ca),validity=clean(e.caValidity),status=clean(e.caStatus),checked=clean(e.caCheckedAt),days=daysTo(validity),st=norm(status);
  let key='ok',label='Regular',cls='ok';
  if(!ca){key='no-ca';label='Sem CA';cls='warn'}
  else if(/venc|expir|cancel|suspens|inativ|invalid|inval/.test(st)||(days!=null&&days<0)){key='expired';label='Vencido/irregular';cls='bad'}
  else if(!validity){key='no-validity';label='Sem validade';cls='warn'}
  else if(days<=30){key='30';label='Vence em '+Math.max(0,days)+' dia(s)';cls='bad'}
  else if(days<=60){key='60';label='Vence em '+days+' dia(s)';cls='warn'}
  else if(days<=90){key='90';label='Vence em '+days+' dia(s)';cls='warn'}
  if(ca&&!checked&&key==='ok'){key='unchecked';label='Sem consulta recente';cls='warn'}
  return {ca,validity,status,checked,days,key,label,cls};
}
function matchesFilter(e){
  const x=info(e);
  if(filter==='all')return true;
  if(filter==='expired')return x.key==='expired';
  if(filter==='30')return x.days!=null&&x.days>=0&&x.days<=30;
  if(filter==='60')return x.days!=null&&x.days>=0&&x.days<=60;
  if(filter==='90')return x.days!=null&&x.days>=0&&x.days<=90;
  if(filter==='no-validity')return !!x.ca&&!x.validity;
  if(filter==='unchecked')return !!x.ca&&!x.checked;
  return true;
}
function stats(rows){
  const out={total:rows.length,expired:0,d30:0,d90:0,noValidity:0,unchecked:0};
  rows.forEach(e=>{const x=info(e);if(x.key==='expired')out.expired++;if(x.days!=null&&x.days>=0&&x.days<=30)out.d30++;if(x.days!=null&&x.days>=0&&x.days<=90)out.d90++;if(x.ca&&!x.validity)out.noValidity++;if(x.ca&&!x.checked)out.unchecked++;});
  return out;
}
function styles(){
  if($('#ca330Style'))return;
  const s=document.createElement('style');s.id='ca330Style';s.textContent=
  '.ca330-wrap{display:grid;gap:12px}.ca330-toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:end}.ca330-toolbar label{display:grid;gap:4px;font-size:11px;font-weight:800;color:#526b67;flex:1;min-width:170px}.ca330-toolbar input{min-height:44px;border:1px solid #cfdfdc;border-radius:11px;padding:8px 10px}.ca330-toolbar button{min-height:44px;border-radius:11px;padding:0 12px;font-weight:850}.ca330-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.ca330-kpi{background:#fff;border:1px solid #dce8e5;border-radius:13px;padding:10px;text-align:center}.ca330-kpi strong{display:block;font-size:20px;color:#173d39}.ca330-kpi span{font-size:10px;color:#6a7f7c}.ca330-filters{display:flex;gap:6px;overflow:auto;padding-bottom:2px}.ca330-filter{white-space:nowrap;border:1px solid #cfe0dc;background:#fff;border-radius:999px;padding:7px 10px;font-size:11px;font-weight:850}.ca330-filter.active{background:#0f766e;color:#fff;border-color:#0f766e}.ca330-list{display:grid;gap:8px}.ca330-row{background:#fff;border:1px solid #dbe8e5;border-radius:13px;padding:11px;display:grid;grid-template-columns:1fr auto;gap:8px}.ca330-row.bad{border-color:#efaaaa;background:#fff7f7}.ca330-row.warn{border-color:#ecd08b;background:#fffaf0}.ca330-row b{display:block;color:#173d39}.ca330-row small{display:block;margin-top:4px;color:#657b77;line-height:1.45}.ca330-pill{display:inline-block;margin-top:6px;border-radius:999px;padding:4px 7px;font-size:10px;font-weight:900;background:#eaf8ef;color:#176b36}.ca330-pill.bad{background:#feecec;color:#9f2929}.ca330-pill.warn{background:#fff1d6;color:#8a5d10}.ca330-refresh{align-self:start;border:1px solid #cfe0dc;background:#fff;border-radius:10px;min-height:38px;padding:0 10px;font-weight:850}.ca330-alert-box{margin:10px 0 12px;padding:11px;border:1px solid #dbe8e5;border-radius:14px;background:#fff}.ca330-alert-box h4{margin:0 0 7px}.ca330-alert-grid{display:flex;gap:7px;flex-wrap:wrap}.ca330-alert-chip{padding:6px 9px;border-radius:999px;font-size:10px;font-weight:850;background:#edf8f5;color:#315f59}.ca330-alert-chip.bad{background:#feecec;color:#9f2929}.ca330-alert-chip.warn{background:#fff1d6;color:#8a5d10}@media(max-width:520px){.ca330-kpis{grid-template-columns:repeat(2,1fr)}.ca330-row{grid-template-columns:1fr}.ca330-refresh{width:100%}}';
  document.head.appendChild(s);
}
function inject(){
  const main=$('.app-shell');if(!main)return;
  if(!$('#caCenterV330')){
    const sec=document.createElement('section');sec.id='caCenterV330';sec.className='view';
    sec.innerHTML='<div class="view-head"><button class="back" data-go="moreFunctions">←</button><div><h2>Central de CA</h2><p>Validade, situação e conferência dos Certificados de Aprovação.</p></div></div><div class="ca330-wrap"><div class="ca330-toolbar"><label>Buscar EPI ou CA<input id="ca330Search" placeholder="Ex.: luva ou 12244"></label><button id="ca330UpdateAll" class="primary" type="button">↻ Atualizar CAs</button></div><div class="ca330-kpis"><div class="ca330-kpi"><strong id="ca330Total">0</strong><span>EPIs cadastrados</span></div><div class="ca330-kpi"><strong id="ca330Expired">0</strong><span>vencidos/irregulares</span></div><div class="ca330-kpi"><strong id="ca33030">0</strong><span>vencem em 30 dias</span></div><div class="ca330-kpi"><strong id="ca330NoValidity">0</strong><span>sem validade</span></div></div><div class="ca330-filters" id="ca330Filters"><button class="ca330-filter active" data-ca-filter="all">Todos</button><button class="ca330-filter" data-ca-filter="expired">Vencidos</button><button class="ca330-filter" data-ca-filter="30">30 dias</button><button class="ca330-filter" data-ca-filter="60">60 dias</button><button class="ca330-filter" data-ca-filter="90">90 dias</button><button class="ca330-filter" data-ca-filter="no-validity">Sem validade</button><button class="ca330-filter" data-ca-filter="unchecked">Sem consulta</button></div><div id="ca330Status"></div><div id="ca330List" class="ca330-list"></div></div>';
    main.appendChild(sec);
    $('#ca330Search')?.addEventListener('input',render);
    $('#ca330UpdateAll')?.addEventListener('click',updateAll);
    $('#ca330Filters')?.addEventListener('click',e=>{const b=e.target.closest('[data-ca-filter]');if(!b)return;filter=b.dataset.caFilter;$$('[data-ca-filter]').forEach(x=>x.classList.toggle('active',x===b));render()});
  }
  const grid=$('#moreFunctions .more323-grid');
  if(grid&&!grid.querySelector('[data-go="caCenterV330"]')){
    const b=document.createElement('button');b.className='more323-card';b.dataset.go='caCenterV330';b.innerHTML='<span>🛡️</span><b>Central de CA</b><small>Validade e situação dos CAs</small>';grid.appendChild(b);
  }
  injectAlerts();
}
function injectAlerts(){
  const view=$('#moreAlerts');if(!view||$('#ca330AlertBox'))return;
  const box=document.createElement('div');box.id='ca330AlertBox';box.className='ca330-alert-box';
  const list=$('#more323AlertList');if(list)list.before(box);else view.appendChild(box);
  renderAlerts();
}
function renderAlerts(){
  const box=$('#ca330AlertBox');if(!box)return;
  const rows=(app().epis||[]).filter(e=>e.active!==false),st=stats(rows);
  const attention=rows.map(e=>({e,x:info(e)})).filter(r=>r.x.key==='expired'||(r.x.days!=null&&r.x.days>=0&&r.x.days<=90)||r.x.key==='no-validity').sort((a,b)=>(a.x.days??99999)-(b.x.days??99999)).slice(0,8);
  box.innerHTML='<h4>🛡️ Alertas de CA</h4><div class="ca330-alert-grid"><span class="ca330-alert-chip bad">'+st.expired+' vencido(s)/irregular(es)</span><span class="ca330-alert-chip warn">'+st.d30+' vence(m) em 30 dias</span><span class="ca330-alert-chip warn">'+st.noValidity+' sem validade</span></div>'+(attention.length?'<div style="margin-top:8px">'+attention.map(r=>'<div style="padding:6px 0;border-top:1px solid #edf2f1"><b style="font-size:11px">'+esc(r.e.name)+'</b><small style="display:block;color:#6a7f7c">'+(r.x.ca?'CA '+esc(r.x.ca):'Sem CA')+' • '+esc(r.x.label)+(r.x.validity?' • '+esc(fmtDate(r.x.validity)):'')+'</small></div>').join('')+'</div>':'');
}
function render(){
  const root=$('#ca330List');if(!root)return;
  const all=(app().epis||[]).filter(e=>e.active!==false),st=stats(all),q=norm($('#ca330Search')?.value||'');
  $('#ca330Total').textContent=st.total;$('#ca330Expired').textContent=st.expired;$('#ca33030').textContent=st.d30;$('#ca330NoValidity').textContent=st.noValidity;
  const rows=all.filter(matchesFilter).filter(e=>!q||[e.name,e.ca,e.model,e.size,e.caStatus].some(v=>norm(v).includes(q))).sort((a,b)=>{const A=info(a),B=info(b);const rank=x=>x.key==='expired'?0:x.key==='30'?1:x.key==='60'?2:x.key==='90'?3:x.key==='no-validity'?4:x.key==='unchecked'?5:6;return rank(A)-rank(B)||String(a.name||'').localeCompare(String(b.name||''))});
  root.innerHTML=rows.length?rows.map(e=>{const x=info(e);return '<div class="ca330-row '+x.cls+'"><div><b>'+esc(e.name||'EPI')+'</b><small>'+(x.ca?'CA '+esc(x.ca):'CA não informado')+(x.validity?' • Validade '+esc(fmtDate(x.validity)):' • Validade não informada')+(x.status?' • '+esc(x.status):'')+(e.model?' • '+esc(e.model):'')+'</small><span class="ca330-pill '+x.cls+'">'+esc(x.label)+'</span><small>'+(x.checked?'Consultado em '+esc(fmtDate(x.checked)):'Ainda não consultado nesta base')+'</small></div><button class="ca330-refresh" data-ca-refresh="'+esc(e.id)+'" type="button">↻ Atualizar</button></div>'}).join(''):'<div class="empty">Nenhum EPI encontrado neste filtro.</div>';
}
async function validate(items){
  const t=token();if(!t)throw new Error('Faça login para consultar os CAs.');if(!navigator.onLine)throw new Error('Sem internet para consultar os CAs.');
  const payloadItems=items.filter(x=>x.ca).map(x=>({ca:x.ca,name:x.name,manufacturer:x.model||''}));
  if(!payloadItems.length)return [];
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),25000);
  try{
    const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'tenant_ai_assistant',authToken:t,payload:{mode:'ca_validate',items:payloadItems}}),signal:controller.signal});
    const data=await res.json();if(!data?.ok)throw new Error(data?.message||'Falha na consulta dos CAs.');
    return Array.isArray(data.result?.checks)?data.result.checks:[];
  }finally{clearTimeout(timer)}
}
function applyChecks(a,checks){
  const map=new Map((checks||[]).map(c=>[digits(c.ca),c])),now=new Date().toISOString();let changed=0;
  (a.epis||[]).forEach(e=>{const c=map.get(digits(e.ca));if(!c)return;e.caVerified=c.found===true;e.caStatus=clean(c.status);e.caCheckedAt=now;e.caSource=clean(c.sourceUrl||e.caSource||'');e.caValidity=clean(c.validity||'');e.updatedAt=now;changed++});
  return changed;
}
async function updateOne(id){
  if(busy)return;const a=app(),e=(a.epis||[]).find(x=>x.id===id);if(!e)return;if(!e.ca)return toast('Este EPI não possui CA informado.');
  busy=true;try{$('#ca330Status').innerHTML='<div class="more323-row"><b>Consultando CA '+esc(e.ca)+'…</b></div>';const checks=await validate([e]);const n=applyChecks(a,checks);if(!n)throw new Error('A consulta não retornou dados para este CA.');save(a);toast('CA atualizado.')}catch(err){toast(err?.message||'Não foi possível atualizar o CA.')}finally{busy=false;$('#ca330Status').innerHTML='';render();renderAlerts()}
}
async function updateAll(){
  if(busy)return;const a=app(),rows=(a.epis||[]).filter(e=>e.active!==false&&digits(e.ca));if(!rows.length)return toast('Nenhum EPI com CA para consultar.');
  busy=true;const btn=$('#ca330UpdateAll');if(btn)btn.disabled=true;let total=0;
  try{
    for(let i=0;i<rows.length;i+=12){
      const batch=rows.slice(i,i+12);$('#ca330Status').innerHTML='<div class="more323-row"><b>Atualizando CAs…</b><small>'+Math.min(i+batch.length,rows.length)+' de '+rows.length+'</small></div>';
      const checks=await validate(batch);total+=applyChecks(a,checks);save(a);
    }
    toast(total+' CA(s) atualizado(s).');
  }catch(err){toast(err?.message||'Falha ao atualizar os CAs.')}finally{busy=false;if(btn)btn.disabled=false;$('#ca330Status').innerHTML='';render();renderAlerts()}
}
function boot(){
  styles();inject();renderAlerts();
  [250,700,1500,2600].forEach(ms=>setTimeout(()=>{inject();renderAlerts()},ms));
  document.addEventListener('click',e=>{
    const go=e.target.closest?.('[data-go]')?.dataset.go;
    if(go==='caCenterV330')setTimeout(render,40);
    if(go==='moreAlerts')setTimeout(()=>{injectAlerts();renderAlerts()},60);
    const b=e.target.closest?.('[data-ca-refresh]');if(b){e.preventDefault();updateOne(b.dataset.caRefresh)}
  },true);
  document.addEventListener('auditar-epi-data-changed',()=>{if($('#caCenterV330')?.classList.contains('active'))render();renderAlerts()});
  document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(()=>{inject();renderAlerts()},120));
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();