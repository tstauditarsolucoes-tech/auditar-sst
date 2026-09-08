(() => {
  'use strict';
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;

  function readApp(){try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')};}catch{return {companies:[],workers:[],epis:[],deliveries:[]};}}
  function writeApp(root){localStorage.setItem(APP_KEY,JSON.stringify(root));afterDataChange();}
  function readStock(){try{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{},...JSON.parse(localStorage.getItem(STOCK_KEY)||'{}')};}catch{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}};}}
  function writeStock(stock){localStorage.setItem(STOCK_KEY,JSON.stringify(stock));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed'));}
  function afterDataChange(){
    try{window.GestaoEpiReloadFromStorage?.();}catch(_){ }
    document.dispatchEvent(new CustomEvent('auditar-epi-data-changed'));
    document.dispatchEvent(new CustomEvent('auditar-epi-state-refreshed'));
  }
  function toast(msg){const el=$('#toast');if(!el)return;el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2400);}

  function injectStyles(){
    if($('#mobileField310Style'))return;
    const s=document.createElement('style');s.id='mobileField310Style';s.textContent=`
      :root{--v31nav:76px}
      html{scroll-behavior:auto!important}
      body{padding-bottom:calc(var(--v31nav) + env(safe-area-inset-bottom,0px))!important}
      .topbar{padding-top:max(10px,env(safe-area-inset-top,0px))!important}
      .app-shell{padding-bottom:calc(110px + env(safe-area-inset-bottom,0px))!important}
      .view-head{scroll-margin-top:80px}
      #v3BottomNav{height:calc(var(--v31nav) + env(safe-area-inset-bottom,0px))!important;padding-bottom:env(safe-area-inset-bottom,0px)!important}
      #v3BottomNav button{min-width:0!important;padding:7px 3px 8px!important;font-size:11px!important}
      #v3BottomNav button span{font-size:23px!important;line-height:1!important}
      .v3-more-grid,.menu-grid{gap:9px!important}
      .v3-more-grid .menu-card,#moreV3 .menu-card{min-height:104px!important;padding:13px!important;border-radius:17px!important}
      .v3-more-grid .menu-card span,#moreV3 .menu-card span{font-size:25px!important;margin-bottom:6px!important}
      .v3-more-grid .menu-card b,#moreV3 .menu-card b{font-size:15px!important;line-height:1.12!important}
      .v3-more-grid .menu-card small,#moreV3 .menu-card small{font-size:11px!important;line-height:1.25!important;margin-top:4px!important}
      #moreV3 .view-head{margin-bottom:11px!important}
      #moreV3 .view-head h2{font-size:23px!important}
      .v31-field-title{margin:3px 0 9px;font-size:11px;font-weight:950;letter-spacing:.06em;color:#607a76;text-transform:uppercase}
      .v31-quick-box{margin-top:10px;padding:11px;border:1px solid #cfe4e0;border-radius:15px;background:#f4fbf9}
      .v31-quick-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}
      .v31-quick-head b{font-size:13px;color:#244c48}.v31-quick-head small{font-size:10px;color:#6c817e}
      .v31-quick-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}
      .v31-quick-actions button{min-height:48px;border:1px solid #bcdad5;border-radius:12px;background:#fff;color:#0f766e;font-weight:900;font-size:12px;padding:7px}
      .v31-quick-actions button:active{background:#e8f8f5}
      .v31-modal{position:fixed;inset:0;z-index:40000;display:none;align-items:flex-end;justify-content:center;background:rgba(7,30,27,.68);padding:0}
      .v31-modal.open{display:flex}
      .v31-sheet{width:100%;max-width:620px;max-height:92vh;overflow:auto;background:#fff;border-radius:24px 24px 0 0;padding:18px 16px calc(18px + env(safe-area-inset-bottom,0px));box-shadow:0 -18px 60px rgba(0,0,0,.2)}
      .v31-sheet-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:13px}
      .v31-sheet-head h2{font-size:20px;margin:0;color:#173d39}.v31-sheet-head p{font-size:11px;color:#6a7f7c;margin:3px 0 0}
      .v31-close{border:0;background:#eef7f5;color:#0f766e;width:40px;height:40px;border-radius:12px;font-size:22px;font-weight:900}
      .v31-form{display:grid;gap:10px}.v31-form label{display:grid;gap:5px;font-size:11px;font-weight:850;color:#4c6763}
      .v31-form input,.v31-form select{min-height:48px;border:1px solid #cbdad8;border-radius:12px;padding:10px 12px;font-size:15px;background:#fff}
      .v31-two{display:grid;grid-template-columns:1fr 1fr;gap:9px}.v31-save{width:100%;min-height:54px;margin-top:4px;border:0;border-radius:14px;background:#0f766e;color:#fff;font-weight:950;font-size:15px}
      .v31-note{font-size:10px;color:#6c817e;line-height:1.4;background:#f6f9f9;border-radius:10px;padding:9px}
      #delivery .worker-search-box{padding:11px;border-radius:14px;background:#f8fbfb;border:1px solid #e1ecea}
      #delivery .card{padding:14px!important}
      #delivery .view-head{margin-bottom:10px!important}
      #delivery .view-head h2{font-size:23px!important}
      #delivery .view-head p{font-size:11px!important}
      #delivery .delivery-item{padding:9px!important;gap:7px!important}
      #delivery #btnSaveDelivery{position:sticky;z-index:35;bottom:calc(var(--v31nav) + 8px + env(safe-area-inset-bottom,0px));box-shadow:0 8px 28px rgba(15,118,110,.32);border:2px solid #fff;margin-top:12px!important}
      .v31-shortcuts{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:0 0 11px}
      .v31-shortcuts button{min-height:44px;border:0;border-radius:12px;background:#e8f8f5;color:#0f766e;font-weight:900;font-size:12px}
      @media(max-width:520px){
        .app-shell{padding-left:10px!important;padding-right:10px!important;padding-top:12px!important}
        #home .menu-card{min-height:100px!important;padding:13px!important}.menu-card span{font-size:25px!important;margin-bottom:6px!important}.menu-card b{font-size:15px!important}.menu-card small{font-size:11px!important}
        #home .hero-card{padding:17px!important;border-radius:20px!important;gap:14px!important}#home .hero-card h1{font-size:20px!important}
        .stats-grid{margin:10px 0!important}.stat{padding:10px 5px!important}.stat strong{font-size:19px!important}
        .v31-two{grid-template-columns:1fr}.v31-sheet{max-height:94vh}.v31-quick-actions{grid-template-columns:1fr 1fr}
      }
      @media(max-width:370px){.v31-quick-actions,.v31-shortcuts{grid-template-columns:1fr}.v3-more-grid,.menu-grid{grid-template-columns:1fr!important}}
    `;document.head.appendChild(s);
  }

  function fixVersionAndLabels(){
    const v=$('#v3VersionLabel');if(v)v.textContent='Gestão EPI Mobile v3.1';
    const eye=$('#home .eyebrow');if(eye)eye.textContent='GESTÃO EPI • MOBILE 3.1';
    const more=$('#moreV3 .view-head p');if(more)more.textContent='Funções organizadas para uso rápido no campo.';
  }

  function fixNavigationScroll(){
    if(document.documentElement.dataset.v31ScrollFix==='1')return;
    document.documentElement.dataset.v31ScrollFix='1';
    document.addEventListener('click',e=>{
      const b=e.target.closest('[data-go]');if(!b)return;
      setTimeout(()=>{try{window.scrollTo({top:0,left:0,behavior:'auto'});document.documentElement.scrollTop=0;document.body.scrollTop=0;}catch(_){ }},0);
    },true);
  }

  function modalShell(id,title,desc,formHtml){
    let d=$('#'+id);if(d)return d;
    d=document.createElement('div');d.id=id;d.className='v31-modal';d.innerHTML=`<div class="v31-sheet"><div class="v31-sheet-head"><div><h2>${title}</h2><p>${desc}</p></div><button class="v31-close" type="button" aria-label="Fechar">×</button></div>${formHtml}</div>`;
    document.body.appendChild(d);
    d.querySelector('.v31-close').onclick=()=>d.classList.remove('open');
    d.addEventListener('click',e=>{if(e.target===d)d.classList.remove('open');});
    return d;
  }

  function companyOptions(selected=''){
    const app=readApp();return (app.companies||[]).map(c=>`<option value="${esc(c.id)}" ${c.id===selected?'selected':''}>${esc(c.name)}</option>`).join('');
  }

  function openWorkerQuick(){
    const companyId=$('#deliveryCompany')?.value||'';
    if(!companyId)return toast('Selecione a empresa da entrega primeiro.');
    const d=modalShell('v31WorkerModal','Cadastrar trabalhador','Cadastre sem sair da entrega.',`<form id="v31WorkerForm" class="v31-form"><label>Empresa<select id="v31WorkerCompany" required>${companyOptions(companyId)}</select></label><label>Nome completo<input id="v31WorkerName" required autocomplete="name" placeholder="Nome do colaborador"></label><div class="v31-two"><label>CPF<input id="v31WorkerCpf" inputmode="numeric" placeholder="000.000.000-00"></label><label>Matrícula<input id="v31WorkerReg" placeholder="Opcional"></label></div><div class="v31-two"><label>Cargo<input id="v31WorkerRole" placeholder="Ex.: Servente"></label><label>Setor<input id="v31WorkerSector" placeholder="Ex.: Produção"></label></div><div class="v31-note">Depois de salvar, o trabalhador ficará selecionado automaticamente nesta entrega.</div><button class="v31-save" type="submit">✓ Salvar e usar na entrega</button></form>`);
    $('#v31WorkerCompany').innerHTML=companyOptions(companyId);$('#v31WorkerCompany').value=companyId;
    $('#v31WorkerName').value='';$('#v31WorkerCpf').value='';$('#v31WorkerReg').value='';$('#v31WorkerRole').value='';$('#v31WorkerSector').value='';
    d.classList.add('open');setTimeout(()=>$('#v31WorkerName')?.focus(),100);
    const f=$('#v31WorkerForm');if(f&&!f.dataset.bound){f.dataset.bound='1';f.addEventListener('submit',saveWorkerQuick);}
  }

  function saveWorkerQuick(e){
    e.preventDefault();const name=$('#v31WorkerName')?.value.trim()||'',companyId=$('#v31WorkerCompany')?.value||'';
    if(!companyId)return toast('Selecione a empresa.');if(!name)return toast('Informe o nome do trabalhador.');
    const app=readApp();const id=uid('w');
    app.workers.push({id,companyId,name,cpf:$('#v31WorkerCpf')?.value.trim()||'',reg:$('#v31WorkerReg')?.value.trim()||'',role:$('#v31WorkerRole')?.value.trim()||'',sector:$('#v31WorkerSector')?.value.trim()||'',active:true,createdAt:new Date().toISOString()});
    writeApp(app);$('#v31WorkerModal')?.classList.remove('open');
    setTimeout(()=>{const c=$('#deliveryCompany');if(c){c.value=companyId;c.dispatchEvent(new Event('change',{bubbles:true}));}setTimeout(()=>{const w=$('#deliveryWorker');if(w){w.value=id;w.dispatchEvent(new Event('change',{bubbles:true}));w.scrollIntoView({block:'center'});}toast('Trabalhador cadastrado e selecionado.');},70);},50);
  }

  function openEpiQuick(){
    const companyId=$('#deliveryCompany')?.value||'';
    if(!companyId)return toast('Selecione a empresa da entrega primeiro.');
    const d=modalShell('v31EpiModal','Cadastrar EPI','Cadastre o equipamento e continue a entrega.',`<form id="v31EpiForm" class="v31-form"><label>EPI<input id="v31EpiName" required placeholder="Ex.: Óculos de segurança"></label><div class="v31-two"><label>CA<input id="v31EpiCa" inputmode="numeric" placeholder="Número do CA"></label><label>Tamanho<input id="v31EpiSize" placeholder="Opcional"></label></div><label>Fabricante / modelo<input id="v31EpiModel" placeholder="Opcional"></label><div class="v31-two"><label>Troca prevista (dias)<input id="v31EpiCycle" type="number" min="0" inputmode="numeric" placeholder="Ex.: 180"></label><label>Saldo inicial nesta empresa<input id="v31EpiStock" type="number" min="0" inputmode="numeric" placeholder="Opcional"></label></div><div class="v31-note">Se informar saldo inicial, o estoque já será criado. O EPI ficará selecionado na entrega ao salvar.</div><button class="v31-save" type="submit">✓ Salvar e usar na entrega</button></form>`);
    ['v31EpiName','v31EpiCa','v31EpiSize','v31EpiModel','v31EpiCycle','v31EpiStock'].forEach(id=>{const el=$('#'+id);if(el)el.value='';});
    d.classList.add('open');setTimeout(()=>$('#v31EpiName')?.focus(),100);
    const f=$('#v31EpiForm');if(f&&!f.dataset.bound){f.dataset.bound='1';f.addEventListener('submit',saveEpiQuick);}
  }

  function saveEpiQuick(e){
    e.preventDefault();const name=$('#v31EpiName')?.value.trim()||'',companyId=$('#deliveryCompany')?.value||'';
    if(!name)return toast('Informe o nome do EPI.');if(!companyId)return toast('Selecione a empresa da entrega.');
    const app=readApp(),id=uid('e');
    app.epis.push({id,name,ca:$('#v31EpiCa')?.value.trim()||'',model:$('#v31EpiModel')?.value.trim()||'',size:$('#v31EpiSize')?.value.trim()||'',cycle:Math.max(0,Number($('#v31EpiCycle')?.value||0)),createdAt:new Date().toISOString()});
    localStorage.setItem(APP_KEY,JSON.stringify(app));
    const initial=Math.max(0,Number($('#v31EpiStock')?.value||0));
    if(initial>0){const stock=readStock(),key=`${companyId}::${id}`;stock.minimums[key]=5;stock.movements.unshift({id:uid('sm'),type:'SET',delta:initial,companyId,epiId:id,note:'Saldo inicial no cadastro rápido',createdAt:new Date().toISOString()});writeStock(stock);}
    afterDataChange();$('#v31EpiModal')?.classList.remove('open');
    setTimeout(()=>{
      let rows=$$('.delivery-item');let row=rows.find(r=>!r.querySelector('.item-epi')?.value);
      if(!row){$('#btnAddItem')?.click();rows=$$('.delivery-item');row=rows[rows.length-1];}
      setTimeout(()=>{const sel=row?.querySelector('.item-epi');if(sel){sel.value=id;sel.dispatchEvent(new Event('change',{bubbles:true}));sel.scrollIntoView({block:'center'});}toast('EPI cadastrado e adicionado à entrega.');},80);
    },80);
  }

  function injectDeliveryQuick(){
    const delivery=$('#delivery');if(!delivery)return;
    const workerBox=$('#delivery .worker-search-box');
    if(workerBox&&!$('#v31QuickBox')){const q=document.createElement('div');q.id='v31QuickBox';q.className='v31-quick-box';q.innerHTML='<div class="v31-quick-head"><b>Cadastro rápido</b><small>sem sair da entrega</small></div><div class="v31-quick-actions"><button id="v31AddWorker" type="button">＋ Trabalhador</button><button id="v31AddEpi" type="button">＋ EPI</button></div>';workerBox.appendChild(q);$('#v31AddWorker').onclick=openWorkerQuick;$('#v31AddEpi').onclick=openEpiQuick;}
    const items=$('#deliveryItems')?.closest('.card');
    if(items&&!$('#v31DeliveryShortcuts')){const r=document.createElement('div');r.id='v31DeliveryShortcuts';r.className='v31-shortcuts';r.innerHTML='<button id="v31QuickEpiTop" type="button">＋ Novo EPI agora</button><button id="v31GoStock" type="button">📦 Ver estoque</button>';items.insertBefore(r,items.firstChild);$('#v31QuickEpiTop').onclick=openEpiQuick;$('#v31GoStock').onclick=()=>document.querySelector('[data-go="stock"]')?.click();}
  }

  function groupMoreScreen(){
    const grid=$('#moreV3 .v3-more-grid');if(!grid||grid.dataset.v31Grouped==='1')return;grid.dataset.v31Grouped='1';
    const parent=grid.parentNode;const t1=document.createElement('div');t1.className='v31-field-title';t1.textContent='Uso no campo';parent.insertBefore(t1,grid);
    // Ordem prática: operação primeiro, cadastros depois.
    const order=['returnsField','holdingsField','stock','history','alertsV3','sectorsV3','workers','importWorkers','epis','companies'];
    order.forEach(go=>{const b=grid.querySelector(`[data-go="${go}"]`);if(b)grid.appendChild(b);});
    const cad=grid.querySelector('[data-go="workers"]');if(cad){const t2=document.createElement('div');t2.className='v31-field-title';t2.textContent='Cadastros e organização';grid.parentNode.insertBefore(t2,grid); /* título geral visual; ordem já priorizada */}
  }

  function fixDuplicateQuickWorker(){
    // O módulo antigo pode inserir um botão de cadastro. Mantemos apenas a versão compacta v3.1.
    const old=$('#btnQuickWorker')||$('.quick-worker-btn');if(old&&old.id!=='v31AddWorker')old.style.display='none';
  }

  function boot(){
    injectStyles();fixVersionAndLabels();fixNavigationScroll();injectDeliveryQuick();groupMoreScreen();fixDuplicateQuickWorker();
    window.addEventListener('online',()=>setTimeout(injectDeliveryQuick,50));
    document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(()=>{injectDeliveryQuick();fixDuplicateQuickWorker();},120));
    document.addEventListener('auditar-epi-state-refreshed',()=>setTimeout(injectDeliveryQuick,80));
    const obs=new MutationObserver(()=>{injectDeliveryQuick();fixVersionAndLabels();fixDuplicateQuickWorker();});obs.observe(document.body,{childList:true,subtree:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
