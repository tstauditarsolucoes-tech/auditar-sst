(() => {
  const APP_KEY = 'auditarEpiV1';
  const STOCK_KEY = 'auditarEpiStockV1';
  const DEFAULT_MIN = 5;

  const $ = (s, root=document) => root.querySelector(s);
  const esc = (v='') => String(v).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const norm = (v='') => String(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const uid = p => `${p}_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;

  function readApp(){
    try { return {companies:[], workers:[], epis:[], deliveries:[], ...JSON.parse(localStorage.getItem(APP_KEY)||'{}')}; }
    catch { return {companies:[], workers:[], epis:[], deliveries:[]}; }
  }

  function blankStock(){
    return {startedAt:'', processedDeliveryIds:[], movements:[], minimums:{}};
  }

  function readStock(){
    try { return {...blankStock(), ...JSON.parse(localStorage.getItem(STOCK_KEY)||'{}')}; }
    catch { return blankStock(); }
  }

  function writeStock(stock){ localStorage.setItem(STOCK_KEY, JSON.stringify(stock)); }

  function toast(msg){
    const el=$('#toast');
    if(!el) return alert(msg);
    el.textContent=msg; el.classList.add('show');
    setTimeout(()=>el.classList.remove('show'),2600);
  }

  function companyName(id, app=readApp()){ return app.companies.find(x=>x.id===id)?.name || 'Empresa'; }
  function epiById(id, app=readApp()){ return app.epis.find(x=>x.id===id); }
  function workerName(id, app=readApp()){ return app.workers.find(x=>x.id===id)?.name || 'Colaborador'; }
  function stockKey(companyId, epiId){ return `${companyId}::${epiId}`; }

  function balance(stock, companyId, epiId){
    return stock.movements
      .filter(m=>m.companyId===companyId && m.epiId===epiId)
      .reduce((sum,m)=>sum+Number(m.delta||0),0);
  }

  function trackedKeys(stock){
    const keys=new Set(Object.keys(stock.minimums||{}));
    stock.movements.forEach(m=>keys.add(stockKey(m.companyId,m.epiId)));
    return keys;
  }

  function initializeStock(){
    const stock=readStock();
    if(stock.startedAt) return;
    const app=readApp();
    stock.startedAt=new Date().toISOString();
    stock.processedDeliveryIds=app.deliveries.map(d=>d.id);
    writeStock(stock);
  }

  function syncNewDeliveries(){
    const app=readApp();
    const stock=readStock();
    const processed=new Set(stock.processedDeliveryIds||[]);
    let changed=false;

    for(const d of app.deliveries){
      if(!d?.id || processed.has(d.id)) continue;
      const totals={};
      (d.items||[]).forEach(item=>{
        if(!item.epiId) return;
        totals[item.epiId]=(totals[item.epiId]||0)+Math.max(0,Number(item.qty||0));
      });
      Object.entries(totals).forEach(([epiId,qty])=>{
        if(!qty) return;
        stock.movements.unshift({
          id:uid('sm'), type:'OUT', delta:-qty,
          companyId:d.companyId, epiId,
          deliveryId:d.id, workerId:d.workerId,
          note:`Entrega para ${workerName(d.workerId,app)}`,
          createdAt:d.createdAt || new Date().toISOString()
        });
        const key=stockKey(d.companyId,epiId);
        if(stock.minimums[key] == null) stock.minimums[key]=DEFAULT_MIN;
      });
      processed.add(d.id); changed=true;
    }

    if(changed){
      stock.processedDeliveryIds=[...processed].slice(-5000);
      writeStock(stock);
      renderStock();
    }
  }

  function fillCompanies(){
    const app=readApp();
    const sel=$('#stockCompany'); if(!sel) return;
    const old=sel.value;
    sel.innerHTML='<option value="">Selecione a empresa</option>'+app.companies.map(c=>`<option value="${c.id}">${esc(c.name)}</option>`).join('');
    if(app.companies.some(c=>c.id===old)) sel.value=old;
    else if(app.companies.length===1) sel.value=app.companies[0].id;
    fillEpis();
  }

  function fillEpis(){
    const app=readApp(); const sel=$('#stockEpi'); if(!sel) return;
    const old=sel.value;
    sel.innerHTML='<option value="">Selecione o EPI</option>'+app.epis.map(e=>`<option value="${e.id}">${esc(e.name)}${e.size?' • '+esc(e.size):''}${e.ca?' • CA '+esc(e.ca):''}</option>`).join('');
    if(app.epis.some(e=>e.id===old)) sel.value=old;
    updateCurrentBalance();
  }

  function updateCurrentBalance(){
    const companyId=$('#stockCompany')?.value||'';
    const epiId=$('#stockEpi')?.value||'';
    const hint=$('#stockCurrentBalance'); if(!hint) return;
    if(!companyId||!epiId){ hint.textContent=''; return; }
    const stock=readStock();
    const current=balance(stock,companyId,epiId);
    const min=stock.minimums[stockKey(companyId,epiId)] ?? DEFAULT_MIN;
    hint.textContent=`Saldo atual: ${current} • mínimo: ${min}`;
    const minInput=$('#stockMinimum');
    if(minInput && document.activeElement!==minInput) minInput.value=min;
  }

  function addMovement(){
    const companyId=$('#stockCompany')?.value||'';
    const epiId=$('#stockEpi')?.value||'';
    const op=$('#stockOperation')?.value||'IN';
    const qty=Number($('#stockQty')?.value||0);
    const note=String($('#stockNote')?.value||'').trim();
    const minimum=Math.max(0,Number($('#stockMinimum')?.value||DEFAULT_MIN));
    if(!companyId) return toast('Selecione a empresa.');
    if(!epiId) return toast('Selecione o EPI.');
    if(qty<0 || !Number.isFinite(qty)) return toast('Informe uma quantidade válida.');
    if(op==='IN' && qty<=0) return toast('Informe a quantidade recebida.');

    const stock=readStock();
    const current=balance(stock,companyId,epiId);
    const delta=op==='SET' ? qty-current : qty;
    stock.minimums[stockKey(companyId,epiId)]=minimum;
    stock.movements.unshift({
      id:uid('sm'), type:op, delta,
      companyId, epiId,
      note:note || (op==='SET'?'Ajuste de saldo':'Entrada de estoque'),
      createdAt:new Date().toISOString()
    });
    writeStock(stock);
    $('#stockQty').value=''; $('#stockNote').value='';
    renderStock(); updateCurrentBalance();
    toast(op==='SET'?'Saldo ajustado.':'Entrada registrada.');
  }

  function renderStock(){
    const root=$('#stock'); if(!root) return;
    const app=readApp(); const stock=readStock();
    const companyId=$('#stockCompany')?.value||'';
    const q=norm($('#stockSearch')?.value||'');
    const list=$('#stockList'), hist=$('#stockHistory');
    if(!list||!hist) return;

    if(!companyId){
      list.innerHTML='<div class="empty">Selecione a empresa para ver o estoque.</div>';
      hist.innerHTML=''; setStats(0,0,0); return;
    }

    const keys=[...trackedKeys(stock)].filter(k=>k.startsWith(companyId+'::'));
    const rows=keys.map(k=>{
      const epiId=k.slice(companyId.length+2); const epi=epiById(epiId,app)||{id:epiId,name:'EPI não encontrado'};
      const saldo=balance(stock,companyId,epiId); const min=Number(stock.minimums[k]??DEFAULT_MIN);
      return {epi,saldo,min,key:k};
    }).filter(r=>!q || [r.epi.name,r.epi.ca,r.epi.model,r.epi.size].some(v=>norm(v).includes(q)))
      .sort((a,b)=>(a.saldo<=a.min?0:1)-(b.saldo<=b.min?0:1) || String(a.epi.name).localeCompare(String(b.epi.name)));

    const allCompanyRows=keys.map(k=>{
      const epiId=k.slice(companyId.length+2); return {saldo:balance(stock,companyId,epiId),min:Number(stock.minimums[k]??DEFAULT_MIN)};
    });
    setStats(allCompanyRows.length,allCompanyRows.reduce((s,r)=>s+r.saldo,0),allCompanyRows.filter(r=>r.saldo<=r.min).length);

    list.innerHTML=rows.length ? rows.map(r=>{
      const status=r.saldo<0?'negative':r.saldo<=r.min?'low':'ok';
      const label=r.saldo<0?'SALDO NEGATIVO':r.saldo<=r.min?'ESTOQUE BAIXO':'OK';
      return `<div class="stock-item ${status}">
        <div class="stock-info"><b>${esc(r.epi.name)}</b><small>${r.epi.ca?'CA '+esc(r.epi.ca):'CA não informado'}${r.epi.size?' • Tam. '+esc(r.epi.size):''}${r.epi.model?' • '+esc(r.epi.model):''}</small></div>
        <div class="stock-balance"><strong>${r.saldo}</strong><span>mín. ${r.min}</span></div>
        <div class="stock-status ${status}">${label}</div>
        <button class="tiny" type="button" data-stock-adjust="${r.epi.id}">Ajustar</button>
      </div>`;
    }).join('') : '<div class="empty">Nenhum EPI com movimentação nesta empresa. Use “Saldo inicial / ajuste” para começar o controle.</div>';

    const moves=stock.movements.filter(m=>m.companyId===companyId).slice(0,40);
    hist.innerHTML=moves.length ? moves.map(m=>{
      const epi=epiById(m.epiId,app)||{}; const sign=Number(m.delta)>=0?'+':'';
      const type=m.type==='OUT'?'Entrega':m.type==='SET'?'Ajuste':'Entrada';
      return `<div class="stock-move"><div><b>${esc(epi.name||'EPI')}</b><small>${type} • ${new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(m.createdAt))}${m.note?' • '+esc(m.note):''}</small></div><strong>${sign}${Number(m.delta||0)}</strong></div>`;
    }).join('') : '<div class="empty compact">Sem movimentações.</div>';
  }

  function setStats(items,units,low){
    if($('#stockStatItems')) $('#stockStatItems').textContent=items;
    if($('#stockStatUnits')) $('#stockStatUnits').textContent=units;
    if($('#stockStatLow')) $('#stockStatLow').textContent=low;
  }

  function adjustFromList(epiId){
    if(!$('#stockCompany')?.value) return;
    $('#stockEpi').value=epiId;
    $('#stockOperation').value='SET';
    const stock=readStock(); const companyId=$('#stockCompany').value;
    $('#stockQty').value=balance(stock,companyId,epiId);
    $('#stockMinimum').value=stock.minimums[stockKey(companyId,epiId)] ?? DEFAULT_MIN;
    updateCurrentBalance();
    $('#stockQty').focus();
    window.scrollTo({top:0,behavior:'smooth'});
  }

  function exportStock(){
    const payload={exportedAt:new Date().toISOString(), app:'Auditar EPI', stock:readStock()};
    const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
    const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=`Auditar_EPI_Estoque_${new Date().toISOString().slice(0,10)}.json`; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),500);
  }

  function applyPracticalLayout(){
    if($('#practicalLayoutStyle')) return;

    const style=document.createElement('style');
    style.id='practicalLayoutStyle';
    style.textContent=`
      #home .hero-card{padding:18px;border-radius:20px;gap:14px}
      #home .hero-card h1{font-size:20px;line-height:1.18}
      #home .hero-card .eyebrow{margin-bottom:5px}
      #home .hero-card .primary{width:100%;min-height:62px;font-size:18px;border-radius:16px}
      #home .stats-grid{grid-template-columns:repeat(4,1fr);margin:10px 0;gap:6px}
      #home .stat{padding:9px 3px;border-radius:12px}
      #home .stat strong{font-size:18px}
      #home .stat span{font-size:9px}
      .home-section-title{font-size:12px;font-weight:900;color:#4d6663;margin:16px 2px 8px;text-transform:uppercase;letter-spacing:.06em}
      .quick-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
      .quick-card{border:1px solid var(--line);background:#fff;border-radius:16px;padding:15px;text-align:left;color:var(--text);min-height:96px;box-shadow:var(--shadow)}
      .quick-card span{font-size:25px;display:block;margin-bottom:7px}.quick-card b{display:block;font-size:15px}.quick-card small{display:block;color:var(--muted);font-size:11px;margin-top:3px}
      .quick-card.wide{grid-column:1/-1;display:grid;grid-template-columns:44px 1fr;align-items:center;min-height:72px}.quick-card.wide span{margin:0}.quick-card.wide div{min-width:0}
      .home-config{margin-top:12px;background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden}
      .home-config summary{list-style:none;padding:15px;font-weight:850;cursor:pointer;display:flex;align-items:center;justify-content:space-between}.home-config summary::-webkit-details-marker{display:none}
      .home-config summary:after{content:'⌄';font-size:18px;color:var(--muted)}.home-config[open] summary:after{content:'⌃'}
      .home-config-body{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 12px 12px}
      .config-btn{border:0;background:var(--soft);color:var(--brand);border-radius:13px;padding:13px 10px;font-weight:800;text-align:left}
      .bottom-nav{position:fixed;z-index:70;left:50%;bottom:8px;transform:translateX(-50%);width:min(94%,720px);display:grid;grid-template-columns:repeat(4,1fr);gap:4px;padding:6px;background:rgba(255,255,255,.97);border:1px solid var(--line);border-radius:18px;box-shadow:0 10px 35px rgba(0,0,0,.14);backdrop-filter:blur(12px)}
      .bottom-nav button{border:0;background:transparent;border-radius:12px;min-height:52px;color:#536d69;font-size:10px;font-weight:800;padding:5px 2px}.bottom-nav button span{display:block;font-size:20px;margin-bottom:2px}.bottom-nav .nav-primary{background:var(--brand);color:#fff}
      .delivery-more{margin-top:2px;border:1px solid var(--line);border-radius:13px;background:#fafcfc}.delivery-more summary{padding:12px 13px;font-size:12px;font-weight:850;color:var(--brand);cursor:pointer}.delivery-more-body{display:grid;gap:12px;padding:0 12px 12px}.delivery-more-body label{display:grid;gap:6px;font-size:12px;font-weight:800;color:#4d6663}
      #delivery .view-head{margin-bottom:10px}#delivery>.card{margin-bottom:10px}#delivery #btnSaveDelivery{position:sticky;bottom:76px;z-index:30;box-shadow:0 8px 25px rgba(15,118,110,.25)}
      @media(max-width:520px){#home .stats-grid{grid-template-columns:repeat(4,1fr)}.quick-grid{grid-template-columns:1fr 1fr}.bottom-nav{bottom:6px}.app-shell{padding-bottom:118px}}
      @media print{.bottom-nav{display:none!important}}
    `;
    document.head.appendChild(style);

    const home=$('#home');
    const menu=home?.querySelector('.menu-grid');
    if(home && menu && !$('#homeQuickActions')){
      const buttons={};
      [...menu.querySelectorAll('[data-go]')].forEach(btn=>buttons[btn.dataset.go]=btn);

      const title=document.createElement('div');
      title.className='home-section-title'; title.textContent='Acesso rápido';
      const quick=document.createElement('div');
      quick.id='homeQuickActions'; quick.className='quick-grid';

      const make=(go,icon,titleText,sub,wide=false)=>{
        const b=document.createElement('button');
        b.type='button'; b.dataset.go=go; b.className='quick-card'+(wide?' wide':'');
        b.innerHTML=wide?`<span>${icon}</span><div><b>${titleText}</b><small>${sub}</small></div>`:`<span>${icon}</span><b>${titleText}</b><small>${sub}</small>`;
        return b;
      };

      quick.append(
        make('workers','👷','Colaboradores','Buscar trabalhador e ficha'),
        make('history','📋','Histórico','Entregas e comprovantes'),
        make('stock','📦','Estoque','Entrada e saldo automático'),
        make('importWorkers','📥','Importar','Cadastrar vários de uma vez')
      );

      const config=document.createElement('details');
      config.className='home-config';
      config.innerHTML='<summary>⚙️ Cadastros e configurações</summary><div class="home-config-body"></div>';
      const body=config.querySelector('.home-config-body');
      body.append(
        make('companies','🏢','Empresas','Cadastro por CNPJ'),
        make('epis','🦺','EPIs','CA, modelo e tamanho')
      );
      [...body.children].forEach(x=>{x.className='config-btn';});

      menu.replaceWith(title,quick,config);
    }

    if(!$('#bottomNav')){
      const nav=document.createElement('nav'); nav.id='bottomNav'; nav.className='bottom-nav';
      nav.innerHTML=`
        <button type="button" data-go="home"><span>⌂</span>Início</button>
        <button type="button" data-go="delivery" class="nav-primary"><span>＋</span>Entrega</button>
        <button type="button" data-go="workers"><span>👷</span>Fichas</button>
        <button type="button" data-go="history"><span>📋</span>Histórico</button>`;
      document.body.appendChild(nav);
    }

    const deliveryCard=$('#delivery .card.form-grid');
    if(deliveryCard && !$('#deliveryMore')){
      const responsible=$('#deliveryResponsible')?.closest('label');
      const notes=$('#deliveryNotes')?.closest('label');
      if(responsible || notes){
        const more=document.createElement('details'); more.id='deliveryMore'; more.className='delivery-more';
        more.innerHTML='<summary>＋ Mais opções (responsável e observação)</summary><div class="delivery-more-body"></div>';
        const body=more.querySelector('.delivery-more-body');
        if(responsible) body.appendChild(responsible);
        if(notes) body.appendChild(notes);
        deliveryCard.appendChild(more);
      }
    }
  }

  document.addEventListener('DOMContentLoaded',()=>{
    applyPracticalLayout();
    initializeStock();
    syncNewDeliveries();
    fillCompanies(); renderStock();
    $('#stockCompany')?.addEventListener('change',()=>{ fillEpis(); renderStock(); });
    $('#stockEpi')?.addEventListener('change',updateCurrentBalance);
    $('#stockSearch')?.addEventListener('input',renderStock);
    $('#btnStockSave')?.addEventListener('click',addMovement);
    $('#btnStockExport')?.addEventListener('click',exportStock);
    $('#btnSaveDelivery')?.addEventListener('click',()=>setTimeout(syncNewDeliveries,0));
    document.addEventListener('click',e=>{
      if(e.target.closest('[data-go="stock"]')) setTimeout(()=>{ fillCompanies(); renderStock(); },0);
      const epiId=e.target.closest('[data-stock-adjust]')?.dataset.stockAdjust;
      if(epiId) adjustFromList(epiId);
    });
  });
})();