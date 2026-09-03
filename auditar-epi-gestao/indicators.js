(() => {
  const CACHE='auditarEpiGestaoCacheV1';
  const $=(s,r=document)=>r.querySelector(s);
  const esc=(v='')=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const num=v=>Number(v||0);

  function load(){
    try{
      const x=JSON.parse(localStorage.getItem(CACHE)||'{}');
      return {
        app:{companies:x?.app?.companies||[],workers:x?.app?.workers||[],epis:x?.app?.epis||[],deliveries:x?.app?.deliveries||[]},
        stock:{movements:x?.stock?.movements||[],minimums:x?.stock?.minimums||{}}
      };
    }catch{return {app:{companies:[],workers:[],epis:[],deliveries:[]},stock:{movements:[],minimums:{}}};}
  }
  function selectedCompany(){return $('#globalCompany')?.value||'';}
  function period(){return $('#indicatorPeriod')?.value||'month';}
  function startDate(kind){
    const d=new Date();
    if(kind==='month')return new Date(d.getFullYear(),d.getMonth(),1);
    if(kind==='3m')return new Date(d.getFullYear(),d.getMonth()-2,1);
    if(kind==='6m')return new Date(d.getFullYear(),d.getMonth()-5,1);
    if(kind==='year')return new Date(d.getFullYear(),0,1);
    return null;
  }
  function inPeriod(iso,kind){const s=startDate(kind);if(!s)return true;const d=new Date(iso);return !Number.isNaN(d.getTime())&&d>=s;}
  function maps(d){return {
    companies:new Map(d.app.companies.map(x=>[x.id,x])),
    workers:new Map(d.app.workers.map(x=>[x.id,x])),
    epis:new Map(d.app.epis.map(x=>[x.id,x]))
  };}
  function deliveryQty(delivery){return (delivery.items||[]).reduce((s,i)=>s+num(i.qty),0);}
  function companyDeliveries(d,kind=period()){
    const c=selectedCompany();
    return d.app.deliveries.filter(x=>(!c||x.companyId===c)&&inPeriod(x.createdAt,kind));
  }
  function stockRows(d){
    const c=selectedCompany(), keys=new Set(Object.keys(d.stock.minimums||{}));
    d.stock.movements.forEach(m=>keys.add(`${m.companyId}::${m.epiId}`));
    return [...keys].map(key=>{
      const p=key.split('::'),companyId=p.shift(),epiId=p.join('::');
      const saldo=d.stock.movements.filter(m=>m.companyId===companyId&&m.epiId===epiId).reduce((s,m)=>s+num(m.delta),0);
      return {key,companyId,epiId,saldo,min:num(d.stock.minimums[key]??5)};
    }).filter(r=>!c||r.companyId===c);
  }
  function setText(id,value){const el=$(id);if(el)el.textContent=value;}
  function nameEpi(m,id,item){return m.epis.get(id)?.name||item?.name||item?.epiName||'EPI';}
  function nameWorker(m,id){return m.workers.get(id)?.name||'Colaborador';}
  function nameCompany(m,id){return m.companies.get(id)?.name||'—';}

  function barList(rows,empty='Sem dados neste período.'){
    if(!rows.length)return `<div class="empty">${esc(empty)}</div>`;
    const max=Math.max(...rows.map(r=>r.value),1);
    return `<div class="rank-list">${rows.map((r,i)=>`<div class="rank-row"><div class="rank-name"><b>${i+1}. ${esc(r.name)}</b>${r.sub?`<small>${esc(r.sub)}</small>`:''}</div><div class="rank-track"><div class="rank-fill" style="width:${Math.max(4,(r.value/max)*100)}%"></div></div><div class="rank-value">${esc(r.label||String(r.value))}</div></div>`).join('')}</div>`;
  }
  function simpleTable(headers,rows,empty='Nada para mostrar.'){
    if(!rows.length)return `<div class="empty">${esc(empty)}</div>`;
    return `<table class="data-table"><thead><tr>${headers.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(v=>`<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  }

  function summary(d,m,deliveries){
    const epiTotals=new Map(),workerTotals=new Map();
    deliveries.forEach(del=>{
      const total=deliveryQty(del);
      const w=workerTotals.get(del.workerId)||{qty:0,deliveries:0};w.qty+=total;w.deliveries++;workerTotals.set(del.workerId,w);
      (del.items||[]).forEach(i=>epiTotals.set(i.epiId,(epiTotals.get(i.epiId)||0)+num(i.qty)));
    });
    const epis=[...epiTotals].sort((a,b)=>b[1]-a[1]);
    const workers=[...workerTotals].sort((a,b)=>b[1].qty-a[1].qty);
    return {units:deliveries.reduce((s,x)=>s+deliveryQty(x),0),deliveries:deliveries.length,epis,workers};
  }

  function renderDashboardEasy(d,m){
    const month=companyDeliveries(d,'month'),s=summary(d,m,month),low=stockRows(d).filter(r=>r.saldo<=r.min);
    setText('#mToday',s.units);
    setText('#mWorkers',s.deliveries);
    setText('#mEpis',s.epis.length?nameEpi(m,s.epis[0][0]):'—');
    setText('#mLow',low.length);
    $('#mEpis')?.closest('.metric')?.classList.add('text');
  }

  function renderIndicators(){
    const d=load(),m=maps(d),deliveries=companyDeliveries(d),s=summary(d,m,deliveries);
    setText('#kUnits',s.units);setText('#kDeliveries',s.deliveries);
    setText('#kTopEpi',s.epis.length?nameEpi(m,s.epis[0][0]):'—');
    setText('#kTopWorker',s.workers.length?nameWorker(m,s.workers[0][0]):'—');

    const epiRows=s.epis.slice(0,5).map(([id,value])=>({name:nameEpi(m,id),value,label:`${value} un.`}));
    const workerRows=s.workers.slice(0,5).map(([id,x])=>({name:nameWorker(m,id),value:x.qty,label:`${x.qty} un.`,sub:`${x.deliveries} entrega(s)`}));
    if($('#topEpis'))$('#topEpis').innerHTML=barList(epiRows);
    if($('#topWorkers'))$('#topWorkers').innerHTML=barList(workerRows);

    const reasonMap=new Map(),sectorMap=new Map();
    deliveries.forEach(del=>{
      const q=deliveryQty(del),reason=String(del.reason||'Não informado').trim()||'Não informado';
      reasonMap.set(reason,(reasonMap.get(reason)||0)+q);
      const sector=String(m.workers.get(del.workerId)?.sector||'Setor não informado').trim()||'Setor não informado';
      sectorMap.set(sector,(sectorMap.get(sector)||0)+q);
    });
    const reasons=[...reasonMap].sort((a,b)=>b[1]-a[1]).slice(0,6).map(([name,value])=>({name,value,label:`${value} un.`}));
    const sectors=[...sectorMap].sort((a,b)=>b[1]-a[1]).slice(0,6).map(([name,value])=>({name,value,label:`${value} un.`}));
    if($('#reasonList'))$('#reasonList').innerHTML=barList(reasons,'Ainda não há motivos registrados.');
    if($('#sectorList'))$('#sectorList').innerHTML=barList(sectors,'Ainda não há consumo por setor.');

    const months=[];const now=new Date();const c=selectedCompany();
    for(let i=5;i>=0;i--){
      const start=new Date(now.getFullYear(),now.getMonth()-i,1),end=new Date(start.getFullYear(),start.getMonth()+1,1);
      const value=d.app.deliveries.filter(x=>(!c||x.companyId===c)&&new Date(x.createdAt)>=start&&new Date(x.createdAt)<end).reduce((sum,x)=>sum+deliveryQty(x),0);
      months.push({name:new Intl.DateTimeFormat('pt-BR',{month:'short',year:'2-digit'}).format(start),value,label:`${value} un.`});
    }
    if($('#monthConsumption'))$('#monthConsumption').innerHTML=barList(months,'Sem consumo nos últimos meses.');
  }

  function renderPending(){
    const d=load(),m=maps(d),c=selectedCompany(),allDeliveries=d.app.deliveries.filter(x=>!c||x.companyId===c),stocks=stockRows(d);
    const low=stocks.filter(r=>r.saldo<=r.min),negative=stocks.filter(r=>r.saldo<0);
    const workers=d.app.workers.filter(w=>w.active!==false&&(!c||w.companyId===c));
    const deliveredWorkers=new Set(allDeliveries.map(x=>x.workerId));
    const noDelivery=workers.filter(w=>!deliveredWorkers.has(w.id));
    const relevantEpis=new Set();
    if(c){allDeliveries.forEach(x=>(x.items||[]).forEach(i=>relevantEpis.add(i.epiId)));d.stock.movements.filter(x=>x.companyId===c).forEach(x=>relevantEpis.add(x.epiId));}
    const missingCa=d.app.epis.filter(e=>!String(e.ca||'').trim()&&(!c||relevantEpis.has(e.id)));
    const noSignature=allDeliveries.filter(x=>!String(x.signature||'').trim());

    setText('#pLow',low.length);setText('#pNegative',negative.length);setText('#pNoDelivery',noDelivery.length);setText('#pMissingCa',missingCa.length);

    if($('#pendingStock'))$('#pendingStock').innerHTML=simpleTable(['EPI','Empresa','Saldo','Mínimo'],low.sort((a,b)=>a.saldo-b.saldo).slice(0,12).map(r=>[
      esc(nameEpi(m,r.epiId)),esc(nameCompany(m,r.companyId)),`<b>${r.saldo}</b>`,String(r.min)
    ]),'Estoque sem alertas.');
    if($('#pendingWorkers'))$('#pendingWorkers').innerHTML=simpleTable(['Colaborador','Empresa','Cargo / setor'],noDelivery.slice(0,12).map(w=>[
      esc(w.name),esc(nameCompany(m,w.companyId)),esc([w.role,w.sector].filter(Boolean).join(' / ')||'—')
    ]),'Todos os colaboradores já possuem alguma entrega registrada.');
    if($('#pendingCa'))$('#pendingCa').innerHTML=simpleTable(['EPI','Situação'],missingCa.slice(0,12).map(e=>[esc(e.name),'<span class="status low">CA não informado</span>']),'Nenhum EPI com CA faltando.');
    if($('#pendingSignature'))$('#pendingSignature').innerHTML=simpleTable(['Data','Colaborador','Situação'],noSignature.slice(0,12).map(x=>[
      esc(new Intl.DateTimeFormat('pt-BR',{dateStyle:'short'}).format(new Date(x.createdAt))),esc(nameWorker(m,x.workerId)),'<span class="status low">Sem assinatura</span>'
    ]),'Nenhuma entrega sem assinatura.');

    const early=[];
    const grouped=new Map();
    allDeliveries.slice().sort((a,b)=>new Date(a.createdAt)-new Date(b.createdAt)).forEach(del=>{
      (del.items||[]).forEach(item=>{
        const e=m.epis.get(item.epiId),cycle=num(e?.cycle);if(!cycle)return;
        const key=`${del.workerId}::${item.epiId}`,prev=grouped.get(key),current=new Date(del.createdAt);
        if(prev){const days=Math.floor((current-prev.date)/86400000);if(days>=0&&days<cycle)early.push({workerId:del.workerId,epiId:item.epiId,days,cycle,date:current});}
        grouped.set(key,{date:current});
      });
    });
    early.sort((a,b)=>b.date-a.date);
    if($('#earlyReplacement'))$('#earlyReplacement').innerHTML=simpleTable(['Colaborador','EPI','Intervalo','Previsto'],early.slice(0,12).map(x=>[
      esc(nameWorker(m,x.workerId)),esc(nameEpi(m,x.epiId)),`${x.days} dia(s)`,`${x.cycle} dias`
    ]),'Nenhuma troca antes do prazo cadastrado.');
  }

  function renderAllIndicators(){
    const d=load(),m=maps(d);renderDashboardEasy(d,m);renderIndicators();renderPending();
  }
  function setViewHeader(view){
    const titles={indicators:['Indicadores de EPI','Veja de forma simples o que mais saiu e quem mais recebeu.'],pending:['Precisa de atenção','Pendências que merecem conferência.']};
    const t=titles[view];if(!t)return;setText('#viewTitle',t[0]);setText('#viewSub',t[1]);
  }

  const previousSet=Storage.prototype.setItem;
  Storage.prototype.setItem=function(key,value){const r=previousSet.call(this,key,value);if(key===CACHE)setTimeout(renderAllIndicators,0);return r;};

  document.addEventListener('DOMContentLoaded',()=>{
    if($('#indicatorPeriod'))$('#indicatorPeriod').addEventListener('change',renderIndicators);
    if($('#globalCompany'))$('#globalCompany').addEventListener('change',()=>setTimeout(renderAllIndicators,0));
    document.addEventListener('click',e=>{const n=e.target.closest('.nav[data-view]');if(n&&['indicators','pending'].includes(n.dataset.view))setTimeout(()=>setViewHeader(n.dataset.view),0);});
    renderAllIndicators();
  });
  window.addEventListener('storage',e=>{if(e.key===CACHE)renderAllIndicators();});
})();