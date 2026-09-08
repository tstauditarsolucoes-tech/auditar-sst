(() => {
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const RETURN_MARK='DEVOLUÇÃO EPI';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const fmt=(iso,withTime=false)=>{try{return new Intl.DateTimeFormat('pt-BR',withTime?{dateStyle:'short',timeStyle:'short'}:{dateStyle:'short'}).format(new Date(iso));}catch{return '—';}};
  const dayMs=86400000;
  let holdCache={appRaw:'',stockRaw:'',rows:[]};
  let homeRefreshTimer=null;

  function readApp(){try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')};}catch{return {companies:[],workers:[],epis:[],deliveries:[]};}}
  function readStock(){try{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{},...JSON.parse(localStorage.getItem(STOCK_KEY)||'{}')};}catch{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}};}}
  function toast(msg){const el=$('#toast');if(!el)return;el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2400);}
  function companyName(app,id){return app.companies.find(c=>c.id===id)?.name||'Empresa';}
  function epiName(app,id){return app.epis.find(e=>e.id===id)?.name||'EPI';}
  function getField(note,key){const p=String(note||'').split('|').map(x=>x.trim()).find(x=>x.toLowerCase().startsWith(key.toLowerCase()+':'));return p?p.slice(p.indexOf(':')+1).trim():'';}
  function idle(fn){if('requestIdleCallback' in window)requestIdleCallback(fn,{timeout:1300});else setTimeout(fn,180);}
  function go(id){const target=document.getElementById(id);if(!target)return false;const trigger=document.querySelector(`[data-go="${CSS.escape(id)}"]`);if(trigger){trigger.click();return true;}$$('.view').forEach(v=>v.classList.remove('active'));target.classList.add('active');window.scrollTo(0,0);return true;}

  function heldRows(){
    const appRaw=localStorage.getItem(APP_KEY)||'{}',stockRaw=localStorage.getItem(STOCK_KEY)||'{}';
    if(holdCache.appRaw===appRaw&&holdCache.stockRaw===stockRaw)return holdCache.rows;
    const app=readApp(),stock=readStock();
    const workers=new Map((app.workers||[]).filter(w=>w.active!==false).map(w=>[w.id,w]));
    const epis=new Map((app.epis||[]).map(e=>[e.id,e]));
    const delivered=new Map();
    for(const d of (app.deliveries||[])){
      if(d?.cancelled||!workers.has(d?.workerId))continue;
      for(const i of (d.items||[])){
        if(!epis.has(i?.epiId))continue;
        const k=`${d.workerId}::${i.epiId}`;
        const cur=delivered.get(k)||{workerId:d.workerId,epiId:i.epiId,qty:0,latest:null};
        cur.qty+=Math.max(0,Number(i.qty||0));
        if(!cur.latest||String(d.createdAt||'')>String(cur.latest.createdAt||''))cur.latest=d;
        delivered.set(k,cur);
      }
    }
    const returned=new Map();
    for(const m of (stock.movements||[])){
      if(!String(m?.note||'').trim().startsWith(RETURN_MARK))continue;
      const workerId=m.workerId||getField(m.note,'workerId'),epiId=m.epiId;
      if(!workerId||!epiId)continue;
      const q=Math.max(0,Number(getField(m.note,'qtd')||0));
      const k=`${workerId}::${epiId}`;returned.set(k,(returned.get(k)||0)+q);
    }
    const rows=[];
    for(const [k,d] of delivered){
      const worker=workers.get(d.workerId),epi=epis.get(d.epiId);if(!worker||!epi)continue;
      const qty=Math.max(0,d.qty-(returned.get(k)||0));if(!qty)continue;
      const cycle=Math.max(0,Number(epi.cycle||0));let due=null;
      if(cycle&&d.latest?.createdAt){due=new Date(d.latest.createdAt);due.setDate(due.getDate()+cycle);}
      rows.push({worker,epi,qty,latest:d.latest,due,company:companyName(app,worker.companyId)});
    }
    holdCache={appRaw,stockRaw,rows};return rows;
  }

  function dueStatus(row){
    if(!row.due)return {key:'none',label:'Sem prazo',cls:'neutral',days:null};
    const days=Math.ceil((row.due-new Date())/dayMs);
    if(days<0)return {key:'overdue',label:`Vencido há ${Math.abs(days)}d`,cls:'bad',days};
    if(days<=15)return {key:'soon',label:`Troca em ${days}d`,cls:'warn',days};
    return {key:'ok',label:'Em dia',cls:'ok',days};
  }

  function stockSummary(companyId=''){
    const stock=readStock(),app=readApp();
    const sums=new Map();
    for(const m of (stock.movements||[])){
      if(companyId&&m.companyId!==companyId)continue;
      const k=`${m.companyId}::${m.epiId}`;sums.set(k,(sums.get(k)||0)+Number(m.delta||0));
    }
    const keys=new Set([...Object.keys(stock.minimums||{}),...sums.keys()]);
    const rows=[];
    for(const k of keys){
      const split=k.indexOf('::');if(split<0)continue;const c=k.slice(0,split),e=k.slice(split+2);if(companyId&&c!==companyId)continue;
      const epi=app.epis.find(x=>x.id===e)||{id:e,name:'EPI'};const saldo=Number(sums.get(k)||0),min=Number(stock.minimums?.[k]??5);
      rows.push({companyId:c,epi,saldo,min,company:companyName(app,c)});
    }
    return rows;
  }

  function injectNetwork(){
    const top=$('.topbar');if(!top||$('#v3Network'))return;
    const badge=document.createElement('div');badge.id='v3Network';badge.className='v3-network';badge.innerHTML='<i class="v3-network-dot"></i><span>Online</span>';
    const right=top.querySelector('div:not(:first-child)');if(right)right.appendChild(badge);else top.appendChild(badge);
    updateNetwork();
  }
  function updateNetwork(){const b=$('#v3Network');if(!b)return;const on=navigator.onLine;b.classList.toggle('offline',!on);const s=b.querySelector('span');if(s)s.textContent=on?'Online':'Offline';}

  function injectHome(){
    const home=$('#home'),grid=$('#home .menu-grid');if(!home||!grid)return;
    const hero=$('#home .hero-card h1');if(hero)hero.textContent='Entregas, devoluções, fichas, estoque e trocas no celular.';
    const eye=$('#home .eyebrow');if(eye)eye.textContent='GESTÃO EPI • MOBILE 3.0';
    if(!$('#v3HomeSearch')){
      const box=document.createElement('div');box.id='v3HomeSearch';box.className='v3-home-search';box.innerHTML='<input id="v3GlobalSearch" autocomplete="off" placeholder="Buscar colaborador, CPF, matrícula ou EPI"><div id="v3GlobalResults" class="v3-search-results"></div>';
      const stats=$('#home .stats-grid');stats?.parentNode.insertBefore(box,stats);
      $('#v3GlobalSearch')?.addEventListener('input',renderGlobalSearch);
    }
    if(!$('#v3Dashboard')){
      const dash=document.createElement('div');dash.id='v3Dashboard';dash.className='v3-dashboard';dash.innerHTML='<button class="v3-alert-card bad" data-go="alertsV3"><strong id="v3Overdue">0</strong><span>Trocas vencidas</span></button><button class="v3-alert-card warn" data-go="alertsV3"><strong id="v3Soon">0</strong><span>Trocas próximas</span></button><button class="v3-alert-card" data-go="alertsV3"><strong id="v3LowStock">0</strong><span>Estoque baixo</span></button>';
      grid.parentNode.insertBefore(dash,grid);
    }
    addHomeCard(grid,'workerSheetsV3','📄','Fichas de EPI','Ficha e histórico por colaborador');
    addHomeCard(grid,'alertsV3','🔔','Alertas','Trocas e estoque que pedem atenção');
    addHomeCard(grid,'sectorsV3','🏭','Setores','Funcionários e EPIs por setor');
    if(!grid.querySelector('[data-v3-batch]')){const b=document.createElement('button');b.className='menu-card';b.dataset.go='delivery';b.dataset.v3Batch='1';b.innerHTML='<span>👥</span><b>Entrega em lote</b><small>Mesmos EPIs para vários colaboradores</small>';grid.appendChild(b);}
    if(!$('#v3VersionLabel')){const v=document.createElement('div');v.id='v3VersionLabel';v.className='v3-version';v.textContent='Gestão EPI Mobile v3.0';home.appendChild(v);}
  }
  function addHomeCard(grid,go,icon,title,small){if(grid.querySelector(`[data-go="${go}"]`))return;const b=document.createElement('button');b.className='menu-card';b.dataset.go=go;b.innerHTML=`<span>${icon}</span><b>${title}</b><small>${small}</small>`;grid.appendChild(b);}

  function injectViews(){
    const main=$('main.app-shell');if(!main)return;
    if(!$('#workerSheetsV3')){const s=document.createElement('section');s.id='workerSheetsV3';s.className='view';s.innerHTML=`<div class="view-head"><button class="back" data-go="home">←</button><div><h2>Fichas de EPI</h2><p>Histórico e EPIs em posse de cada colaborador.</p></div></div><div id="v3SheetsFilters" class="card v3-toolbar"><label>Empresa<select id="v3SheetCompany"></select></label><label>Buscar colaborador<input id="v3SheetSearch" placeholder="Nome, CPF, matrícula, cargo ou setor"></label></div><div id="v3WorkerList" class="v3-grid"></div><div id="v3SheetDetail" class="v3-sheet-panel" style="display:none"></div>`;main.appendChild(s);}
    if(!$('#alertsV3')){const s=document.createElement('section');s.id='alertsV3';s.className='view';s.innerHTML=`<div class="view-head"><button class="back" data-go="home">←</button><div><h2>Alertas</h2><p>Prioridades de troca e estoque.</p></div></div><div class="card v3-toolbar"><label>Empresa<select id="v3AlertCompany"></select></label></div><div class="v3-subtitle">Trocas vencidas ou próximas</div><div id="v3ReplacementAlerts" class="v3-grid"></div><div class="v3-subtitle">Estoque baixo</div><div id="v3StockAlerts" class="v3-grid"></div>`;main.appendChild(s);}
    if(!$('#sectorsV3')){const s=document.createElement('section');s.id='sectorsV3';s.className='view';s.innerHTML=`<div class="view-head"><button class="back" data-go="home">←</button><div><h2>Setores</h2><p>Visão rápida por área da empresa.</p></div></div><div class="card v3-toolbar"><label>Empresa<select id="v3SectorCompany"></select></label><label>Buscar setor<input id="v3SectorSearch" placeholder="Ex.: Produção, Manutenção"></label></div><div id="v3SectorList" class="v3-grid"></div>`;main.appendChild(s);}
    if(!$('#moreV3')){const s=document.createElement('section');s.id='moreV3';s.className='view';s.innerHTML=`<div class="view-head"><button class="back" data-go="home">←</button><div><h2>Mais funções</h2><p>Cadastros e controles do Gestão EPI.</p></div></div><div class="v3-more-grid"><button class="menu-card" data-go="returnsField"><span>↩️</span><b>Devoluções</b><small>Volta ou não ao estoque</small></button><button class="menu-card" data-go="holdingsField"><span>🎒</span><b>EPIs em posse</b><small>Por colaborador</small></button><button class="menu-card" data-go="stock"><span>📦</span><b>Estoque</b><small>Saldo e movimentações</small></button><button class="menu-card" data-go="history"><span>📋</span><b>Histórico</b><small>Entregas registradas</small></button><button class="menu-card" data-go="workers"><span>👷</span><b>Funcionários</b><small>Cadastro e biometria</small></button><button class="menu-card" data-go="importWorkers"><span>📥</span><b>Importar</b><small>PDF, Excel e CSV</small></button><button class="menu-card" data-go="epis"><span>🦺</span><b>Cadastro de EPIs</b><small>CA, modelo e durabilidade</small></button><button class="menu-card" data-go="companies"><span>🏢</span><b>Empresas</b><small>Cadastro de empresas</small></button><button class="menu-card" data-go="sectorsV3"><span>🏭</span><b>Setores</b><small>Visão por área</small></button><button class="menu-card" data-go="alertsV3"><span>🔔</span><b>Alertas</b><small>Trocas e estoque</small></button></div>`;main.appendChild(s);}
  }

  function injectBottomNav(){
    if($('#v3BottomNav'))return;const n=document.createElement('nav');n.id='v3BottomNav';n.className='v3-bottom-nav';n.innerHTML='<button data-go="home"><span>⌂</span>Início</button><button data-go="delivery"><span>＋</span>Entrega</button><button data-go="workerSheetsV3"><span>📄</span>Fichas</button><button data-go="replacementsField"><span>🔄</span>Trocas</button><button data-go="moreV3"><span>☰</span>Mais</button>';document.body.appendChild(n);updateBottomNav('home');
  }
  function updateBottomNav(id){const map={companies:'moreV3',workers:'moreV3',importWorkers:'moreV3',epis:'moreV3',stock:'moreV3',history:'moreV3',receipt:'moreV3',returnsField:'moreV3',holdingsField:'moreV3',alertsV3:'moreV3',sectorsV3:'moreV3'};const active=map[id]||id;$$('#v3BottomNav button').forEach(b=>b.classList.toggle('active',b.dataset.go===active));}

  function fillCompanySelect(id,allLabel='Todas as empresas'){
    const sel=$('#'+id);if(!sel)return;const app=readApp(),old=sel.value;sel.innerHTML=`<option value="">${allLabel}</option>`+(app.companies||[]).map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('');if(app.companies.some(c=>c.id===old))sel.value=old;else if(app.companies.length===1)sel.value=app.companies[0].id;
  }

  function renderGlobalSearch(){
    const q=norm($('#v3GlobalSearch')?.value||''),root=$('#v3GlobalResults');if(!root)return;if(q.length<2){root.classList.remove('show');root.innerHTML='';return;}
    const app=readApp();const workers=(app.workers||[]).filter(w=>w.active!==false&&[w.name,w.cpf,w.reg,w.role,w.sector].some(v=>norm(v).includes(q))).slice(0,6);const epis=(app.epis||[]).filter(e=>[e.name,e.ca,e.model,e.size].some(v=>norm(v).includes(q))).slice(0,4);
    const html=[...workers.map(w=>`<button class="v3-search-row" data-v3-sheet="${esc(w.id)}"><b>👷 ${esc(w.name)}</b><small>${esc(companyName(app,w.companyId))}${w.role?' • '+esc(w.role):''}${w.sector?' • '+esc(w.sector):''}</small></button>`),...epis.map(e=>`<button class="v3-search-row" data-v3-epi="${esc(e.id)}"><b>🦺 ${esc(e.name)}</b><small>${e.ca?'CA '+esc(e.ca):'CA não informado'}${e.size?' • '+esc(e.size):''}</small></button>`)].join('');
    root.innerHTML=html||'<div class="v3-alert-empty">Nada encontrado.</div>';root.classList.add('show');
  }

  function renderHomeCounts(){
    if(!$('#home')?.classList.contains('active'))return;
    const rows=heldRows();let overdue=0,soon=0;for(const r of rows){const s=dueStatus(r);if(s.key==='overdue')overdue++;else if(s.key==='soon')soon++;}
    const low=stockSummary().filter(r=>r.saldo<=r.min).length;
    if($('#v3Overdue'))$('#v3Overdue').textContent=overdue;if($('#v3Soon'))$('#v3Soon').textContent=soon;if($('#v3LowStock'))$('#v3LowStock').textContent=low;
  }
  function scheduleHomeCounts(){clearTimeout(homeRefreshTimer);homeRefreshTimer=setTimeout(()=>idle(renderHomeCounts),180);}

  function renderWorkerList(){
    fillCompanySelect('v3SheetCompany');const app=readApp(),c=$('#v3SheetCompany')?.value||'',q=norm($('#v3SheetSearch')?.value||'');const root=$('#v3WorkerList');if(!root)return;
    const rows=(app.workers||[]).filter(w=>w.active!==false&&(!c||w.companyId===c)&&(!q||[w.name,w.cpf,w.reg,w.role,w.sector].some(v=>norm(v).includes(q)))).sort((a,b)=>String(a.name).localeCompare(String(b.name)));
    root.innerHTML=rows.length?rows.map(w=>`<article class="v3-worker-card"><div><b>${esc(w.name||'Colaborador')}</b><small>${esc(companyName(app,w.companyId))}${w.role?' • '+esc(w.role):''}${w.sector?' • '+esc(w.sector):''}</small><small>${w.cpf?esc(w.cpf):''}${w.reg?(w.cpf?' • ':'')+'Matr. '+esc(w.reg):''}</small></div><button class="v3-open" data-v3-sheet="${esc(w.id)}">Abrir ficha</button></article>`).join(''):'<div class="v3-alert-empty">Nenhum colaborador encontrado.</div>';
  }

  function renderSheet(workerId){
    const app=readApp(),w=(app.workers||[]).find(x=>x.id===workerId),root=$('#v3SheetDetail');if(!w||!root)return;
    const held=heldRows().filter(r=>r.worker.id===workerId);const deliveries=(app.deliveries||[]).filter(d=>!d.cancelled&&d.workerId===workerId).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')));
    const total=deliveries.reduce((n,d)=>n+(d.items||[]).reduce((s,i)=>s+Number(i.qty||0),0),0);const overdue=held.filter(r=>dueStatus(r).key==='overdue').length;
    root.style.display='block';root.dataset.workerId=workerId;root.innerHTML=`<div class="v3-sheet-head"><div><h3>${esc(w.name||'Colaborador')}</h3><p>${esc(companyName(app,w.companyId))}${w.role?' • '+esc(w.role):''}${w.sector?' • '+esc(w.sector):''}</p><p>${w.cpf?'CPF '+esc(w.cpf):''}${w.reg?(w.cpf?' • ':'')+'Matrícula '+esc(w.reg):''}</p></div><button class="v3-open" data-v3-close-sheet>Fechar</button></div><div class="v3-kpis"><div class="v3-kpi"><strong>${held.length}</strong><span>EPIs em posse</span></div><div class="v3-kpi"><strong>${deliveries.length}</strong><span>Entregas</span></div><div class="v3-kpi"><strong>${overdue}</strong><span>Trocas vencidas</span></div></div><div class="v3-subtitle">EPIs em posse</div><div class="v3-mini-list">${held.length?held.map(r=>{const st=dueStatus(r);return `<div class="v3-mini-row"><b>${esc(r.epi.name)} • Qtd. ${r.qty}</b><small>${r.epi.ca?'CA '+esc(r.epi.ca):'CA não informado'}${r.latest?.createdAt?' • Última entrega '+fmt(r.latest.createdAt):''}</small><span class="v3-pill ${st.cls}">${st.label}</span></div>`;}).join(''):'<div class="v3-alert-empty">Nenhum EPI em posse.</div>'}</div><div class="v3-subtitle">Histórico de entregas</div><div class="v3-mini-list">${deliveries.length?deliveries.slice(0,30).map(d=>`<div class="v3-mini-row"><b>${fmt(d.createdAt,true)} • ${(d.items||[]).reduce((s,i)=>s+Number(i.qty||0),0)} unidade(s)</b><small>${esc(d.reason||'Entrega')} • ${(d.items||[]).map(i=>esc(epiName(app,i.epiId))+' x'+Number(i.qty||0)).join(', ')}</small></div>`).join(''):'<div class="v3-alert-empty">Sem entregas registradas.</div>'}</div><div class="v3-sheet-actions"><button class="main" data-v3-deliver="${esc(w.id)}">＋ Nova entrega para este colaborador</button><button class="alt" data-v3-print>🖨️ Imprimir / PDF</button></div><small style="display:block;color:var(--muted);margin-top:9px">Total histórico entregue: ${total} unidade(s).</small>`;
    root.scrollIntoView({behavior:'smooth',block:'start'});
  }

  function startDelivery(workerId){
    const app=readApp(),w=(app.workers||[]).find(x=>x.id===workerId);if(!w)return;go('delivery');setTimeout(()=>{const c=$('#deliveryCompany'),sel=$('#deliveryWorker');if(c){c.value=w.companyId;c.dispatchEvent(new Event('change',{bubbles:true}));}setTimeout(()=>{if(sel){sel.value=w.id;sel.dispatchEvent(new Event('change',{bubbles:true}));sel.scrollIntoView({behavior:'smooth',block:'center'});}},90);},80);
  }

  function renderAlerts(){
    fillCompanySelect('v3AlertCompany');const c=$('#v3AlertCompany')?.value||'';const rep=$('#v3ReplacementAlerts'),stk=$('#v3StockAlerts');if(!rep||!stk)return;
    const rows=heldRows().filter(r=>!c||r.worker.companyId===c).map(r=>({r,s:dueStatus(r)})).filter(x=>x.s.key==='overdue'||x.s.key==='soon').sort((a,b)=>(a.s.days??9999)-(b.s.days??9999));
    rep.innerHTML=rows.length?rows.map(({r,s})=>`<article class="v3-alert-row"><div><b>${esc(r.worker.name)} • ${esc(r.epi.name)}</b><small>${esc(r.company)}${r.worker.sector?' • '+esc(r.worker.sector):''} • Qtd. ${r.qty}</small></div><span class="v3-alert-value ${s.cls}">${s.label}</span></article>`).join(''):'<div class="v3-alert-empty">Nenhuma troca vencida ou próxima.</div>';
    const lows=stockSummary(c).filter(r=>r.saldo<=r.min).sort((a,b)=>a.saldo-b.saldo);
    stk.innerHTML=lows.length?lows.map(r=>`<article class="v3-alert-row"><div><b>${esc(r.epi.name)}</b><small>${esc(r.company)}${r.epi.ca?' • CA '+esc(r.epi.ca):''} • mínimo ${r.min}</small></div><span class="v3-alert-value ${r.saldo<0?'bad':'warn'}">Saldo ${r.saldo}</span></article>`).join(''):'<div class="v3-alert-empty">Nenhum item com estoque baixo.</div>';
  }

  function renderSectors(){
    fillCompanySelect('v3SectorCompany');const app=readApp(),c=$('#v3SectorCompany')?.value||'',q=norm($('#v3SectorSearch')?.value||''),root=$('#v3SectorList');if(!root)return;
    const workers=(app.workers||[]).filter(w=>w.active!==false&&(!c||w.companyId===c));const groups=new Map();for(const w of workers){const name=String(w.sector||'Sem setor').trim()||'Sem setor';if(q&&!norm(name).includes(q))continue;const g=groups.get(name)||{name,workers:[],held:0,deliveries:0};g.workers.push(w);groups.set(name,g);}
    const holds=heldRows();for(const g of groups.values()){const ids=new Set(g.workers.map(w=>w.id));g.held=holds.filter(r=>ids.has(r.worker.id)).reduce((s,r)=>s+r.qty,0);g.deliveries=(app.deliveries||[]).filter(d=>!d.cancelled&&ids.has(d.workerId)).length;}
    const rows=[...groups.values()].sort((a,b)=>b.workers.length-a.workers.length||a.name.localeCompare(b.name));
    root.innerHTML=rows.length?rows.map(g=>`<article class="v3-sector-card"><b>${esc(g.name)}</b><small>${g.workers.length} colaborador(es) • ${g.held} EPI(s) em posse • ${g.deliveries} entrega(s)</small><details><summary>Ver colaboradores</summary><div class="v3-sector-people">${g.workers.map(w=>`<span>${esc(w.name)}</span>`).join('')}</div></details></article>`).join(''):'<div class="v3-alert-empty">Nenhum setor encontrado.</div>';
  }

  function handleRoute(id){
    updateBottomNav(id);
    if(id==='home')scheduleHomeCounts();
    if(id==='workerSheetsV3'){renderWorkerList();const d=$('#v3SheetDetail');if(d)d.style.display='none';}
    if(id==='alertsV3')idle(renderAlerts);
    if(id==='sectorsV3')idle(renderSectors);
  }

  function bind(){
    document.addEventListener('click',e=>{
      const route=e.target.closest('[data-go]');if(route)setTimeout(()=>handleRoute(route.dataset.go),30);
      const sheet=e.target.closest('[data-v3-sheet]');if(sheet){e.preventDefault();$('#v3GlobalResults')?.classList.remove('show');go('workerSheetsV3');setTimeout(()=>renderSheet(sheet.dataset.v3Sheet),70);}
      const epi=e.target.closest('[data-v3-epi]');if(epi){e.preventDefault();$('#v3GlobalResults')?.classList.remove('show');go('epis');setTimeout(()=>{const input=$('#epiName');if(input){input.value='';input.placeholder='EPI localizado na busca';}},50);}
      const close=e.target.closest('[data-v3-close-sheet]');if(close){const d=$('#v3SheetDetail');if(d)d.style.display='none';}
      const deliver=e.target.closest('[data-v3-deliver]');if(deliver)startDelivery(deliver.dataset.v3Deliver);
      if(e.target.closest('[data-v3-print]')){document.body.classList.add('v3-sheet-print');window.print();setTimeout(()=>document.body.classList.remove('v3-sheet-print'),600);}
      const batch=e.target.closest('[data-v3-batch]');if(batch){setTimeout(()=>{const company=$('#deliveryCompany');const app=readApp();if(company&&!company.value&&app.companies.length===1){company.value=app.companies[0].id;company.dispatchEvent(new Event('change',{bubbles:true}));}setTimeout(()=>{const b=$('#btnBulkDelivery');if(b&&company?.value)b.click();else toast('Selecione a empresa e toque em “Entrega em lote”.');},120);},120);}
      if(!e.target.closest('#v3HomeSearch'))$('#v3GlobalResults')?.classList.remove('show');
    },true);
    $('#v3SheetCompany')?.addEventListener('change',renderWorkerList);$('#v3SheetSearch')?.addEventListener('input',renderWorkerList);$('#v3AlertCompany')?.addEventListener('change',()=>idle(renderAlerts));$('#v3SectorCompany')?.addEventListener('change',()=>idle(renderSectors));$('#v3SectorSearch')?.addEventListener('input',()=>idle(renderSectors));
    window.addEventListener('online',()=>{updateNetwork();scheduleHomeCounts();});window.addEventListener('offline',updateNetwork);
    document.addEventListener('gestao-epi-sync-applied',()=>{holdCache.appRaw='';setTimeout(()=>{if($('#home')?.classList.contains('active'))scheduleHomeCounts();},500);});
    document.addEventListener('auditar-epi-state-refreshed',()=>{holdCache.appRaw='';if($('#home')?.classList.contains('active'))scheduleHomeCounts();});
    document.addEventListener('auditar-epi-data-changed',()=>{holdCache.appRaw='';if($('#home')?.classList.contains('active'))scheduleHomeCounts();});
    document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(()=>{injectNetwork();updateNetwork();scheduleHomeCounts();},120));
  }

  function init(){
    if(document.documentElement.dataset.gestaoEpiMobileV3==='1')return;document.documentElement.dataset.gestaoEpiMobileV3='1';
    injectNetwork();injectHome();injectViews();injectBottomNav();bind();
    [250,700,1500].forEach(ms=>setTimeout(()=>{injectHome();injectNetwork();},ms));
    scheduleHomeCounts();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
