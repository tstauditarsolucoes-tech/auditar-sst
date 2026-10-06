(()=>{
'use strict';
const APP='auditarEpiV1',STOCK='auditarEpiStockV1';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function read(k,f){try{return {...f,...JSON.parse(localStorage.getItem(k)||'{}')}}catch{return f}}
function app(){return read(APP,{companies:[],workers:[],epis:[],deliveries:[]})}
function stock(){return read(STOCK,{movements:[],minimums:{}})}

function styles(){
  if($('#moreShortcutV323Style'))return;
  const s=document.createElement('style');s.id='moreShortcutV323Style';s.textContent=`
    .bottom-nav{grid-template-columns:repeat(5,1fr)!important}
    .more323-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .more323-card{
      border:1px solid #d7e4e1;background:#fff;border-radius:18px;padding:17px 15px;
      min-height:132px;text-align:left;color:#202d3d;box-shadow:0 6px 20px rgba(22,73,64,.045)
    }
    .more323-card span{display:block;font-size:35px;line-height:1;margin-bottom:12px}
    .more323-card b{display:block;font-size:18px;line-height:1.12;margin-bottom:6px}
    .more323-card small{display:block;font-size:12px;line-height:1.3;color:#70847f}
    .more323-card:active{transform:translateY(1px)}
    .more323-list{display:grid;gap:9px}
    .more323-row{background:#fff;border:1px solid #dbe7e4;border-radius:14px;padding:12px}
    .more323-row b{display:block;color:#213f3a;font-size:13px}
    .more323-row small{display:block;color:#71847f;font-size:10.5px;line-height:1.4;margin-top:3px}
    .more323-kpis{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-bottom:11px}
    .more323-kpi{background:#fff;border:1px solid #dbe7e4;border-radius:14px;padding:12px;text-align:center}
    .more323-kpi strong{display:block;font-size:23px;color:#173f39}
    .more323-kpi span{font-size:10px;color:#71847f}
    .more323-alert.bad{border-left:4px solid #c33}.more323-alert.warn{border-left:4px solid #c98917}
    #bottomNav [data-go="moreFunctions"] span{font-size:22px}
    @media(max-width:390px){
      .more323-grid{gap:9px}.more323-card{min-height:122px;padding:14px 12px}
      .more323-card b{font-size:16px}.more323-card small{font-size:11px}
    }
  `;document.head.appendChild(s);
}

function injectViews(){
  const main=$('.app-shell')||$('main');if(!main)return;
  if(!$('#moreFunctions')){
    const sec=document.createElement('section');sec.id='moreFunctions';sec.className='view';
    sec.innerHTML=`
      <div class="view-head"><button class="back" data-go="home">←</button><div><h2>Mais funções</h2><p>Cadastros e controles do Gestão EPI.</p></div></div>
      <div class="more323-grid">
        <button class="more323-card" data-go="epiReturn"><span>↩️</span><b>Devoluções</b><small>Volta ou não ao estoque</small></button>
        <button class="more323-card" data-go="epiHeld"><span>🎒</span><b>EPIs em posse</b><small>Por colaborador</small></button>
        <button class="more323-card" data-go="stock"><span>📦</span><b>Estoque</b><small>Saldo e movimentações</small></button>
        <button class="more323-card" data-go="history"><span>📋</span><b>Histórico</b><small>Entregas registradas</small></button>
        <button class="more323-card" data-go="workers"><span>👷</span><b>Funcionários</b><small>Cadastro e biometria</small></button>
        <button class="more323-card" data-go="importWorkers"><span>📥</span><b>Importar</b><small>PDF, Excel e CSV</small></button>
        <button class="more323-card" data-go="epis"><span>🦺</span><b>Cadastro de EPIs</b><small>CA, modelo e durabilidade</small></button>
        <button class="more323-card" data-go="companies"><span>🏢</span><b>Empresas</b><small>Cadastro de empresas</small></button>
        <button class="more323-card" data-go="moreSectors"><span>🏭</span><b>Setores</b><small>Visão por área</small></button>
        <button class="more323-card" data-go="moreAlerts"><span>🔔</span><b>Alertas</b><small>Trocas e estoque</small></button>
      </div>`;
    main.appendChild(sec);
  }
  if(!$('#moreSectors')){
    const sec=document.createElement('section');sec.id='moreSectors';sec.className='view';
    sec.innerHTML='<div class="view-head"><button class="back" data-go="moreFunctions">←</button><div><h2>Setores</h2><p>Visão dos trabalhadores por área.</p></div></div><div id="more323SectorList" class="more323-list"></div>';
    main.appendChild(sec);
  }
  if(!$('#moreAlerts')){
    const sec=document.createElement('section');sec.id='moreAlerts';sec.className='view';
    sec.innerHTML='<div class="view-head"><button class="back" data-go="moreFunctions">←</button><div><h2>Alertas</h2><p>Trocas próximas e estoque em atenção.</p></div></div><div class="more323-kpis"><div class="more323-kpi"><strong id="more323Low">0</strong><span>estoques baixos</span></div><div class="more323-kpi"><strong id="more323Due">0</strong><span>trocas próximas/vencidas</span></div></div><div id="more323AlertList" class="more323-list"></div>';
    main.appendChild(sec);
  }
}

function injectNav(){
  const nav=$('#bottomNav');if(!nav||nav.querySelector('[data-go="moreFunctions"]'))return;
  const b=document.createElement('button');b.type='button';b.dataset.go='moreFunctions';
  b.innerHTML='<span>☰</span>Mais';
  nav.appendChild(b);
}

function renderSectors(){
  const root=$('#more323SectorList');if(!root)return;
  const a=app(),companies=new Map((a.companies||[]).map(c=>[c.id,c.name]));
  const map=new Map();
  (a.workers||[]).filter(w=>w.active!==false).forEach(w=>{
    const sector=String(w.sector||'Sem setor informado').trim()||'Sem setor informado';
    const key=(w.companyId||'')+'::'+sector;
    const row=map.get(key)||{sector,company:companies.get(w.companyId)||'Empresa não informada',count:0,roles:new Set()};
    row.count++;if(w.role)row.roles.add(w.role);map.set(key,row);
  });
  const rows=[...map.values()].sort((x,y)=>x.company.localeCompare(y.company)||x.sector.localeCompare(y.sector));
  root.innerHTML=rows.length?rows.map(r=>`<div class="more323-row"><b>${esc(r.sector)} • ${r.count} trabalhador(es)</b><small>${esc(r.company)}${r.roles.size?' • '+esc([...r.roles].slice(0,4).join(', ')):''}</small></div>`).join(''):'<div class="empty">Nenhum setor informado nos cadastros.</div>';
}

function latestDeliveryFor(a,workerId,epiId){
  return (a.deliveries||[]).filter(d=>d.workerId===workerId&&d.cancelled!==true&&(d.items||[]).some(i=>i.epiId===epiId))
    .sort((x,y)=>String(y.createdAt||'').localeCompare(String(x.createdAt||'')))[0]||null;
}
function heldQty(a,s,workerId,epiId){
  let delivered=0,returned=0;
  (a.deliveries||[]).filter(d=>d.workerId===workerId&&d.cancelled!==true).forEach(d=>(d.items||[]).forEach(i=>{if(i.epiId===epiId)delivered+=Number(i.qty||0)}));
  (s.movements||[]).forEach(m=>{
    const note=String(m.note||'');
    if(m.epiId===epiId&&note.includes('[DEVOLUÇÃO EPI]')&&note.includes('workerId:'+workerId)){
      const q=Number((note.match(/qtd:([^|]+)/)||[])[1]||0);returned+=q;
    }
  });
  return Math.max(0,delivered-returned);
}
function balance(s,companyId,epiId){return (s.movements||[]).filter(m=>m.companyId===companyId&&m.epiId===epiId).reduce((n,m)=>n+Number(m.delta||0),0)}

function renderAlerts(){
  const root=$('#more323AlertList');if(!root)return;
  const a=app(),s=stock(),alerts=[];
  const comps=new Map((a.companies||[]).map(c=>[c.id,c.name])),epis=new Map((a.epis||[]).map(e=>[e.id,e]));
  const keys=new Set(Object.keys(s.minimums||{}));
  (s.movements||[]).forEach(m=>{if(m.companyId&&m.epiId)keys.add(m.companyId+'::'+m.epiId)});
  let low=0,due=0;
  keys.forEach(key=>{
    const i=key.indexOf('::');if(i<0)return;const companyId=key.slice(0,i),epiId=key.slice(i+2),e=epis.get(epiId);if(!e)return;
    const saldo=balance(s,companyId,epiId),min=Number((s.minimums||{})[key]??5);
    if(saldo<=min){low++;alerts.push({cls:saldo<=0?'bad':'warn',title:'Estoque baixo • '+e.name,sub:(comps.get(companyId)||'Empresa')+' • saldo '+saldo+' • mínimo '+min})}
  });
  const now=Date.now();
  (a.workers||[]).filter(w=>w.active!==false).forEach(w=>{
    (a.epis||[]).filter(e=>Number(e.cycle||0)>0).forEach(e=>{
      if(heldQty(a,s,w.id,e.id)<=0)return;
      const d=latestDeliveryFor(a,w.id,e.id);if(!d)return;
      const t=Date.parse(d.createdAt||'');if(!Number.isFinite(t))return;
      const days=Math.ceil((t+Number(e.cycle)*86400000-now)/86400000);
      if(days<=15){due++;alerts.push({cls:days<0?'bad':'warn',title:(days<0?'Troca vencida':'Troca próxima')+' • '+w.name,sub:e.name+' • '+(days<0?Math.abs(days)+' dia(s) em atraso':days+' dia(s)')})}
    });
  });
  $('#more323Low').textContent=low;$('#more323Due').textContent=due;
  root.innerHTML=alerts.length?alerts.slice(0,80).map(x=>`<div class="more323-row more323-alert ${x.cls}"><b>${esc(x.title)}</b><small>${esc(x.sub)}</small></div>`).join(''):'<div class="empty">Nenhum alerta identificado agora.</div>';
}

function pass(){styles();injectViews();injectNav()}
function boot(){
  pass();
  [200,600,1200,2200].forEach(ms=>setTimeout(pass,ms));
  document.addEventListener('click',e=>{
    const g=e.target.closest('[data-go]')?.dataset.go;
    if(g==='moreSectors')setTimeout(renderSectors,30);
    if(g==='moreAlerts')setTimeout(renderAlerts,30);
  },true);
  document.addEventListener('auditar-epi-data-changed',()=>{
    if($('#moreSectors')?.classList.contains('active'))renderSectors();
    if($('#moreAlerts')?.classList.contains('active'))renderAlerts();
  });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();