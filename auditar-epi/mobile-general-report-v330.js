(() => {
  'use strict';
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const RETURN_MARK='DEVOLUÇÃO EPI';
  const $=(s,r=document)=>r.querySelector(s);
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;

  function readApp(){try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')};}catch{return {companies:[],workers:[],epis:[],deliveries:[]};}}
  function readStock(){try{return {movements:[],minimums:{},...JSON.parse(localStorage.getItem(STOCK_KEY)||'{}')};}catch{return {movements:[],minimums:{}};}}
  function toast(msg){const el=$('#toast');if(!el)return;el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2500);}
  function fmtDate(v){if(!v)return '—';try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short'}).format(new Date(v));}catch{return '—';}}
  function fmtDateTime(v){if(!v)return '—';try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(v));}catch{return '—';}}
  function startOfDay(d){const x=new Date(d);x.setHours(0,0,0,0);return x;}
  function endOfDay(d){const x=new Date(d);x.setHours(23,59,59,999);return x;}
  function isoInput(d){return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10);}
  function companyName(app,id){return app.companies.find(c=>c.id===id)?.name||'Empresa';}
  function worker(app,id){return app.workers.find(w=>w.id===id)||null;}
  function epi(app,id){return app.epis.find(e=>e.id===id)||null;}

  function injectStyle(){
    if($('#v330ReportStyle'))return;
    const s=document.createElement('style');s.id='v330ReportStyle';s.textContent=`
      body{padding-bottom:112px!important}
      #reportV330{padding-bottom:42px}
      .v330-toolbar{display:grid;gap:10px}.v330-toolbar label{display:grid;gap:5px;font-size:12px;font-weight:850;color:#385c58}
      .v330-toolbar select,.v330-toolbar input{min-height:48px;border:1px solid #cfdeda;border-radius:12px;padding:9px 11px;background:#fff;color:#173d39;font-size:14px}
      .v330-dates{display:grid;grid-template-columns:1fr 1fr;gap:9px}.v330-dates.hidden{display:none}
      .v330-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.v330-actions button{min-height:48px;border-radius:12px;font-weight:900;border:1px solid #bdd5d1;background:#fff;color:#0f766e}.v330-actions .main{background:#0f766e;color:#fff;border-color:#0f766e;grid-column:1/-1}
      .v330-kpis{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin:12px 0}.v330-kpi{background:#fff;border:1px solid #d8e5e2;border-radius:14px;padding:13px}.v330-kpi strong{display:block;font-size:23px;color:#173d39}.v330-kpi span{display:block;color:#6b807d;font-size:11px;margin-top:3px}
      .v330-panel{background:#fff;border:1px solid #d8e5e2;border-radius:16px;padding:14px;margin:10px 0}.v330-panel h3{margin:0 0 10px;color:#173d39;font-size:16px}.v330-panel p{margin:0;color:#6b807d;font-size:11px}
      .v330-row{display:grid;grid-template-columns:1fr auto;gap:10px;padding:10px 0;border-bottom:1px solid #edf2f1}.v330-row:last-child{border-bottom:0}.v330-row b{display:block;color:#173d39;font-size:13px}.v330-row small{display:block;color:#6b807d;font-size:10px;margin-top:3px;line-height:1.35}.v330-row strong{color:#0f766e;font-size:14px;align-self:center}
      .v330-empty{padding:13px;text-align:center;color:#708581;font-size:12px;background:#f8fbfa;border-radius:12px}
      .v330-period{font-size:11px;color:#58716d;margin-top:5px}
      .v330-print-head{display:none}
      @media print{
        body *{visibility:hidden!important}#reportV330,#reportV330 *{visibility:visible!important}#reportV330{position:absolute;inset:0;width:100%;padding:0 14px;background:#fff}.v3-bottom-nav,.topbar,.view-head,.v330-toolbar,.v330-actions{display:none!important}.v330-print-head{display:block!important;margin:0 0 12px}.v330-panel,.v330-kpi{box-shadow:none;break-inside:avoid}.v330-kpis{grid-template-columns:repeat(4,1fr)}
      }
    `;document.head.appendChild(s);
  }

  function injectView(){
    const main=$('main.app-shell');if(!main||$('#reportV330'))return;
    const s=document.createElement('section');s.id='reportV330';s.className='view';s.innerHTML=`
      <div class="view-head"><button class="back" data-go="moreV3">←</button><div><h2>Relatório geral de EPI</h2><p>Saídas, entregas, devoluções e estoque por período.</p></div></div>
      <div class="v330-print-head"><h1>RELATÓRIO GERAL DE EPI</h1><div id="v330PrintPeriod"></div></div>
      <div class="card v330-toolbar">
        <label>Empresa<select id="v330Company"></select></label>
        <label>Período<select id="v330Period"><option value="today">Hoje</option><option value="7d">Últimos 7 dias</option><option value="30d">Últimos 30 dias</option><option value="month" selected>Este mês</option><option value="prevMonth">Mês anterior</option><option value="year">Este ano</option><option value="all">Todo o histórico</option><option value="custom">Personalizado</option></select></label>
        <div id="v330Dates" class="v330-dates hidden"><label>De<input id="v330From" type="date"></label><label>Até<input id="v330To" type="date"></label></div>
        <label>EPI<select id="v330Epi"><option value="">Todos os EPIs</option></select></label>
        <label>Setor<input id="v330Sector" placeholder="Todos os setores"></label>
        <div class="v330-actions"><button id="v330Apply" class="main" type="button">Gerar relatório</button><button id="v330Csv" type="button">⇩ Exportar CSV</button><button id="v330Print" type="button">🖨️ PDF / Imprimir</button></div>
      </div>
      <div id="v330PeriodLabel" class="v330-period"></div>
      <div class="v330-kpis"><div class="v330-kpi"><strong id="v330Units">0</strong><span>EPIs entregues</span></div><div class="v330-kpi"><strong id="v330Deliveries">0</strong><span>Entregas</span></div><div class="v330-kpi"><strong id="v330Workers">0</strong><span>Trabalhadores atendidos</span></div><div class="v330-kpi"><strong id="v330Returns">0</strong><span>Unidades devolvidas</span></div><div class="v330-kpi"><strong id="v330Entries">0</strong><span>Entradas no estoque</span></div><div class="v330-kpi"><strong id="v330Distinct">0</strong><span>Tipos de EPI movimentados</span></div></div>
      <div class="v330-panel"><h3>🦺 EPIs que mais saíram</h3><div id="v330TopEpis"></div></div>
      <div class="v330-panel"><h3>🏭 Consumo por setor</h3><div id="v330Sectors"></div></div>
      <div class="v330-panel"><h3>👷 Trabalhadores que mais receberam</h3><div id="v330TopWorkers"></div></div>
      <div class="v330-panel"><h3>📋 Detalhamento das saídas</h3><div id="v330Details"></div></div>`;
    main.appendChild(s);
  }

  function addMenuEntry(){
    const grid=$('#moreV3 .v3-more-grid');if(!grid||grid.querySelector('[data-go="reportV330"]'))return;
    const b=document.createElement('button');b.className='menu-card';b.dataset.go='reportV330';b.innerHTML='<span>📊</span><b>Relatório geral</b><small>Saídas, períodos e filtros</small>';grid.appendChild(b);
  }

  function fillFilters(){
    const app=readApp();
    const cs=$('#v330Company'),es=$('#v330Epi');if(!cs||!es)return;
    const oldC=cs.value,oldE=es.value;
    cs.innerHTML='<option value="">Todas as empresas</option>'+app.companies.map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('');
    es.innerHTML='<option value="">Todos os EPIs</option>'+app.epis.slice().sort((a,b)=>String(a.name).localeCompare(String(b.name))).map(e=>`<option value="${esc(e.id)}">${esc(e.name)}${e.ca?' • CA '+esc(e.ca):''}</option>`).join('');
    if(app.companies.some(c=>c.id===oldC))cs.value=oldC;else if(app.companies.length===1)cs.value=app.companies[0].id;
    if(app.epis.some(e=>e.id===oldE))es.value=oldE;
  }

  function range(){
    const mode=$('#v330Period')?.value||'month',now=new Date();let from=null,to=null;
    if(mode==='today'){from=startOfDay(now);to=endOfDay(now);}
    else if(mode==='7d'){from=startOfDay(new Date(now.getFullYear(),now.getMonth(),now.getDate()-6));to=endOfDay(now);}
    else if(mode==='30d'){from=startOfDay(new Date(now.getFullYear(),now.getMonth(),now.getDate()-29));to=endOfDay(now);}
    else if(mode==='month'){from=startOfDay(new Date(now.getFullYear(),now.getMonth(),1));to=endOfDay(new Date(now.getFullYear(),now.getMonth()+1,0));}
    else if(mode==='prevMonth'){from=startOfDay(new Date(now.getFullYear(),now.getMonth()-1,1));to=endOfDay(new Date(now.getFullYear(),now.getMonth(),0));}
    else if(mode==='year'){from=startOfDay(new Date(now.getFullYear(),0,1));to=endOfDay(new Date(now.getFullYear(),11,31));}
    else if(mode==='custom'){
      const a=$('#v330From')?.value,b=$('#v330To')?.value;if(a)from=startOfDay(new Date(a+'T00:00:00'));if(b)to=endOfDay(new Date(b+'T00:00:00'));
    }
    return {from,to,mode};
  }
  function inRange(iso,r){if(!iso)return false;const d=new Date(iso);if(Number.isNaN(d.getTime()))return false;if(r.from&&d<r.from)return false;if(r.to&&d>r.to)return false;return true;}

  function reportData(){
    const app=readApp(),stock=readStock(),r=range();const companyId=$('#v330Company')?.value||'',epiId=$('#v330Epi')?.value||'',sectorQ=norm($('#v330Sector')?.value||'');
    const deliveries=[];const detail=[];const epiTotals=new Map(),workerTotals=new Map(),sectorTotals=new Map(),workerIds=new Set(),distinct=new Set();let units=0;
    for(const d of app.deliveries||[]){
      if(d?.cancelled||!inRange(d.createdAt,r)||companyId&&d.companyId!==companyId)continue;
      const w=worker(app,d.workerId);if(!w)continue;if(sectorQ&&!norm(w.sector||'Sem setor').includes(sectorQ))continue;
      let matchedItems=[];
      for(const i of d.items||[]){if(epiId&&i.epiId!==epiId)continue;const q=Math.max(0,Number(i.qty||0));if(!q)continue;matchedItems.push({...i,qty:q});}
      if(!matchedItems.length)continue;
      deliveries.push(d);workerIds.add(w.id);
      for(const i of matchedItems){const e=epi(app,i.epiId)||{id:i.epiId,name:'EPI'};units+=i.qty;distinct.add(i.epiId);epiTotals.set(i.epiId,(epiTotals.get(i.epiId)||0)+i.qty);workerTotals.set(w.id,(workerTotals.get(w.id)||0)+i.qty);const sec=String(w.sector||'Sem setor').trim()||'Sem setor';sectorTotals.set(sec,(sectorTotals.get(sec)||0)+i.qty);detail.push({createdAt:d.createdAt,company:companyName(app,d.companyId),worker:w.name,sector:sec,epi:e.name,ca:e.ca||'',qty:i.qty,reason:d.reason||'Entrega'});}
    }
    let returns=0,entries=0;
    for(const m of stock.movements||[]){
      if(!inRange(m.createdAt,r)||companyId&&m.companyId!==companyId||epiId&&m.epiId!==epiId)continue;
      const isReturn=String(m.note||'').trim().startsWith(RETURN_MARK);const delta=Number(m.delta||0);
      if(isReturn){const mt=String(m.note||'').match(/(?:^|\|)\s*qtd\s*:\s*(\d+(?:[.,]\d+)?)/i);returns+=mt?Number(String(mt[1]).replace(',','.')):Math.max(0,delta);}
      else if(delta>0&&(m.type==='IN'||m.type==='SET'))entries+=delta;
    }
    const sortMap=(map,labeler)=>[...map.entries()].sort((a,b)=>b[1]-a[1]).map(([id,qty])=>({id,qty,label:labeler(id)}));
    return {app,r,units,deliveries:deliveries.length,workers:workerIds.size,returns,entries,distinct:distinct.size,topEpis:sortMap(epiTotals,id=>epi(app,id)?.name||'EPI'),topWorkers:sortMap(workerTotals,id=>worker(app,id)?.name||'Trabalhador'),sectors:[...sectorTotals.entries()].sort((a,b)=>b[1]-a[1]).map(([label,qty])=>({label,qty})),detail:detail.sort((a,b)=>String(b.createdAt).localeCompare(String(a.createdAt)))};
  }

  let last=null;
  function rowHtml(rows,empty='Sem movimentação no período.'){
    if(!rows.length)return `<div class="v330-empty">${empty}</div>`;
    return rows.slice(0,15).map((x,i)=>`<div class="v330-row"><div><b>${i+1}. ${esc(x.label)}</b></div><strong>${x.qty}</strong></div>`).join('');
  }
  function render(){
    fillFilters();last=reportData();const x=last;
    $('#v330Units').textContent=x.units;$('#v330Deliveries').textContent=x.deliveries;$('#v330Workers').textContent=x.workers;$('#v330Returns').textContent=x.returns;$('#v330Entries').textContent=x.entries;$('#v330Distinct').textContent=x.distinct;
    $('#v330TopEpis').innerHTML=rowHtml(x.topEpis);
    $('#v330Sectors').innerHTML=rowHtml(x.sectors,'Nenhum setor com saída no período.');
    $('#v330TopWorkers').innerHTML=rowHtml(x.topWorkers,'Nenhum trabalhador recebeu EPI no período.');
    $('#v330Details').innerHTML=x.detail.length?x.detail.slice(0,200).map(d=>`<div class="v330-row"><div><b>${esc(d.worker)} • ${esc(d.epi)}</b><small>${fmtDateTime(d.createdAt)} • ${esc(d.company)}${d.sector?' • '+esc(d.sector):''}${d.ca?' • CA '+esc(d.ca):''} • ${esc(d.reason)}</small></div><strong>x${d.qty}</strong></div>`).join(''):'<div class="v330-empty">Nenhuma saída encontrada.</div>';
    const label=x.r.from||x.r.to?`${x.r.from?fmtDate(x.r.from):'início'} a ${x.r.to?fmtDate(x.r.to):'hoje'}`:'Todo o histórico';$('#v330PeriodLabel').textContent='Período: '+label;$('#v330PrintPeriod').textContent='Período: '+label;
  }

  function csv(){
    if(!last)render();const rows=[['Data','Empresa','Trabalhador','Setor','EPI','CA','Quantidade','Motivo'],...last.detail.map(d=>[fmtDateTime(d.createdAt),d.company,d.worker,d.sector,d.epi,d.ca,d.qty,d.reason])];
    const text=rows.map(r=>r.map(v=>{const s=String(v??'');return /[;"\n]/.test(s)?`"${s.replace(/"/g,'""')}"`:s;}).join(';')).join('\n');
    const blob=new Blob(['\ufeff'+text],{type:'text/csv;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`Relatorio_Geral_EPI_${new Date().toISOString().slice(0,10)}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),500);
  }

  function bind(){
    $('#v330Period')?.addEventListener('change',()=>{$('#v330Dates')?.classList.toggle('hidden',$('#v330Period').value!=='custom');});
    $('#v330Apply')?.addEventListener('click',()=>{render();toast('Relatório atualizado.');});
    $('#v330Csv')?.addEventListener('click',csv);$('#v330Print')?.addEventListener('click',()=>{if(!last)render();window.print();});
    document.addEventListener('click',e=>{if(e.target.closest('[data-go="reportV330"]'))setTimeout(render,40);});
    document.addEventListener('gestao-epi-sync-applied',()=>{if($('#reportV330')?.classList.contains('active'))setTimeout(render,120);});
  }

  function boot(){injectStyle();injectView();addMenuEntry();fillFilters();bind();setTimeout(addMenuEntry,500);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
