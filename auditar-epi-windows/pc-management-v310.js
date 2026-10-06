(()=>{
'use strict';
const CACHE='auditarEpiGestaoCacheV1';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function read(){
  try{
    const r=JSON.parse(localStorage.getItem(CACHE)||'{}');
    r.app=r.app&&typeof r.app==='object'?r.app:{};
    for(const k of ['companies','workers','epis','deliveries'])r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];
    r.stock=r.stock&&typeof r.stock==='object'?r.stock:{};
    r.stock.movements=Array.isArray(r.stock.movements)?r.stock.movements:[];
    r.stock.minimums=r.stock.minimums&&typeof r.stock.minimums==='object'?r.stock.minimums:{};
    return r;
  }catch(_){return {app:{companies:[],workers:[],epis:[],deliveries:[]},stock:{movements:[],minimums:{}}}}
}
function companyFilter(){return $('#globalCompany')?.value||''}
function dayKey(d){return new Date(d).toISOString().slice(0,10)}
function fmt(n){return new Intl.NumberFormat('pt-BR').format(Number(n||0))}
function datePt(v){try{return new Intl.DateTimeFormat('pt-BR',{day:'2-digit',month:'2-digit'}).format(new Date(v))}catch{return '—'}}
function cutoff(days){return Date.now()-days*86400000}
function within(v,days){const t=Date.parse(v||'');return Number.isFinite(t)&&t>=cutoff(days)}
function balance(snapshot,companyId,epiId){
  return snapshot.stock.movements.filter(m=>m.companyId===companyId&&m.epiId===epiId).reduce((s,m)=>s+Number(m.delta||0),0);
}
function stockRows(snapshot,filter){
  const keys=new Set(Object.keys(snapshot.stock.minimums||{}));
  snapshot.stock.movements.forEach(m=>{if(m.companyId&&m.epiId)keys.add(m.companyId+'::'+m.epiId)});
  const cm=new Map(snapshot.app.companies.map(c=>[c.id,c])),em=new Map(snapshot.app.epis.map(e=>[e.id,e]));
  return [...keys].map(key=>{
    const p=key.split('::'),companyId=p.shift(),epiId=p.join('::');
    return {companyId,epiId,company:cm.get(companyId),epi:em.get(epiId),saldo:balance(snapshot,companyId,epiId),min:Number(snapshot.stock.minimums[key]??5)};
  }).filter(x=>(!filter||x.companyId===filter)&&x.epi);
}
function dueRows(snapshot,filter){
  const latest=new Map(),em=new Map(snapshot.app.epis.map(e=>[e.id,e])),wm=new Map(snapshot.app.workers.map(w=>[w.id,w]));
  snapshot.app.deliveries.forEach(d=>{
    if(d.cancelled===true||filter&&d.companyId!==filter)return;
    (d.items||[]).forEach(i=>{
      const e=em.get(i.epiId);if(!e||!Number(e.cycle||0))return;
      const key=d.workerId+'::'+i.epiId,current=latest.get(key);
      if(!current||String(d.createdAt||'')>String(current.createdAt||''))latest.set(key,{workerId:d.workerId,epiId:i.epiId,companyId:d.companyId,createdAt:d.createdAt,qty:Number(i.qty||1)});
    });
  });
  return [...latest.values()].map(r=>{
    const e=em.get(r.epiId),w=wm.get(r.workerId),due=Date.parse(r.createdAt||0)+Number(e?.cycle||0)*86400000;
    return {...r,epi:e,worker:w,due,days:Math.ceil((due-Date.now())/86400000)};
  }).filter(r=>r.worker&&r.worker.active!==false&&r.days<=15).sort((a,b)=>a.days-b.days);
}
function trend(snapshot,filter){
  const out=[],today=new Date();today.setHours(0,0,0,0);
  for(let i=6;i>=0;i--){const d=new Date(today);d.setDate(d.getDate()-i);out.push({key:dayKey(d),label:new Intl.DateTimeFormat('pt-BR',{weekday:'short'}).format(d).replace('.',''),count:0})}
  const map=new Map(out.map(x=>[x.key,x]));
  snapshot.app.deliveries.forEach(d=>{if(d.cancelled===true||filter&&d.companyId!==filter)return;const x=map.get(String(d.createdAt||'').slice(0,10));if(x)x.count++});
  return out;
}
function topEpis(snapshot,filter){
  const score=new Map(),em=new Map(snapshot.app.epis.map(e=>[e.id,e]));
  snapshot.app.deliveries.filter(d=>d.cancelled!==true&&within(d.createdAt,30)&&(!filter||d.companyId===filter)).forEach(d=>(d.items||[]).forEach(i=>score.set(i.epiId,(score.get(i.epiId)||0)+Number(i.qty||0))));
  return [...score.entries()].map(([id,qty])=>({epi:em.get(id),qty})).filter(x=>x.epi).sort((a,b)=>b.qty-a.qty).slice(0,5);
}
function quality(snapshot,filter){
  const workers=snapshot.app.workers.filter(w=>w.active!==false&&(!filter||w.companyId===filter));
  const epis=snapshot.app.epis;
  return {
    workersIncomplete:workers.filter(w=>!String(w.role||'').trim()||!String(w.sector||'').trim()).length,
    episNoCa:epis.filter(e=>!String(e.ca||'').trim()).length
  };
}
function clickView(id){const b=$('.sidebar .nav[data-view="'+id+'"]');if(b)b.click()}
function styles(){
  if($('#pc310Style'))return;
  const s=document.createElement('style');s.id='pc310Style';s.textContent=`
  @media(min-width:1000px){
    .pc310-wrap{display:grid;gap:12px;margin:12px 0 18px}
    .pc310-top{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}
    .pc310-kpi{background:#fff;border:1px solid #dde8e5;border-radius:14px;padding:13px 14px;box-shadow:0 6px 20px rgba(20,67,61,.045);min-width:0}
    .pc310-kpi span{display:block;color:#718480;font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.06em}
    .pc310-kpi strong{display:block;margin:4px 0 1px;font-size:24px;color:#193e39;letter-spacing:-.04em}.pc310-kpi small{font-size:9px;color:#8b9a97}
    .pc310-kpi.warn strong{color:#b45309}.pc310-kpi.danger strong{color:#b42318}
    .pc310-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:10px}
    .pc310-panel{background:#fff;border:1px solid #dde8e5;border-radius:14px;padding:14px;min-width:0}
    .pc310-head{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:10px}.pc310-head b{font-size:12px;color:#234b45}.pc310-head small{font-size:9px;color:#7a8c88}
    .pc310-bars{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;align-items:end;height:112px;padding-top:8px}
    .pc310-barcol{height:100%;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:5px}
    .pc310-bar{width:min(38px,70%);min-height:3px;border-radius:7px 7px 3px 3px;background:linear-gradient(180deg,#14ad8c,#087663);position:relative}
    .pc310-barcol b{font-size:9px;color:#496963}.pc310-barcol small{font-size:8px;color:#899894;text-transform:capitalize}
    .pc310-list{display:grid;gap:6px}.pc310-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center;padding:8px 9px;border-radius:10px;background:#f7faf9;border:1px solid #edf2f0}
    .pc310-row b{display:block;font-size:10px;color:#2d514c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.pc310-row small{display:block;font-size:8px;color:#7a8d89;margin-top:2px}.pc310-row strong{font-size:11px;color:#0c7765}
    .pc310-attn{display:grid;grid-template-columns:1fr 1fr;gap:10px}.pc310-attn .pc310-panel{min-height:122px}
    .pc310-action{border:0;background:#edf8f5;color:#0c7765;border-radius:9px;padding:7px 9px;font-size:9px;font-weight:900;cursor:pointer}
    .pc310-chip{display:inline-flex;border-radius:999px;padding:3px 7px;font-size:8px;font-weight:900}.pc310-chip.red{background:#feeceb;color:#a9362b}.pc310-chip.amber{background:#fff4df;color:#a15c06}
    .pc310-empty{font-size:9px;color:#859590;padding:10px 2px}
    .view .card,.view .panel{border-color:#dfe9e6!important}.view input,.view select,.view textarea{border-radius:9px!important}
  }
  `;document.head.appendChild(s);
}
function render(){
  styles();
  const dash=$('#dashboard');if(!dash)return;
  let wrap=$('#pc310Dashboard');
  if(!wrap){wrap=document.createElement('div');wrap.id='pc310Dashboard';wrap.className='pc310-wrap';const shortcuts=$('#pc280Shortcuts');shortcuts?.insertAdjacentElement('afterend',wrap);if(!shortcuts)dash.prepend(wrap)}
  const s=read(),filter=companyFilter();
  const deliveries30=s.app.deliveries.filter(d=>d.cancelled!==true&&within(d.createdAt,30)&&(!filter||d.companyId===filter));
  const units30=deliveries30.reduce((sum,d)=>sum+(d.items||[]).reduce((q,i)=>q+Number(i.qty||0),0),0);
  const served=new Set(deliveries30.map(d=>d.workerId).filter(Boolean)).size;
  const active=s.app.workers.filter(w=>w.active!==false&&(!filter||w.companyId===filter)).length;
  const low=stockRows(s,filter).filter(r=>r.saldo<=r.min).sort((a,b)=>a.saldo-b.saldo);
  const due=dueRows(s,filter),overdue=due.filter(r=>r.days<0);
  const top=topEpis(s,filter),tr=trend(s,filter),q=quality(s,filter),max=Math.max(1,...tr.map(x=>x.count));
  const lowRows=low.slice(0,5).map(r=>'<div class="pc310-row"><div><b>'+esc(r.epi.name)+'</b><small>'+esc(r.company?.name||'')+' • mín. '+fmt(r.min)+'</small></div><span class="pc310-chip '+(r.saldo<0?'red':'amber')+'">'+fmt(r.saldo)+' un.</span></div>').join('');
  const dueRowsHtml=due.slice(0,5).map(r=>'<div class="pc310-row"><div><b>'+esc(r.worker.name)+' • '+esc(r.epi.name)+'</b><small>'+datePt(r.due)+'</small></div><span class="pc310-chip '+(r.days<0?'red':'amber')+'">'+(r.days<0?Math.abs(r.days)+'d atrasado':r.days+'d')+'</span></div>').join('');
  wrap.innerHTML=
    '<div class="pc310-top">'+
      '<div class="pc310-kpi"><span>Entregas • 30 dias</span><strong>'+fmt(deliveries30.length)+'</strong><small>'+fmt(served)+' trabalhadores atendidos</small></div>'+
      '<div class="pc310-kpi"><span>Unidades entregues</span><strong>'+fmt(units30)+'</strong><small>últimos 30 dias</small></div>'+
      '<div class="pc310-kpi"><span>Trabalhadores ativos</span><strong>'+fmt(active)+'</strong><small>no filtro atual</small></div>'+
      '<div class="pc310-kpi '+(low.length?'warn':'')+'"><span>Estoque em atenção</span><strong>'+fmt(low.length)+'</strong><small>no mínimo ou abaixo</small></div>'+
      '<div class="pc310-kpi '+(overdue.length?'danger':'')+'"><span>Trocas vencidas</span><strong>'+fmt(overdue.length)+'</strong><small>estimativa pelo ciclo</small></div>'+
    '</div>'+
    '<div class="pc310-grid">'+
      '<div class="pc310-panel"><div class="pc310-head"><b>Entregas nos últimos 7 dias</b><small>movimentação diária</small></div><div class="pc310-bars">'+
        tr.map(x=>'<div class="pc310-barcol"><b>'+x.count+'</b><div class="pc310-bar" style="height:'+Math.max(3,Math.round(x.count/max*78))+'px"></div><small>'+esc(x.label)+'</small></div>').join('')+
      '</div></div>'+
      '<div class="pc310-panel"><div class="pc310-head"><b>EPIs mais entregues • 30 dias</b><small>unidades</small></div><div class="pc310-list">'+
        (top.length?top.map(x=>'<div class="pc310-row"><div><b>'+esc(x.epi.name)+'</b><small>'+(x.epi.ca?'CA '+esc(x.epi.ca):'Sem CA informado')+'</small></div><strong>'+fmt(x.qty)+'</strong></div>').join(''):'<div class="pc310-empty">Sem entregas no período.</div>')+
      '</div></div>'+
    '</div>'+
    '<div class="pc310-attn">'+
      '<div class="pc310-panel"><div class="pc310-head"><b>Estoque que exige atenção</b><button class="pc310-action" data-pc310-go="stock">Abrir estoque</button></div><div class="pc310-list">'+(lowRows||'<div class="pc310-empty">Nenhum estoque crítico.</div>')+'</div></div>'+
      '<div class="pc310-panel"><div class="pc310-head"><b>Próximas trocas</b><button class="pc310-action" data-pc310-go="replacementPc">Ver trocas</button></div><div class="pc310-list">'+(dueRowsHtml||'<div class="pc310-empty">Nenhuma troca prevista nos próximos 15 dias.</div>')+'</div></div>'+
    '</div>'+
    '<div class="pc310-panel"><div class="pc310-head"><b>Qualidade dos cadastros</b><small>melhora relatórios e rastreabilidade</small></div><div class="pc310-row"><div><b>'+fmt(q.workersIncomplete)+' trabalhador(es) sem cargo ou setor completo</b><small>'+fmt(q.episNoCa)+' EPI(s) sem CA informado</small></div><button class="pc310-action" data-pc310-go="dataQualityPc">Revisar dados</button></div></div>';
  wrap.querySelectorAll('[data-pc310-go]').forEach(b=>b.onclick=()=>clickView(b.dataset.pc310Go));
}
let timer=0;
function schedule(){clearTimeout(timer);timer=setTimeout(render,80)}
function boot(){
  styles();render();
  $('#globalCompany')?.addEventListener('change',schedule);
  document.addEventListener('click',e=>{if(e.target.closest('.sidebar .nav[data-view="dashboard"]'))setTimeout(render,80)});
  window.addEventListener('storage',e=>{if(e.key===CACHE)schedule()});
  window.addEventListener('focus',schedule);
  setInterval(()=>{if($('#dashboard')?.classList.contains('active'))render()},30000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();