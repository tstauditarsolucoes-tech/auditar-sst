(()=>{
  const CACHE='auditarEpiGestaoCacheV1';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=v=>Number(v||0);
  const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  let selectedSectorKey='';

  function load(){
    try{
      const x=JSON.parse(localStorage.getItem(CACHE)||'{}');
      return {app:{companies:x?.app?.companies||[],workers:x?.app?.workers||[],epis:x?.app?.epis||[],deliveries:x?.app?.deliveries||[]}};
    }catch{return {app:{companies:[],workers:[],epis:[],deliveries:[]}};}
  }
  function selectedCompany(){return $('#globalCompany')?.value||'';}
  function sectorPeriod(){return $('#sectorPeriod')?.value||'month';}
  function startDate(kind){
    const d=new Date();
    if(kind==='month')return new Date(d.getFullYear(),d.getMonth(),1);
    if(kind==='3m')return new Date(d.getFullYear(),d.getMonth()-2,1);
    if(kind==='6m')return new Date(d.getFullYear(),d.getMonth()-5,1);
    if(kind==='year')return new Date(d.getFullYear(),0,1);
    return null;
  }
  function inPeriod(iso,kind=sectorPeriod()){
    const s=startDate(kind);if(!s)return true;
    const d=new Date(iso);return !Number.isNaN(d.getTime())&&d>=s;
  }
  function qty(del){return (del.items||[]).reduce((s,i)=>s+num(i.qty),0);}
  function fmt(iso){try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(iso));}catch{return '—';}}
  function table(headers,rows,empty='Nada para mostrar.'){
    if(!rows.length)return `<div class="empty">${esc(empty)}</div>`;
    return `<table class="data-table"><thead><tr>${headers.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(v=>`<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  }
  function barList(rows,empty='Sem consumo registrado.'){
    if(!rows.length)return `<div class="empty">${esc(empty)}</div>`;
    const max=Math.max(...rows.map(r=>r.value),1);
    return `<div class="rank-list">${rows.map((r,i)=>`<div class="rank-row"><div class="rank-name"><b>${i+1}. ${esc(r.name)}</b>${r.sub?`<small>${esc(r.sub)}</small>`:''}</div><div class="rank-track"><div class="rank-fill" style="width:${Math.max(4,(r.value/max)*100)}%"></div></div><div class="rank-value">${esc(r.label||String(r.value))}</div></div>`).join('')}</div>`;
  }

  function injectStyle(){
    if($('#sectorV277Style'))return;
    const s=document.createElement('style');s.id='sectorV277Style';s.textContent=`
      #sectors .sector-name{font-weight:900;color:#173d39}
      #sectors .sector-detail-head{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:14px}
      #sectors .sector-detail-head h2{margin:0}
      #sectors .sector-detail-head p{margin:5px 0 0;color:#718682;font-size:13px}
      #sectors .sector-subgrid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
      #sectors .sector-back{border:1px solid #d6e5e2;background:#f4f8f7;color:#285651;border-radius:10px;padding:9px 12px;font-weight:850;cursor:pointer}
      #sectors .sector-open{white-space:nowrap}
      #sectorsDetail.hidden{display:none}
      @media(max-width:900px){#sectors .sector-subgrid{grid-template-columns:1fr}.sector-detail-head{align-items:flex-start!important;flex-direction:column}}
    `;document.head.appendChild(s);
  }

  function injectUi(){
    injectStyle();
    const nav=$('.sidebar nav');
    if(nav&&!$('#sectorNav')){
      const b=document.createElement('button');b.id='sectorNav';b.className='nav';b.dataset.view='sectors';b.innerHTML='🏭 <span>Setores</span>';
      const workers=nav.querySelector('.nav[data-view="workers"]');
      nav.insertBefore(b,workers||null);
    }
    const main=$('.main');
    if(main&&!$('#sectors')){
      const section=document.createElement('section');section.id='sectors';section.className='view';
      section.innerHTML=`
        <div class="simple-filter">
          <label>Período para analisar
            <select id="sectorPeriod">
              <option value="month">Este mês</option>
              <option value="3m">Últimos 3 meses</option>
              <option value="6m">Últimos 6 meses</option>
              <option value="year">Este ano</option>
              <option value="all">Todo o histórico</option>
            </select>
          </label>
          <p>Use o filtro de empresa no canto superior para analisar uma empresa específica.</p>
        </div>
        <div class="cards four">
          <article class="metric"><span>Setores</span><strong id="sectorCount">0</strong><small>com trabalhadores ativos</small></article>
          <article class="metric"><span>Trabalhadores</span><strong id="sectorWorkers">0</strong><small>nos setores exibidos</small></article>
          <article class="metric"><span>EPIs entregues</span><strong id="sectorUnits">0</strong><small>unidades no período</small></article>
          <article class="metric text"><span>Setor que mais recebeu</span><strong id="sectorTop">—</strong><small>maior consumo no período</small></article>
        </div>
        <article class="panel">
          <div class="panel-head"><div><h2>🏭 Setores da empresa</h2><p>Clique em um setor para abrir o detalhamento.</p></div></div>
          <div id="sectorOverview" class="table-wrap"></div>
        </article>
        <div id="sectorsDetail" class="hidden" style="margin-top:16px">
          <article class="panel">
            <div class="sector-detail-head"><div><h2 id="sectorDetailTitle">Setor</h2><p id="sectorDetailSub">Detalhamento do consumo.</p></div><button id="sectorBack" class="sector-back" type="button">← Voltar ao ranking</button></div>
            <div class="cards three compact">
              <article class="metric"><span>Trabalhadores</span><strong id="sectorDetailWorkers">0</strong></article>
              <article class="metric"><span>Unidades entregues</span><strong id="sectorDetailUnits">0</strong></article>
              <article class="metric"><span>Entregas</span><strong id="sectorDetailDeliveries">0</strong></article>
            </div>
          </article>
          <div class="sector-subgrid">
            <article class="panel"><div class="panel-head"><div><h2>🦺 EPIs mais consumidos</h2><p>Quantidade entregue ao setor no período.</p></div></div><div id="sectorTopEpis"></div></article>
            <article class="panel"><div class="panel-head"><div><h2>👷 Trabalhadores do setor</h2><p>Quem pertence ao setor e quanto recebeu no período.</p></div></div><div id="sectorWorkerTable" class="table-wrap"></div></article>
          </div>
          <article class="panel full"><div class="panel-head"><div><h2>📋 Histórico de entregas do setor</h2><p>Registros mais recentes do período selecionado.</p></div></div><div id="sectorHistory" class="table-wrap"></div></article>
        </div>`;
      main.appendChild(section);
    }
  }

  function sectorData(){
    const d=load(),companyId=selectedCompany();
    const companies=new Map(d.app.companies.map(x=>[x.id,x]));
    const workers=new Map(d.app.workers.map(x=>[x.id,x]));
    const epis=new Map(d.app.epis.map(x=>[x.id,x]));
    const activeWorkers=d.app.workers.filter(w=>w.active!==false&&(!companyId||w.companyId===companyId));
    const deliveries=d.app.deliveries.filter(del=>(!companyId||del.companyId===companyId)&&inPeriod(del.createdAt));
    const sectorMap=new Map();
    function ensure(name){
      const display=String(name||'Setor não informado').trim()||'Setor não informado';
      const key=norm(display)||'setor nao informado';
      if(!sectorMap.has(key))sectorMap.set(key,{key,name:display,workers:[],deliveries:[],units:0,epiTotals:new Map()});
      return sectorMap.get(key);
    }
    activeWorkers.forEach(w=>ensure(w.sector).workers.push(w));
    deliveries.forEach(del=>{
      const w=workers.get(del.workerId),sec=ensure(w?.sector);
      sec.deliveries.push(del);sec.units+=qty(del);
      (del.items||[]).forEach(i=>sec.epiTotals.set(i.epiId,(sec.epiTotals.get(i.epiId)||0)+num(i.qty)));
    });
    const sectors=[...sectorMap.values()].sort((a,b)=>b.units-a.units||b.deliveries.length-a.deliveries.length||a.name.localeCompare(b.name));
    return {d,companies,workers,epis,activeWorkers,deliveries,sectors};
  }

  function renderOverview(){
    if(!$('#sectors'))return;
    const x=sectorData();
    $('#sectorCount').textContent=String(x.sectors.length);
    $('#sectorWorkers').textContent=String(x.activeWorkers.length);
    $('#sectorUnits').textContent=String(x.deliveries.reduce((s,d)=>s+qty(d),0));
    $('#sectorTop').textContent=x.sectors.length?x.sectors[0].name:'—';
    $('#sectorOverview').innerHTML=table(['Setor','Trabalhadores','EPIs entregues','Entregas',''],x.sectors.map(s=>[
      `<span class="sector-name">${esc(s.name)}</span>`,String(s.workers.length),`<b>${s.units} un.</b>`,String(s.deliveries.length),`<button class="link sector-open" type="button" data-sector-open="${esc(s.key)}">Ver detalhes →</button>`
    ]),'Nenhum setor encontrado nos trabalhadores cadastrados.');
    if(selectedSectorKey){
      const exists=x.sectors.some(s=>s.key===selectedSectorKey);
      if(exists)renderDetail(selectedSectorKey,x);else closeDetail();
    }
  }

  function renderDetail(key,x=sectorData()){
    const s=x.sectors.find(v=>v.key===key);if(!s)return closeDetail();
    selectedSectorKey=key;
    $('#sectorsDetail')?.classList.remove('hidden');
    $('#sectorDetailTitle').textContent=s.name;
    $('#sectorDetailSub').textContent=selectedCompany()?`Detalhes do setor na empresa selecionada.`:'Detalhes do setor considerando as empresas exibidas.';
    $('#sectorDetailWorkers').textContent=String(s.workers.length);
    $('#sectorDetailUnits').textContent=String(s.units);
    $('#sectorDetailDeliveries').textContent=String(s.deliveries.length);

    const epiRows=[...s.epiTotals].sort((a,b)=>b[1]-a[1]).slice(0,10).map(([id,value])=>({name:x.epis.get(id)?.name||'EPI',value,label:`${value} un.`}));
    $('#sectorTopEpis').innerHTML=barList(epiRows,'Ainda não houve entrega de EPI para este setor no período.');

    const workerStats=new Map();
    s.deliveries.forEach(del=>{const a=workerStats.get(del.workerId)||{units:0,deliveries:0};a.units+=qty(del);a.deliveries++;workerStats.set(del.workerId,a);});
    $('#sectorWorkerTable').innerHTML=table(['Trabalhador','Empresa','Matrícula','Cargo','Recebeu'],s.workers.slice().sort((a,b)=>String(a.name).localeCompare(String(b.name))).map(w=>{
      const st=workerStats.get(w.id)||{units:0,deliveries:0};
      return [esc(w.name||'—'),esc(x.companies.get(w.companyId)?.name||'—'),esc(w.reg||'—'),esc(w.role||'—'),`${st.units} un. / ${st.deliveries} entrega(s)`];
    }),'Nenhum trabalhador ativo neste setor.');

    const history=s.deliveries.slice().sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||''))).slice(0,30);
    $('#sectorHistory').innerHTML=table(['Data','Trabalhador','Empresa','EPIs','Motivo'],history.map(del=>{
      const w=x.workers.get(del.workerId);
      const items=(del.items||[]).map(i=>`${x.epis.get(i.epiId)?.name||'EPI'} (${num(i.qty)})`).join(', ');
      return [fmt(del.createdAt),esc(w?.name||'—'),esc(x.companies.get(del.companyId)?.name||'—'),esc(items||'—'),esc(del.reason||'—')];
    }),'Nenhuma entrega registrada para este setor no período.');
    setTimeout(()=>$('#sectorsDetail')?.scrollIntoView({behavior:'smooth',block:'start'}),20);
  }

  function closeDetail(){selectedSectorKey='';$('#sectorsDetail')?.classList.add('hidden');}
  function openSectorView(){
    $$('.view').forEach(v=>v.classList.toggle('active',v.id==='sectors'));
    $$('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view==='sectors'));
    if($('#viewTitle'))$('#viewTitle').textContent='Setores';
    if($('#viewSub'))$('#viewSub').textContent='Veja o consumo de EPI por setor e abra os detalhes de cada área.';
    renderOverview();
  }

  function bind(){
    document.addEventListener('click',e=>{
      const nav=e.target.closest('.nav[data-view="sectors"]');if(nav){e.preventDefault();openSectorView();return;}
      const open=e.target.closest('[data-sector-open]');if(open){e.preventDefault();renderDetail(open.dataset.sectorOpen);return;}
      if(e.target.closest('#sectorBack')){e.preventDefault();closeDetail();$('#sectorOverview')?.scrollIntoView({behavior:'smooth',block:'start'});}
    },true);
    $('#sectorPeriod')?.addEventListener('change',()=>{closeDetail();renderOverview();});
    $('#globalCompany')?.addEventListener('change',()=>{closeDetail();setTimeout(renderOverview,0);});
    const prior=Storage.prototype.setItem;
    Storage.prototype.setItem=function(key,value){const r=prior.call(this,key,value);if(key===CACHE)setTimeout(renderOverview,0);return r;};
    window.addEventListener('storage',e=>{if(e.key===CACHE)renderOverview();});
  }

  function boot(){injectUi();bind();renderOverview();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
