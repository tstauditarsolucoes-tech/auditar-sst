(()=>{
  'use strict';

  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const UX_KEY='gestaoEpiUxV300';
  const RETURN_MARK='DEVOLUÇÃO EPI';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const norm=v=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt=(v,withTime=false)=>{if(!v)return '—';const d=new Date(v);if(Number.isNaN(d.getTime()))return '—';return new Intl.DateTimeFormat('pt-BR',withTime?{dateStyle:'short',timeStyle:'short'}:{dateStyle:'short'}).format(d);};
  let decorateTimer=0,observer=null,lastDeliveryId='',qrStream=null,qrLoop=0;

  function readApp(){
    try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')};}
    catch(_){return {companies:[],workers:[],epis:[],deliveries:[]};}
  }
  function readStock(){
    try{return {movements:[],minimums:{},...JSON.parse(localStorage.getItem(STOCK_KEY)||'{}')};}
    catch(_){return {movements:[],minimums:{}};}
  }
  function readUx(){
    try{
      const x=JSON.parse(localStorage.getItem(UX_KEY)||'{}');
      return {
        favorites:Array.isArray(x.favorites)?x.favorites:[],
        recent:Array.isArray(x.recent)?x.recent:[],
        kits:x.kits&&typeof x.kits==='object'?x.kits:{},
        menuExpanded:x.menuExpanded===true
      };
    }catch(_){return {favorites:[],recent:[],kits:{},menuExpanded:false};}
  }
  function writeUx(x){localStorage.setItem(UX_KEY,JSON.stringify(x));}
  function toast(msg){
    const el=$('#toast');if(!el)return alert(msg);
    el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);
  }
  function companyName(app,id){return app.companies.find(c=>c.id===id)?.name||'Empresa';}
  function canOperate(){const role=String(window.GestaoEpiAuth?.user?.()?.role||document.body.dataset.epiRole||'');return role==='admin'||role==='campo';}
  function epi(app,id){return app.epis.find(e=>e.id===id)||{};}
  function getField(note,key){
    const p=String(note||'').split('|').map(x=>x.trim()).find(x=>x.toLowerCase().startsWith(String(key).toLowerCase()+':'));
    return p?p.slice(p.indexOf(':')+1).trim():'';
  }
  function returnedQty(stock,workerId,epiId){
    return (stock.movements||[])
      .filter(m=>String(m?.note||'').trim().startsWith(RETURN_MARK)&&m.epiId===epiId&&getField(m.note,'workerId')===workerId)
      .reduce((s,m)=>s+Math.max(0,Number(getField(m.note,'qtd')||0)),0);
  }
  function deliveryItems(app,workerId,epiId){
    return app.deliveries
      .filter(d=>d.workerId===workerId&&d.cancelled!==true)
      .flatMap(d=>(d.items||[]).filter(i=>i.epiId===epiId).map(i=>({delivery:d,qty:Number(i.qty||0)})));
  }
  function heldRows(workerId){
    const app=readApp(),stock=readStock(),rows=[];
    app.epis.forEach(e=>{
      const deliveries=deliveryItems(app,workerId,e.id);
      const delivered=deliveries.reduce((s,x)=>s+Math.max(0,x.qty),0);
      const qty=Math.max(0,delivered-returnedQty(stock,workerId,e.id));
      if(!qty)return;
      const latest=deliveries.sort((a,b)=>String(b.delivery.createdAt||'').localeCompare(String(a.delivery.createdAt||'')))[0]?.delivery||null;
      const cycle=Number(e.cycle||0);
      let due=null,days=null,status='none';
      if(latest&&cycle>0){
        const d=new Date(latest.createdAt);
        if(!Number.isNaN(d.getTime())){
          due=new Date(d.getTime()+cycle*86400000);
          days=Math.ceil((due.getTime()-Date.now())/86400000);
          status=days<0?'overdue':days<=15?'soon':'ok';
        }
      }
      rows.push({epi:e,qty,latest,due,days,status});
    });
    return rows.sort((a,b)=>{
      const o={overdue:0,soon:1,ok:2,none:3};
      return (o[a.status]??4)-(o[b.status]??4)||String(a.epi.name||'').localeCompare(String(b.epi.name||''));
    });
  }
  function rememberWorker(id){
    const ux=readUx();
    ux.recent=[id,...ux.recent.filter(x=>x!==id)].slice(0,8);
    writeUx(ux);renderRecentFavorites();
  }
  function toggleFavorite(id){
    const ux=readUx();
    ux.favorites=ux.favorites.includes(id)?ux.favorites.filter(x=>x!==id):[id,...ux.favorites].slice(0,12);
    writeUx(ux);renderWorker360(id);renderRecentFavorites();
  }
  function nav(id){
    const b=document.querySelector('[data-go="'+id+'"]');
    if(b){b.click();return;}
    $$('.view').forEach(v=>v.classList.remove('active'));
    $('#'+id)?.classList.add('active');
    window.scrollTo({top:0,behavior:'smooth'});
  }

  function injectStyles(){
    if($('#uxV300Styles'))return;
    const s=document.createElement('style');s.id='uxV300Styles';s.textContent=`
      :root{--ux-brand:#078468;--ux-brand2:#0b5d56;--ux-ink:#173b47;--ux-muted:#6c817d;--ux-line:#d8e6e2;--ux-soft:#f2f8f6;--ux-danger:#b42318;--ux-warn:#a15c00}
      .topbar .brand{display:flex!important;align-items:center;gap:8px;font-size:0!important}.topbar .brand::after{content:'Gestão EPI';font-size:18px;font-weight:950;color:var(--ux-ink)}.topbar .brand img{width:34px;height:34px;display:block}.topbar .subtitle{margin-left:42px;margin-top:-7px}
      .ux-online-pill{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--ux-line);border-radius:999px;padding:5px 8px;background:#fff;font-size:9px;font-weight:900;color:#46645e;margin-left:auto}.ux-online-pill i{width:7px;height:7px;border-radius:50%;background:#15946f}.ux-online-pill.offline{color:#a15c00;background:#fff7ea}.ux-online-pill.offline i{background:#d97a12}
      .ux-search{position:relative;margin:12px 0}.ux-search input{width:100%;height:50px;border:1px solid var(--ux-line);border-radius:14px;padding:0 44px 0 14px;background:#fff;font-size:14px;box-shadow:0 6px 18px rgba(23,59,71,.04)}.ux-search::after{content:'⌕';position:absolute;right:16px;top:11px;font-size:25px;color:#66817c}.ux-search-results{display:none;position:absolute;z-index:120;left:0;right:0;top:55px;background:#fff;border:1px solid var(--ux-line);border-radius:14px;box-shadow:0 20px 45px rgba(23,59,71,.14);max-height:330px;overflow:auto}.ux-search-results.open{display:block}.ux-search-row{width:100%;border:0;border-bottom:1px solid #edf2f1;background:#fff;padding:11px 12px;text-align:left;color:var(--ux-ink)}.ux-search-row:last-child{border-bottom:0}.ux-search-row b{display:block;font-size:12px}.ux-search-row small{display:block;color:var(--ux-muted);font-size:10px;margin-top:3px}
      .ux-quick{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin:12px 0}.ux-quick button{border:1px solid var(--ux-line);border-radius:16px;background:#fff;padding:13px;text-align:left;color:var(--ux-ink);min-height:82px;box-shadow:0 6px 19px rgba(23,59,71,.045)}.ux-quick button.primary{grid-column:1/-1;background:linear-gradient(135deg,#0a9475,#076a5d);color:#fff;border:0}.ux-quick button span{font-size:21px;display:block}.ux-quick button b{display:block;font-size:13px;margin-top:5px}.ux-quick button small{display:block;font-size:9px;opacity:.78;margin-top:2px}
      #home .menu-grid.ux-collapsed{display:none}.ux-more{width:100%;border:1px solid var(--ux-line);background:#fff;border-radius:13px;padding:11px;color:var(--ux-brand2);font-weight:900;margin:4px 0 10px}
      .ux-people{display:grid;gap:8px;margin:10px 0}.ux-person-row{display:flex;align-items:center;gap:10px;border:1px solid var(--ux-line);background:#fff;border-radius:13px;padding:10px}.ux-person-row button{border:0;background:transparent;text-align:left;min-width:0;flex:1;color:var(--ux-ink)}.ux-person-row b{display:block;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.ux-person-row small{display:block;color:var(--ux-muted);font-size:9px;margin-top:2px}.ux-star{font-size:18px!important;flex:0 0 auto!important}
      .ux-worker-btn{border:1px solid #cce0db;background:#edf8f5;color:var(--ux-brand2);border-radius:8px;padding:6px 8px;font-size:10px;font-weight:900}
      .ux-view{display:none}.ux-view.active{display:block}.ux360-head{background:linear-gradient(135deg,#123f48,#08725f);border-radius:20px;padding:18px;color:#fff;margin-bottom:12px}.ux360-head h2{margin:0;font-size:21px}.ux360-head p{margin:6px 0 0;color:#d7efea;font-size:11px}.ux360-meta{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:13px}.ux360-meta div{border:1px solid rgba(255,255,255,.15);border-radius:10px;padding:8px}.ux360-meta small{display:block;font-size:8px;color:#c6e1dc;text-transform:uppercase;font-weight:900}.ux360-meta b{font-size:10px}.ux360-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.ux360-actions button{border:0;border-radius:13px;padding:11px;font-weight:900;background:#fff;color:var(--ux-brand2);border:1px solid var(--ux-line)}.ux360-actions button.primary{background:var(--ux-brand);color:#fff;border-color:var(--ux-brand)}.ux-card{background:#fff;border:1px solid var(--ux-line);border-radius:16px;padding:13px;margin:10px 0}.ux-card h3{margin:0 0 9px;font-size:14px;color:var(--ux-ink)}.ux-held{display:grid;gap:7px}.ux-held-row{border:1px solid #e2ece9;border-radius:12px;padding:10px;background:#fbfdfc}.ux-held-top{display:flex;justify-content:space-between;gap:8px}.ux-held-row b{font-size:11px}.ux-held-row small{display:block;color:var(--ux-muted);font-size:9px;line-height:1.45;margin-top:3px}.ux-pill{padding:4px 7px;border-radius:999px;font-size:8px;font-weight:950;white-space:nowrap}.ux-pill.ok{background:#e8f7ef;color:#11633c}.ux-pill.soon{background:#fff4e3;color:#985600}.ux-pill.overdue{background:#fff0ee;color:#b42318}.ux-pill.none{background:#eef2f2;color:#627471}.ux-held-actions{display:flex;gap:6px;margin-top:8px}.ux-held-actions button{border:0;background:#e9f5f2;color:#0b6a5d;border-radius:8px;padding:6px 8px;font-size:9px;font-weight:900}
      .ux-modal{position:fixed;inset:0;z-index:50000;background:rgba(5,35,32,.72);display:none;align-items:center;justify-content:center;padding:16px}.ux-modal.open{display:flex}.ux-modal-card{width:min(620px,100%);max-height:90vh;overflow:auto;background:#fff;border-radius:20px;padding:18px;box-shadow:0 28px 80px rgba(0,0,0,.28)}.ux-modal-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}.ux-modal-head h2{margin:0;color:var(--ux-ink);font-size:17px}.ux-modal-head p{margin:4px 0 0;color:var(--ux-muted);font-size:10px}.ux-close{border:0;border-radius:10px;background:#edf5f3;width:38px;height:38px;font-size:20px}.ux-modal-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.ux-modal-actions button{border:0;border-radius:10px;padding:9px 11px;font-weight:900}.ux-modal-actions .p{background:var(--ux-brand);color:#fff}.ux-modal-actions .s{background:#eaf5f2;color:var(--ux-brand2)}.ux-checklist{display:grid;gap:7px;margin-top:12px}.ux-check{display:flex;gap:9px;align-items:center;border:1px solid var(--ux-line);border-radius:11px;padding:9px}.ux-check input{width:18px;height:18px}.ux-check span{font-size:11px;color:var(--ux-ink)}
      .ux-qrbox{display:grid;place-items:center;min-height:220px;margin:14px 0;background:#fff;border:1px solid var(--ux-line);border-radius:14px;padding:14px}.ux-qr-code{font-family:monospace;background:#f2f7f6;border-radius:9px;padding:8px;font-size:10px;word-break:break-all;color:#45615d}
      .ux-scanner-video{width:100%;max-height:55vh;background:#071b1a;border-radius:14px}.ux-success-icon{width:72px;height:72px;border-radius:50%;display:grid;place-items:center;margin:0 auto 12px;background:#e8f7ef;color:#147047;font-size:38px}.ux-success{text-align:center}.ux-success h2{margin:0;color:var(--ux-ink)}.ux-success p{color:var(--ux-muted);font-size:11px;line-height:1.5}
      .epi-auth-overlay{background:linear-gradient(160deg,#e9f5f2 0,#f9fbfb 48%,#eef7f5 100%)!important}.epi-auth-card{max-width:430px!important;border-radius:24px!important;padding:24px!important;box-shadow:0 28px 70px rgba(18,62,57,.16)!important}.epi-auth-mark{width:auto!important;height:auto!important;background:transparent!important;margin:0 auto 12px!important}.epi-auth-mark img{display:block;width:min(270px,82vw);height:auto;margin:auto}.epi-auth-card h1{font-size:22px!important;color:var(--ux-ink)!important;margin-top:6px!important}.epi-auth-card>p{font-size:11px!important;line-height:1.5!important;color:var(--ux-muted)!important}.ux-login-benefit{background:#f0f8f6;border:1px solid #d7e9e4;border-radius:13px;padding:10px 12px;margin:10px 0 12px;color:#46645e;font-size:10px;line-height:1.5}.ux-login-benefit b{color:var(--ux-brand2)}
      @media(min-width:700px){.ux-quick{grid-template-columns:repeat(5,1fr)}.ux-quick button.primary{grid-column:auto}.ux360-actions{grid-template-columns:repeat(5,1fr)}}
    `;document.head.appendChild(s);
  }

  function applyBrand(){
    const brand=$('.topbar .brand');
    if(brand&&!brand.querySelector('img'))brand.innerHTML='<img src="gestao-epi-icon-v300.svg" alt=""><span style="display:none">Gestão EPI</span>';
    document.documentElement.style.setProperty('--brand','#078468');
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content','#078468');
  }

  function improveLogin(){
    const card=$('#epiAuthOverlay .epi-auth-card');if(!card)return;
    const mark=card.querySelector('.epi-auth-mark');
    if(mark&&!mark.querySelector('img'))mark.innerHTML='<img src="gestao-epi-logo-v300.svg" alt="Gestão EPI Auditar">';
    const h=card.querySelector('h1');if(h)h.textContent='Bem-vindo ao Gestão EPI';
    const p=card.querySelector('p');if(p)p.textContent='Controle de EPI com segurança, rastreabilidade e agilidade.';
    if(!card.querySelector('.ux-login-benefit')){
      const box=document.createElement('div');box.className='ux-login-benefit';
      box.innerHTML='<b>Proteja pessoas. Simplifique a gestão.</b><br>Entregas, estoque, CA, biometria, trocas e histórico em um só lugar.';
      const firstLabel=card.querySelector('label');card.insertBefore(box,firstLabel);
    }
  }

  function onlinePill(){
    const top=$('.topbar');if(!top)return;
    let pill=$('#uxOnlinePill');if(!pill){pill=document.createElement('div');pill.id='uxOnlinePill';pill.className='ux-online-pill';pill.innerHTML='<i></i><span></span>';top.appendChild(pill);}
    const online=navigator.onLine;pill.classList.toggle('offline',!online);
    const sync=$('#syncStatus')?.textContent?.trim();
    pill.querySelector('span').textContent=online?(sync&&sync.length<42?sync:'Online'):'Offline • salvando localmente';
  }

  function injectHome(){
    const home=$('#home');if(!home)return;
    if(!$('#uxGlobalSearch')){
      const search=document.createElement('div');search.id='uxGlobalSearch';search.className='ux-search';
      search.innerHTML='<input id="uxGlobalSearchInput" placeholder="Buscar trabalhador, EPI, CA, empresa ou matrícula"><div id="uxGlobalSearchResults" class="ux-search-results"></div>';
      const hero=home.querySelector('.hero-card');hero?.insertAdjacentElement('afterend',search);
      $('#uxGlobalSearchInput').addEventListener('input',renderSearch);
      $('#uxGlobalSearchInput').addEventListener('focus',renderSearch);
    }
    if(!$('#uxQuickHome')){
      const q=document.createElement('div');q.id='uxQuickHome';q.className='ux-quick';
      q.innerHTML=`
        <button class="primary" data-ux-action="delivery"><span>＋</span><b>Nova entrega</b><small>Fluxo rápido de campo</small></button>
        <button data-ux-action="scan"><span>▣</span><b>Ler QR</b><small>Abrir trabalhador</small></button>
        <button data-ux-action="workers"><span>👷</span><b>Trabalhadores</b><small>Ficha 360°</small></button>
        <button data-ux-action="replace"><span>↻</span><b>Trocar / devolver</b><small>Atalhos inteligentes</small></button>
        <button data-ux-action="stock"><span>▤</span><b>Estoque</b><small>Saldo e movimentação</small></button>`;
      const search=$('#uxGlobalSearch');search?.insertAdjacentElement('afterend',q);
    }
    if(!$('#uxRecentFav')){
      const wrap=document.createElement('div');wrap.id='uxRecentFav';wrap.className='ux-card';
      wrap.innerHTML='<h3>Favoritos e recentes</h3><div id="uxRecentFavList" class="ux-people"></div>';
      const quick=$('#uxQuickHome');quick?.insertAdjacentElement('afterend',wrap);
    }
    const menu=home.querySelector('.menu-grid');
    if(menu){
      const ux=readUx();menu.classList.toggle('ux-collapsed',!ux.menuExpanded);
      if(!$('#uxMoreResources')){
        const b=document.createElement('button');b.id='uxMoreResources';b.className='ux-more';b.type='button';
        menu.insertAdjacentElement('beforebegin',b);b.onclick=()=>{const x=readUx();x.menuExpanded=!x.menuExpanded;writeUx(x);menu.classList.toggle('ux-collapsed',!x.menuExpanded);updateMoreLabel();};
      }
      updateMoreLabel();
    }
    const op=canOperate();$('#uxQuickHome [data-ux-action="delivery"],#uxQuickHome [data-ux-action="replace"]').forEach(b=>b.style.display=op?'':'none');
    renderRecentFavorites();
  }
  function updateMoreLabel(){const b=$('#uxMoreResources');if(b)b.textContent=readUx().menuExpanded?'Ocultar recursos administrativos':'Mais recursos';}

  function renderSearch(){
    const input=$('#uxGlobalSearchInput'),box=$('#uxGlobalSearchResults');if(!input||!box)return;
    const q=norm(input.value);if(q.length<2){box.classList.remove('open');box.innerHTML='';return;}
    const app=readApp(),rows=[];
    app.workers.filter(w=>w.active!==false&&[w.name,w.cpf,w.reg,w.role,w.sector].some(v=>norm(v).includes(q))).slice(0,6).forEach(w=>rows.push({type:'worker',id:w.id,title:w.name,sub:`Trabalhador • ${companyName(app,w.companyId)}${w.role?' • '+w.role:''}`}));
    app.epis.filter(e=>[e.name,e.ca,e.model,e.size].some(v=>norm(v).includes(q))).slice(0,5).forEach(e=>rows.push({type:'epi',id:e.id,title:e.name,sub:`EPI${e.ca?' • CA '+e.ca:''}`}));
    app.companies.filter(c=>[c.name,c.cnpj].some(v=>norm(v).includes(q))).slice(0,4).forEach(c=>rows.push({type:'company',id:c.id,title:c.name,sub:'Empresa'}));
    box.innerHTML=rows.length?rows.map(r=>`<button class="ux-search-row" data-ux-search="${r.type}|${esc(r.id)}"><b>${esc(r.title)}</b><small>${esc(r.sub)}</small></button>`).join(''):'<div class="ux-search-row"><b>Nenhum resultado</b></div>';
    box.classList.add('open');
  }

  function renderRecentFavorites(){
    const box=$('#uxRecentFavList');if(!box)return;
    const app=readApp(),ux=readUx(),ids=[...ux.favorites,...ux.recent].filter((x,i,a)=>a.indexOf(x)===i).slice(0,6);
    const rows=ids.map(id=>app.workers.find(w=>w.id===id)).filter(Boolean);
    box.innerHTML=rows.length?rows.map(w=>`<div class="ux-person-row"><button data-worker-360="${esc(w.id)}"><b>${ux.favorites.includes(w.id)?'★ ':''}${esc(w.name)}</b><small>${esc(w.role||w.sector||companyName(app,w.companyId))}</small></button><button class="ux-star" data-ux-fav="${esc(w.id)}">${ux.favorites.includes(w.id)?'★':'☆'}</button></div>`).join(''):'<div class="empty">Os trabalhadores usados com mais frequência aparecerão aqui.</div>';
  }

  function injectWorker360(){
    if($('#worker360'))return;
    const main=$('.app-shell')||$('main');if(!main)return;
    const sec=document.createElement('section');sec.id='worker360';sec.className='view ux-view';
    sec.innerHTML='<div class="view-head"><button class="back" data-go="workers">←</button><div><h2>Trabalhador 360°</h2><p>Entrega, posse, trocas e histórico em uma tela.</p></div></div><div id="worker360Body"></div>';
    main.appendChild(sec);
  }

  function renderWorker360(id){
    injectWorker360();
    const app=readApp(),w=app.workers.find(x=>x.id===id),box=$('#worker360Body');if(!w||!box)return;
    rememberWorker(id);
    const ux=readUx(),fav=ux.favorites.includes(id),rows=heldRows(id);
    const deliveries=app.deliveries.filter(d=>d.workerId===id&&d.cancelled!==true).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')));
    const bio=!!(window.GestaoEpiBiometricCrypto?.hasTemplate?.(w)||(Array.isArray(w?.biometric?.embedding)&&w.biometric.embedding.length));
    box.innerHTML=`
      <div class="ux360-head">
        <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start"><div><h2>${esc(w.name||'Trabalhador')}</h2><p>${esc(companyName(app,w.companyId))}</p></div><button class="ux-star" data-ux-fav="${esc(w.id)}" style="border:0;background:transparent;color:#fff">${fav?'★':'☆'}</button></div>
        <div class="ux360-meta">
          <div><small>Cargo</small><b>${esc(w.role||'—')}</b></div><div><small>Setor</small><b>${esc(w.sector||'—')}</b></div>
          <div><small>Matrícula</small><b>${esc(w.reg||'—')}</b></div><div><small>Biometria</small><b>${bio?'Cadastrada':'Não cadastrada'}</b></div>
        </div>
      </div>
      <div class="ux360-actions">
        ${canOperate()?`<button class="primary" data-ux-deliver="${esc(w.id)}">＋ Entregar EPI</button><button data-ux-kit="${esc(w.id)}">🧰 Kit da função</button><button data-ux-return="${esc(w.id)}">↩ Devolver</button>`:''}
        <button data-ux-qr="${esc(w.id)}">▣ QR do trabalhador</button>
        ${canOperate()?`<button data-ux-portal="${esc(w.id)}">🌐 Portal</button>`:''}
      </div>
      <div class="ux-card"><h3>EPIs em posse</h3><div class="ux-held">${rows.length?rows.map(r=>heldHtml(w,r)).join(''):'<div class="empty">Nenhum EPI em posse.</div>'}</div></div>
      <div class="ux-card"><h3>Últimas entregas</h3>${deliveries.length?deliveries.slice(0,5).map(d=>`<div class="ux-held-row"><b>${fmt(d.createdAt,true)} • ${esc(d.reason||'Entrega')}</b><small>${(d.items||[]).map(i=>{const e=epi(app,i.epiId);return esc(e.name||'EPI')+' × '+Number(i.qty||0)}).join(' • ')}</small></div>`).join(''):'<div class="empty">Sem entregas registradas.</div>'}</div>`;
    nav('worker360');
  }

  function heldHtml(w,r){
    const label=r.status==='overdue'?`Vencido há ${Math.abs(r.days)}d`:r.status==='soon'?`Troca em ${r.days}d`:r.status==='ok'?`Em dia • ${r.days}d`:'Sem prazo';
    return `<div class="ux-held-row"><div class="ux-held-top"><div><b>${esc(r.epi.name||'EPI')} • Qtd. ${r.qty}</b><small>${r.epi.ca?'CA '+esc(r.epi.ca)+' • ':''}${r.latest?'Última entrega '+fmt(r.latest.createdAt):''}${r.due?' • Próxima '+fmt(r.due.toISOString()):''}</small></div><span class="ux-pill ${r.status}">${esc(label)}</span></div><div class="ux-held-actions"><button data-ux-swap="${esc(w.id)}|${esc(r.epi.id)}">Trocar agora</button><button data-ux-return-epi="${esc(w.id)}|${esc(r.epi.id)}">Devolver</button></div></div>`;
  }

  function decorateWorkers(){
    const list=$('#workerList');if(!list)return;
    list.querySelectorAll('.list-item').forEach(item=>{
      const del=item.querySelector('[data-del-worker]'),id=del?.dataset.delWorker;if(!id||item.querySelector('[data-worker-360]'))return;
      const actions=item.querySelector('.list-actions')||item;
      const b=document.createElement('button');b.type='button';b.className='tiny ux-worker-btn';b.dataset.worker360=id;b.textContent='360°';
      actions.insertBefore(b,actions.firstChild);
    });
  }

  function prefillDelivery(workerId,epiIds=[],reason=''){
    const app=readApp(),w=app.workers.find(x=>x.id===workerId);if(!w)return;
    rememberWorker(workerId);nav('delivery');
    setTimeout(()=>{
      const comp=$('#deliveryCompany');if(comp){comp.value=w.companyId;comp.dispatchEvent(new Event('change',{bubbles:true}));}
      setTimeout(()=>{
        const worker=$('#deliveryWorker');if(worker){worker.value=workerId;worker.dispatchEvent(new Event('change',{bubbles:true}));}
        if(reason&&$('#deliveryReason'))$('#deliveryReason').value=reason;
        if(epiIds.length){
          const need=epiIds.length;
          while($$('.delivery-item').length<need)$('#btnAddItem')?.click();
          $$('.delivery-item').forEach((row,i)=>{
            if(i>=need)return;
            const sel=row.querySelector('.item-epi'),qty=row.querySelector('.item-qty');
            if(sel)sel.value=epiIds[i];if(qty)qty.value='1';
          });
        }
      },140);
    },120);
  }

  function quickSwap(workerId,epiId){prefillDelivery(workerId,[epiId],'Substituição por desgaste');}
  function prefillReturn(workerId,epiId=''){
    const app=readApp(),w=app.workers.find(x=>x.id===workerId);if(!w)return;
    nav('epiReturn');setTimeout(()=>{
      if($('#returnCompany')){$('#returnCompany').value=w.companyId;$('#returnCompany').dispatchEvent(new Event('change',{bubbles:true}));}
      setTimeout(()=>{if($('#returnWorker')){$('#returnWorker').value=workerId;$('#returnWorker').dispatchEvent(new Event('change',{bubbles:true}));}setTimeout(()=>{if(epiId&&$('#returnEpi')){$('#returnEpi').value=epiId;$('#returnEpi').dispatchEvent(new Event('change',{bubbles:true}));}},100);},120);
    },120);
  }

  function modalBase(id,title,sub=''){
    let d=$('#'+id);if(!d){d=document.createElement('div');d.id=id;d.className='ux-modal';d.innerHTML=`<div class="ux-modal-card"><div class="ux-modal-head"><div><h2></h2><p></p></div><button class="ux-close" type="button">×</button></div><div class="ux-modal-body"></div></div>`;document.body.appendChild(d);d.querySelector('.ux-close').onclick=()=>closeModal(id);d.addEventListener('click',e=>{if(e.target===d)closeModal(id);});}
    d.querySelector('h2').textContent=title;d.querySelector('.ux-modal-head p').textContent=sub;return d;
  }
  function closeModal(id){const d=$('#'+id);if(d)d.classList.remove('open');if(id==='uxQrScanner')stopScanner();}
  function openModal(id){$('#'+id)?.classList.add('open');}

  function roleKey(role){return norm(role).replace(/[^a-z0-9]+/g,'-');}
  function kitForWorker(w){if(!w?.role)return [];const ux=readUx();return Array.isArray(ux.kits[roleKey(w.role)])?ux.kits[roleKey(w.role)]:[];}
  function openKit(workerId){
    const app=readApp(),w=app.workers.find(x=>x.id===workerId);if(!w)return;
    if(!w.role)return toast('Informe o cargo/função do trabalhador para usar kits.');
    const d=modalBase('uxKitModal','Kit de EPI • '+w.role,'Salve os EPIs mais usados nesta função para preencher entregas em um toque.');
    const selected=new Set(kitForWorker(w));
    d.querySelector('.ux-modal-body').innerHTML=`<div class="ux-checklist">${app.epis.filter(e=>e.active!==false).map(e=>`<label class="ux-check"><input type="checkbox" value="${esc(e.id)}" ${selected.has(e.id)?'checked':''}><span><b>${esc(e.name)}</b>${e.ca?' • CA '+esc(e.ca):''}</span></label>`).join('')}</div><div class="ux-modal-actions"><button class="p" id="uxSaveKit">Salvar kit</button><button class="s" id="uxUseKit">Usar na entrega</button></div>`;
    d.querySelector('#uxSaveKit').onclick=()=>{const ux=readUx();ux.kits[roleKey(w.role)]=$$('#uxKitModal input:checked').map(x=>x.value);writeUx(ux);toast('Kit da função salvo neste dispositivo.');closeModal('uxKitModal');};
    d.querySelector('#uxUseKit').onclick=()=>{const ids=$$('#uxKitModal input:checked').map(x=>x.value);if(!ids.length)return toast('Selecione pelo menos um EPI.');closeModal('uxKitModal');prefillDelivery(workerId,ids,'Primeira entrega');};
    openModal('uxKitModal');
  }

  async function loadQrLib(){
    if(window.QRCode)return true;
    if(!navigator.onLine)return false;
    return new Promise(resolve=>{
      const existing=$('script[data-ux-qrcode]');if(existing){existing.addEventListener('load',()=>resolve(!!window.QRCode),{once:true});existing.addEventListener('error',()=>resolve(false),{once:true});return;}
      const s=document.createElement('script');s.dataset.uxQrcode='1';s.src='https://cdn.jsdelivr.net/gh/davidshimjs/qrcodejs/qrcode.min.js';s.onload=()=>resolve(!!window.QRCode);s.onerror=()=>resolve(false);document.head.appendChild(s);
    });
  }
  async function openQr(workerId){
    const app=readApp(),w=app.workers.find(x=>x.id===workerId);if(!w)return;
    const d=modalBase('uxQrModal','QR do trabalhador',w.name||'Trabalhador');
    const code='GEPI|'+workerId;
    d.querySelector('.ux-modal-body').innerHTML=`<div id="uxQrBox" class="ux-qrbox"><div class="spinner">Gerando…</div></div><div class="ux-qr-code">${esc(code)}</div><p style="font-size:10px;color:#6c817d">O QR contém apenas um identificador interno, sem CPF ou nome.</p><div class="ux-modal-actions"><button class="s" id="uxQrPrint">Imprimir cartão</button></div>`;
    openModal('uxQrModal');
    const ok=await loadQrLib(),box=$('#uxQrBox');if(!box)return;
    box.innerHTML='';
    if(ok){new window.QRCode(box,{text:code,width:190,height:190,colorDark:'#173b47',colorLight:'#ffffff',correctLevel:window.QRCode.CorrectLevel.H});}
    else box.innerHTML='<div class="empty">Para gerar o QR pela primeira vez, conecte este aparelho à internet. O código rápido abaixo continua disponível.</div>';
    $('#uxQrPrint').onclick=()=>window.print();
  }

  async function openScanner(){
    const d=modalBase('uxQrScanner','Ler QR do trabalhador','Aponte a câmera para o QR gerado pelo Gestão EPI.');
    d.querySelector('.ux-modal-body').innerHTML='<video id="uxScannerVideo" class="ux-scanner-video" playsinline muted></video><div style="margin-top:10px"><input id="uxManualCode" placeholder="Ou cole o código GEPI|..." style="width:100%;height:46px;border:1px solid #d8e6e2;border-radius:10px;padding:0 10px"><button id="uxManualOpen" class="ux-more" type="button">Abrir código</button></div><div id="uxScannerMsg" style="font-size:10px;color:#6c817d;margin-top:8px"></div>';
    openModal('uxQrScanner');
    $('#uxManualOpen').onclick=()=>handleQrValue($('#uxManualCode').value);
    if(!('BarcodeDetector' in window)){
      $('#uxScannerMsg').textContent='Leitura automática não disponível neste aparelho. Use o código rápido ou a busca.';
      return;
    }
    try{
      const formats=await window.BarcodeDetector.getSupportedFormats();if(!formats.includes('qr_code'))throw new Error('QR não suportado');
      const detector=new window.BarcodeDetector({formats:['qr_code']});
      qrStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
      const video=$('#uxScannerVideo');video.srcObject=qrStream;await video.play();
      const scan=async()=>{if(!qrStream)return;try{const found=await detector.detect(video);if(found?.[0]?.rawValue){handleQrValue(found[0].rawValue);return;}}catch(_){}
        qrLoop=requestAnimationFrame(scan);};
      qrLoop=requestAnimationFrame(scan);
    }catch(_){$('#uxScannerMsg').textContent='Não foi possível iniciar a leitura automática. Use o código rápido ou a busca.';}
  }
  function stopScanner(){if(qrLoop)cancelAnimationFrame(qrLoop);qrLoop=0;if(qrStream){qrStream.getTracks().forEach(t=>t.stop());qrStream=null;}}
  function handleQrValue(value){
    const raw=String(value||'').trim(),id=raw.startsWith('GEPI|')?raw.slice(5):raw;
    const w=readApp().workers.find(x=>x.id===id);if(!w)return toast('QR/código não corresponde a um trabalhador deste aparelho.');
    stopScanner();closeModal('uxQrScanner');renderWorker360(w.id);
  }

  async function sharePortal(workerId){
    const app=readApp(),w=app.workers.find(x=>x.id===workerId);if(!w)return;
    const auth=window.GestaoEpiAuth;if(!auth?.api)return toast('Entre no sistema para gerar o portal.');
    if(!navigator.onLine)return toast('O Portal do Trabalhador precisa de internet para gerar um novo link.');
    try{
      const r=await auth.api('tenant_worker_portal_link',{workerId,days:90});if(!r?.ok||!r.url)throw new Error(r?.message||'Falha ao gerar portal.');
      if(navigator.share){try{await navigator.share({title:'Portal do Trabalhador • Gestão EPI',text:`Olá, ${w.name}. Consulte seus EPIs e comprovantes.`,url:r.url});return;}catch(e){if(e?.name==='AbortError')return;}}
      await navigator.clipboard.writeText(r.url);toast('Link do portal copiado.');
    }catch(e){toast(e?.message||'Falha ao gerar portal.');}
  }

  function showSuccess(d){
    const app=readApp(),w=app.workers.find(x=>x.id===d.workerId)||{},items=(d.items||[]).map(i=>{const e=epi(app,i.epiId);return `${e.name||'EPI'} × ${Number(i.qty||0)}`;}).join(' • ');
    const modal=modalBase('uxSuccessModal','Entrega registrada','');
    modal.querySelector('.ux-modal-body').innerHTML=`<div class="ux-success"><div class="ux-success-icon">✓</div><h2>Entrega concluída</h2><p><b>${esc(w.name||'Trabalhador')}</b><br>${esc(items)}<br>${fmt(d.createdAt,true)}</p></div><div class="ux-modal-actions" style="justify-content:center"><button class="p" id="uxNextWorker">Próximo trabalhador</button><button class="s" id="uxViewHistory">Ver histórico</button></div>`;
    $('#uxNextWorker').onclick=()=>{closeModal('uxSuccessModal');nav('delivery');setTimeout(()=>{$('#deliveryWorkerSearch')?.focus();},120);};
    $('#uxViewHistory').onclick=()=>{closeModal('uxSuccessModal');nav('history');};
    openModal('uxSuccessModal');
  }

  function watchNewDelivery(){
    const rows=readApp().deliveries||[];
    if(!lastDeliveryId){lastDeliveryId=rows[0]?.id||'';return;}
    const latest=rows[0];if(!latest||latest.id===lastDeliveryId)return;
    lastDeliveryId=latest.id;
    if(Date.now()-(new Date(latest.createdAt||0).getTime())<15000)showSuccess(latest);
  }

  function bindActions(){
    document.addEventListener('click',e=>{
      const a=e.target.closest('[data-ux-action]');
      if(a){
        const v=a.dataset.uxAction;
        if((v==='delivery'||v==='replace')&&!canOperate())return toast('Seu perfil é somente consulta.');
        if(v==='delivery')nav('delivery');else if(v==='scan')openScanner();else if(v==='workers')nav('workers');else if(v==='replace')nav('epiReplacements');else if(v==='stock')nav('stock');
        return;
      }
      const search=e.target.closest('[data-ux-search]');if(search){
        const [type,id]=search.dataset.uxSearch.split('|');$('#uxGlobalSearchResults')?.classList.remove('open');
        if(type==='worker')renderWorker360(id);else if(type==='epi')nav('epis');else if(type==='company')nav('companies');return;
      }
      const w=e.target.closest('[data-worker-360]');if(w){renderWorker360(w.dataset.worker360);return;}
      const fav=e.target.closest('[data-ux-fav]');if(fav){toggleFavorite(fav.dataset.uxFav);return;}
      const deliver=e.target.closest('[data-ux-deliver]');if(deliver){if(!canOperate())return toast('Seu perfil é somente consulta.');const app=readApp(),wk=app.workers.find(x=>x.id===deliver.dataset.uxDeliver);const kit=kitForWorker(wk);prefillDelivery(wk.id,kit,kit.length?'Primeira entrega':'');return;}
      const kit=e.target.closest('[data-ux-kit]');if(kit){if(!canOperate())return toast('Seu perfil é somente consulta.');openKit(kit.dataset.uxKit);return;}
      const ret=e.target.closest('[data-ux-return]');if(ret){if(!canOperate())return toast('Seu perfil é somente consulta.');prefillReturn(ret.dataset.uxReturn);return;}
      const qr=e.target.closest('[data-ux-qr]');if(qr){openQr(qr.dataset.uxQr);return;}
      const portal=e.target.closest('[data-ux-portal]');if(portal){if(!canOperate())return toast('Seu perfil é somente consulta.');sharePortal(portal.dataset.uxPortal);return;}
      const sw=e.target.closest('[data-ux-swap]');if(sw){if(!canOperate())return toast('Seu perfil é somente consulta.');const [wid,eid]=sw.dataset.uxSwap.split('|');quickSwap(wid,eid);return;}
      const re=e.target.closest('[data-ux-return-epi]');if(re){if(!canOperate())return toast('Seu perfil é somente consulta.');const [wid,eid]=re.dataset.uxReturnEpi.split('|');prefillReturn(wid,eid);return;}
    },true);
    document.addEventListener('click',e=>{if(!e.target.closest('#uxGlobalSearch'))$('#uxGlobalSearchResults')?.classList.remove('open');});
    window.addEventListener('online',onlinePill);window.addEventListener('offline',onlinePill);
    document.addEventListener('auditar-epi-data-changed',()=>setTimeout(()=>{decorate();watchNewDelivery();},90));
    document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(()=>{improveLogin();onlinePill();decorate();lastDeliveryId=readApp().deliveries?.[0]?.id||'';},100));
    setInterval(watchNewDelivery,700);
  }

  function decorate(){
    clearTimeout(decorateTimer);decorateTimer=0;
    applyBrand();improveLogin();injectHome();injectWorker360();decorateWorkers();onlinePill();
  }
  function queue(){if(decorateTimer)return;decorateTimer=setTimeout(decorate,60);}

  function boot(){
    injectStyles();decorate();bindActions();lastDeliveryId=readApp().deliveries?.[0]?.id||'';
    observer=new MutationObserver(queue);observer.observe(document.body,{childList:true,subtree:true});
    [200,700,1600,3500].forEach(ms=>setTimeout(queue,ms));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();