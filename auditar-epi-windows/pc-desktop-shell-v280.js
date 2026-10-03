(()=>{
  const VERSION='PC v2.8.1';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];

  const GROUPS=[
    {title:'OPERAÇÃO',ids:['dashboard','fastDeliveryPc','newDeliveryPc','batchDeliveryPc','employeeSheetsPc','receiptsPc','workers','deliveries']},
    {title:'ESTOQUE',ids:['stock','inventoryPc','purchasesPc','nfImportPc','returnsPc','replacementPc']},
    {title:'CADASTROS',ids:['epis','caSmartPc','rolePpePc','importWorkersPc','qrPeoplePc','faceEnrollPc','externalsPc']},
    {title:'GESTÃO E CONTROLE',ids:['alertsPc','managerReportsPc','indicators','inspectionPc','inspectionDossierPc','dataQualityPc','dataSafetyPc','auditPc','companies','pending']}
  ];

  function installStyles(){
    if($('#pcDesktopV280Styles')) return;
    const s=document.createElement('style');
    s.id='pcDesktopV280Styles';
    s.textContent=`
      @media (min-width:1000px){
        html,body{height:100%;overflow:hidden!important;background:#eef3f2!important}
        body.pc-desktop-v280{font-size:13px}
        .layout{
          display:grid!important;
          grid-template-columns:288px minmax(0,1fr)!important;
          width:100vw!important;
          height:100vh!important;
          min-height:0!important;
          overflow:hidden!important;
          background:#eef3f2!important
        }
        .sidebar{
          position:relative!important;
          inset:auto!important;
          width:288px!important;
          min-width:288px!important;
          max-width:288px!important;
          height:100vh!important;
          min-height:0!important;
          padding:18px 12px 14px!important;
          overflow:hidden!important;
          display:flex!important;
          flex-direction:column!important;
          background:linear-gradient(180deg,#1f3032 0%,#172729 100%)!important;
          border-right:1px solid rgba(255,255,255,.05)!important;
          box-shadow:10px 0 32px rgba(18,38,39,.08)!important
        }
        .sidebar-brand{
          flex:0 0 auto!important;
          padding:2px 10px 16px!important;
          margin:0 0 5px!important;
          border-bottom:1px solid rgba(255,255,255,.08)!important
        }
        .sidebar-brand .logo{font-size:17px!important;line-height:1.15!important}
        .sidebar-brand .logo::before{width:42px!important;height:42px!important;flex-basis:42px!important}
        .sidebar-brand small{margin-left:52px!important;font-size:8px!important;letter-spacing:.18em!important}
        .sidebar nav{
          flex:1 1 auto!important;
          min-height:0!important;
          overflow-y:auto!important;
          overflow-x:hidden!important;
          display:block!important;
          padding:4px 4px 18px!important;
          scrollbar-width:thin!important
        }
        .sidebar nav::-webkit-scrollbar{width:5px}
        .sidebar nav::-webkit-scrollbar-thumb{background:rgba(255,255,255,.14);border-radius:10px}
        .pc280-nav-group{
          padding:14px 10px 5px!important;
          color:#8fa5a4!important;
          font-size:8px!important;
          font-weight:900!important;
          letter-spacing:.14em!important;
          text-transform:uppercase!important;
          user-select:none!important
        }
        .pc280-nav-group:first-child{padding-top:7px!important}
        .sidebar .nav{
          width:100%!important;
          min-height:38px!important;
          margin:1px 0!important;
          padding:8px 10px!important;
          display:flex!important;
          align-items:center!important;
          justify-content:flex-start!important;
          gap:9px!important;
          border-radius:9px!important;
          font-size:14px!important;
          font-weight:650!important;
          color:#c8d7d5!important;
          background:transparent!important;
          transition:background .12s ease,color .12s ease,transform .12s ease!important
        }
        .sidebar .nav span{display:inline!important;font-size:11.5px!important;line-height:1.2!important}
        .sidebar .nav:hover{background:rgba(255,255,255,.07)!important;color:#fff!important}
        .sidebar .nav.active{
          background:#eff8f6!important;
          color:#0e6d63!important;
          box-shadow:inset 3px 0 0 #18a58f!important;
          font-weight:850!important
        }
        .sidebar .nav.active span{color:#0e6d63!important}
        .sidebar-foot{
          flex:0 0 auto!important;
          margin-top:0!important;
          padding:12px 9px 3px!important;
          border-top:1px solid rgba(255,255,255,.09)!important
        }
        .sidebar-foot b{font-size:10.5px!important}
        .sidebar-foot small{font-size:9px!important}
        .pc280-user{
          flex:0 0 auto;
          display:grid;
          grid-template-columns:30px minmax(0,1fr);
          gap:9px;
          align-items:center;
          margin:8px 4px 2px;
          padding:9px;
          border:1px solid rgba(255,255,255,.08);
          border-radius:10px;
          background:rgba(255,255,255,.035)
        }
        .pc280-user-avatar{
          width:30px;height:30px;border-radius:9px;display:grid;place-items:center;
          background:#284344;color:#8fe0d4;font-weight:900;font-size:12px
        }
        .pc280-user b{display:block;color:#edf7f5;font-size:10.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .pc280-user small{display:block;color:#8fa5a4;font-size:8.5px;margin-top:2px;text-transform:uppercase;letter-spacing:.06em}

        .main{
          position:relative!important;
          width:auto!important;
          min-width:0!important;
          height:100vh!important;
          min-height:0!important;
          margin:0!important;
          padding:0!important;
          overflow-y:auto!important;
          overflow-x:hidden!important;
          background:#f4f7f7!important
        }
        .topbar{
          position:sticky!important;
          top:0!important;
          z-index:100!important;
          min-height:78px!important;
          margin:0!important;
          padding:16px 28px 14px!important;
          display:flex!important;
          align-items:center!important;
          justify-content:space-between!important;
          gap:20px!important;
          background:rgba(244,247,247,.97)!important;
          border-bottom:1px solid #dce7e5!important;
          backdrop-filter:blur(14px)!important
        }
        .topbar>div:first-child{min-width:0}
        .topbar h1{font-size:22px!important;line-height:1.15!important;letter-spacing:-.02em!important}
        .topbar p{font-size:10.5px!important;margin-top:4px!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}
        .top-actions{display:flex!important;align-items:end!important;gap:8px!important;flex:0 0 auto!important}
        .company-filter{min-width:220px!important;font-size:8.5px!important;text-transform:uppercase!important;letter-spacing:.05em!important}
        .company-filter select{width:100%!important;min-height:38px!important}
        #btnRefresh{min-height:38px!important}

        .view{
          display:none;
          width:100%!important;
          max-width:none!important;
          margin:0!important;
          padding:22px 28px 38px!important
        }
        .view.active{display:block!important}
        .split-head,.pc-modern-head,.v260-head,.v272-head{
          margin-bottom:14px!important;
          align-items:flex-start!important
        }
        .split-head h2,.pc-modern-head h2,.v260-head h2,.v272-head h2{font-size:18px!important}
        .split-head p,.pc-modern-head p,.v260-head p,.v272-head p{font-size:10.5px!important;max-width:760px!important}
        .cards{gap:10px!important;margin-bottom:14px!important}
        .cards.four{grid-template-columns:repeat(4,minmax(0,1fr))!important}
        .cards.three{grid-template-columns:repeat(3,minmax(0,1fr))!important}
        .metric{
          min-height:105px!important;
          padding:14px 15px!important;
          border-radius:12px!important;
          border:1px solid #dde8e6!important;
          box-shadow:0 3px 12px rgba(22,61,56,.035)!important
        }
        .metric span{font-size:10px!important}
        .metric strong{font-size:27px!important;margin:5px 0 1px!important;letter-spacing:-.03em!important}
        .metric.text strong{font-size:16px!important;line-height:1.25!important}
        .metric small{font-size:9px!important}

        .grid-2{grid-template-columns:minmax(0,1.35fr) minmax(360px,.65fr)!important;gap:12px!important}
        .panel,.pc-card,.v260-card,.v25c,.v270-card,.v272-card{
          border-radius:12px!important;
          border:1px solid #dde8e6!important;
          box-shadow:0 3px 14px rgba(22,61,56,.035)!important;
          padding:14px!important
        }
        .panel-head{margin-bottom:9px!important}
        .panel-head h2{font-size:14px!important}
        .panel-head p{font-size:9.5px!important}
        .filters{margin-bottom:10px!important}
        .filters input{width:min(620px,100%)!important;min-height:38px!important}
        .table-wrap,.pc-preview{border:1px solid #edf2f1!important;border-radius:9px!important;overflow:auto!important}
        .data-table,.v260-table,.v25t,.v270-table,.v272-table,.worker-sheet-table,.pc-preview table{
          width:100%!important;
          border-collapse:separate!important;
          border-spacing:0!important;
          font-size:10.5px!important
        }
        .data-table th,.v260-table th,.v25t th,.v270-table th,.v272-table th,.worker-sheet-table th,.pc-preview th{
          position:sticky!important;
          top:0!important;
          z-index:2!important;
          padding:8px 9px!important;
          background:#f2f6f5!important;
          color:#60736f!important;
          font-size:8.5px!important;
          letter-spacing:.045em!important;
          border-bottom:1px solid #dfe9e7!important
        }
        .data-table td,.v260-table td,.v25t td,.v270-table td,.v272-table td,.worker-sheet-table td,.pc-preview td{
          padding:8px 9px!important;
          vertical-align:middle!important;
          border-bottom:1px solid #edf2f1!important
        }
        .data-table tbody tr:hover td,.v260-table tbody tr:hover td,.v270-table tbody tr:hover td,.v272-table tbody tr:hover td{background:#f9fbfb!important}
        .primary,.secondary,.link,.v260-btn,.v25btn,.v270-btn,.v272-open,.worker-sheet-btn{
          min-height:36px!important;
          border-radius:9px!important;
          font-size:10.5px!important;
          padding:8px 11px!important
        }

        .v260-home{margin:0 0 14px!important}
        .v260-home>h2{font-size:15px!important;margin:0 0 8px!important}
        .v260-home>h2::after{display:none!important}
        .v260-home-grid{
          grid-template-columns:repeat(5,minmax(0,1fr))!important;
          gap:8px!important
        }
        .v260-home-grid button{
          min-height:74px!important;
          padding:10px 11px!important;
          border-radius:10px!important;
          display:grid!important;
          grid-template-columns:auto minmax(0,1fr)!important;
          grid-template-rows:auto auto!important;
          column-gap:8px!important;
          align-content:center!important
        }
        .v260-home-grid span{grid-row:1/3!important;font-size:20px!important;align-self:center!important}
        .v260-home-grid b{font-size:10.5px!important;margin:0!important}
        .v260-home-grid small{font-size:8.5px!important;margin:2px 0 0!important;line-height:1.25!important}
        .v260-kpis{grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:8px!important}
        .v260-kpi{padding:10px!important;border-radius:10px!important}
        .v260-kpi strong{font-size:19px!important}
        .v260-kpi span{font-size:8.5px!important}
        .v260-profile-top{grid-template-columns:2fr repeat(3,minmax(0,1fr))!important}
        .v260-alert{grid-template-columns:30px minmax(0,1fr) auto!important;padding:10px!important}

        .pc-quick{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:8px!important;margin-bottom:12px!important}
        .pc-quick button{min-height:68px!important;padding:10px 12px!important;border-radius:10px!important}
        .pc-quick button b{font-size:10.5px!important;margin-top:3px!important}
        .pc-quick button small{font-size:8.5px!important}
        .pc-grid{gap:10px!important}
        .pc-card label{font-size:10px!important}
        .pc-card input,.pc-card select,.pc-card textarea{min-height:38px!important;border-radius:9px!important;padding:9px 10px!important}
        .pc-actions{gap:7px!important;margin-top:10px!important}

        dialog{width:min(820px,86vw)!important;max-height:84vh!important;border-radius:14px!important}
        #dynamicForm{padding:18px!important}
        .form-grid{grid-template-columns:1fr 1fr!important;gap:10px!important}
        .form-grid input,.form-grid select{min-height:38px!important}
        .dialog-head h2{font-size:18px!important}

        .pc280-desktop-badge{
          display:inline-flex;align-items:center;gap:6px;
          margin-left:8px;padding:4px 7px;border-radius:999px;
          background:#e7f5f2;color:#0e7468;font-size:8px;font-weight:900;
          vertical-align:middle;letter-spacing:.04em;text-transform:uppercase
        }
        .pc280-command{
          position:relative!important;
          width:min(360px,28vw)!important;
          min-width:230px!important
        }
        .pc280-command input{
          width:100%!important;
          min-height:38px!important;
          padding:9px 36px 9px 34px!important;
          border:1px solid #cfddda!important;
          border-radius:10px!important;
          background:#fff!important;
          color:#203735!important;
          font-size:10.5px!important;
          box-shadow:none!important
        }
        .pc280-command input:focus{
          border-color:#0f8d7e!important;
          box-shadow:0 0 0 3px rgba(15,141,126,.10)!important
        }
        .pc280-command-icon{
          position:absolute!important;left:11px!important;top:50%!important;
          transform:translateY(-50%)!important;color:#71837f!important;
          font-size:13px!important;pointer-events:none!important
        }
        .pc280-command-kbd{
          position:absolute!important;right:8px!important;top:50%!important;
          transform:translateY(-50%)!important;border:1px solid #d8e3e1!important;
          background:#f5f8f7!important;color:#788985!important;border-radius:6px!important;
          padding:2px 5px!important;font-size:7.5px!important;font-weight:800!important;
          pointer-events:none!important
        }
        .pc280-command-results{
          display:none;position:absolute;top:44px;left:0;right:0;z-index:5000;
          max-height:390px;overflow:auto;background:#fff;border:1px solid #d9e4e2;
          border-radius:12px;box-shadow:0 18px 45px rgba(21,52,50,.18);padding:6px
        }
        .pc280-command-results.open{display:block}
        .pc280-search-item{
          width:100%;display:grid;grid-template-columns:28px minmax(0,1fr) auto;
          gap:9px;align-items:center;border:0;background:transparent;text-align:left;
          padding:9px;border-radius:8px;cursor:pointer;color:#263c39
        }
        .pc280-search-item:hover{background:#f1f7f5}
        .pc280-search-ico{
          width:28px;height:28px;border-radius:8px;display:grid;place-items:center;
          background:#edf6f4;font-size:13px
        }
        .pc280-search-item b{display:block;font-size:10.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .pc280-search-item small{display:block;font-size:8.5px;color:#71837f;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .pc280-search-kind{font-size:7.5px;font-weight:900;color:#0f766e;text-transform:uppercase;letter-spacing:.05em}
        .pc280-search-empty{padding:16px;text-align:center;color:#70827e;font-size:9.5px}
        .pc280-shortcuts{
          display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin:0 0 14px
        }
        .pc280-shortcut{
          border:1px solid #d8e5e2;background:#fff;color:#315c57;border-radius:9px;
          min-height:34px;padding:7px 10px;font-size:9.5px;font-weight:850;cursor:pointer
        }
        .pc280-shortcut:hover{border-color:#a9cbc5;background:#f5faf9}
        .pc280-shortcut.primary{background:#0f766e;color:#fff;border-color:#0f766e}
        .pc280-section-title{
          display:flex;align-items:center;justify-content:space-between;gap:12px;
          margin:0 0 10px;color:#193d39
        }
        .pc280-section-title b{font-size:11px}
        .pc280-section-title small{font-size:8.5px;color:#748783}
        .pc280-density-note{
          display:inline-flex;align-items:center;gap:5px;padding:4px 7px;
          border-radius:999px;background:#eef6f4;color:#55736e;font-size:8px;font-weight:800
        }
        .pc280-table-shell{max-height:calc(100vh - 245px)!important;overflow:auto!important}
        #workers .table-wrap,#epis .table-wrap,#deliveries .table-wrap,#stock .table-wrap,#companies .table-wrap{
          max-height:calc(100vh - 245px)!important;overflow:auto!important
        }
        .pc280-focus-view .panel,.pc280-focus-view .pc-card{box-shadow:0 4px 18px rgba(22,61,56,.05)!important}
        .pc280-role-readonly .primary[data-save],.pc280-role-readonly [data-delete]{display:none!important}
      }

      @media (min-width:1000px) and (max-width:1180px){
        .layout{grid-template-columns:248px minmax(0,1fr)!important}
        .sidebar{width:248px!important;min-width:248px!important;max-width:248px!important}
        .grid-2{grid-template-columns:1fr!important}
        .v260-home-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important}
        .company-filter{min-width:180px!important}
      }
    `;
    document.head.appendChild(s);
  }

  function arrangeNavigation(){
    const nav=$('.sidebar nav');
    if(!nav) return;
    $$('.pc280-nav-group',nav).forEach(x=>x.remove());
    const used=new Set();
    for(const g of GROUPS){
      const buttons=g.ids.map(id=>nav.querySelector(`.nav[data-view="${id}"]`)).filter(Boolean);
      if(!buttons.length) continue;
      const label=document.createElement('div');
      label.className='pc280-nav-group';
      label.textContent=g.title;
      nav.appendChild(label);
      buttons.forEach(b=>{nav.appendChild(b);used.add(b);});
    }
    const extras=$$('.nav[data-view]',nav).filter(b=>!used.has(b));
    if(extras.length){
      const label=document.createElement('div');
      label.className='pc280-nav-group';
      label.textContent='OUTROS';
      nav.appendChild(label);
      extras.forEach(b=>nav.appendChild(b));
    }
  }

  function installIdentity(){
    const brand=$('.sidebar-brand');
    if(brand&&!brand.querySelector('.pc280-desktop-badge')){
      const badge=document.createElement('span');
      badge.className='pc280-desktop-badge';
      badge.textContent='Desktop';
      brand.querySelector('.logo')?.appendChild(badge);
    }

    const foot=$('.sidebar-foot');
    if(foot&&!$('#pc280User')){
      const user=window.GestaoEpiAuth?.user?.()||{};
      const name=String(user.name||user.username||user.user||user.login||'Usuário');
      const role=String(user.role||'');
      const box=document.createElement('div');
      box.id='pc280User';
      box.className='pc280-user';
      box.innerHTML=`<div class="pc280-user-avatar">${name.slice(0,1).toUpperCase()}</div><div><b></b><small></small></div>`;
      box.querySelector('b').textContent=name;
      box.querySelector('small').textContent=role==='admin'?'Administrador':role==='campo'?'Operação':role==='consulta'?'Consulta':role||'Sessão ativa';
      foot.insertAdjacentElement('beforebegin',box);
    }

    const v=$('.pc-version');
    if(v) v.textContent=VERSION;
  }

  function cleanLegacyArtifacts(){
    $('#v273Welcome')?.remove();
    $('.v273-nav-group').forEach(x=>x.remove());
    $('.v273-hide-duplicate').forEach(x=>x.classList.remove('v273-hide-duplicate'));
  }

  function readCache(){
    try{
      const r=JSON.parse(localStorage.getItem('auditarEpiGestaoCacheV1')||'{}');
      r.app=r.app&&typeof r.app==='object'?r.app:{};
      for(const k of ['companies','workers','epis','deliveries'])r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];
      return r;
    }catch(_){return {app:{companies:[],workers:[],epis:[],deliveries:[]}}}
  }

  function norm(v=''){
    return String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  }

  function clickView(id){
    const b=$('.sidebar .nav[data-view="'+id+'"]');
    if(b){b.click();return true}
    return false;
  }

  function openSearchTarget(kind,id,label){
    const value=String(label||'');
    if(kind==='worker'){
      clickView('workers');
      setTimeout(()=>{
        const q=$('#workerSearch');
        if(q){q.value=value;q.dispatchEvent(new Event('input',{bubbles:true}));q.focus()}
      },100);
    }else if(kind==='epi'){
      clickView('epis');
      setTimeout(()=>{
        const q=$('#epiSearch');
        if(q){q.value=value;q.dispatchEvent(new Event('input',{bubbles:true}));q.focus()}
      },100);
    }else if(kind==='company'){
      const sel=$('#globalCompany');
      if(sel){
        sel.value=id;
        sel.dispatchEvent(new Event('change',{bubbles:true}));
      }
      clickView('dashboard');
    }else if(kind==='delivery'){
      clickView('deliveries');
      setTimeout(()=>{
        const q=$('#deliverySearch');
        if(q){q.value=value;q.dispatchEvent(new Event('input',{bubbles:true}));q.focus()}
      },100);
    }
    $('#pc280SearchResults')?.classList.remove('open');
  }

  function renderGlobalSearch(){
    const input=$('#pc280GlobalSearch'),box=$('#pc280SearchResults');
    if(!input||!box)return;
    const q=norm(input.value);
    if(q.length<2){box.classList.remove('open');box.innerHTML='';return}
    const r=readCache(),items=[];
    const companies=new Map(r.app.companies.map(x=>[x.id,x]));

    for(const w of r.app.workers){
      const hay=norm([w.name,w.cpf,w.reg,w.role,w.sector,companies.get(w.companyId)?.name].join(' '));
      if(hay.includes(q))items.push({kind:'worker',id:w.id,label:w.name||'Trabalhador',sub:[w.role,w.sector,companies.get(w.companyId)?.name].filter(Boolean).join(' • '),ico:'👷'});
      if(items.length>=6)break;
    }
    for(const e of r.app.epis){
      if(items.length>=10)break;
      const hay=norm([e.name,e.ca,e.model,e.size].join(' '));
      if(hay.includes(q))items.push({kind:'epi',id:e.id,label:e.name||'EPI',sub:[e.ca?'CA '+e.ca:'',e.model,e.size].filter(Boolean).join(' • '),ico:'🦺'});
    }
    for(const company of r.app.companies){
      if(items.length>=12)break;
      if(norm([company.name,company.cnpj].join(' ')).includes(q))items.push({kind:'company',id:company.id,label:company.name||'Empresa',sub:company.cnpj||'',ico:'🏢'});
    }

    box.innerHTML='';
    if(!items.length){
      const d=document.createElement('div');d.className='pc280-search-empty';d.textContent='Nenhum resultado encontrado.';box.appendChild(d);
    }else{
      items.forEach(item=>{
        const b=document.createElement('button');
        b.type='button';b.className='pc280-search-item';
        const ico=document.createElement('span');ico.className='pc280-search-ico';ico.textContent=item.ico;
        const txt=document.createElement('span');
        const strong=document.createElement('b');strong.textContent=item.label;
        const small=document.createElement('small');small.textContent=item.sub||'';
        txt.append(strong,small);
        const kind=document.createElement('span');kind.className='pc280-search-kind';kind.textContent=item.kind==='worker'?'Pessoa':item.kind==='epi'?'EPI':'Empresa';
        b.append(ico,txt,kind);
        b.addEventListener('click',()=>openSearchTarget(item.kind,item.id,item.label));
        box.appendChild(b);
      });
    }
    box.classList.add('open');
  }

  function installCommandBar(){
    const actions=$('.top-actions');
    if(!actions||$('#pc280Command'))return;
    const wrap=document.createElement('div');
    wrap.id='pc280Command';wrap.className='pc280-command';
    wrap.innerHTML='<span class="pc280-command-icon">⌕</span><input id="pc280GlobalSearch" type="search" autocomplete="off" placeholder="Buscar trabalhador, EPI, CA ou empresa"><span class="pc280-command-kbd">Ctrl K</span><div id="pc280SearchResults" class="pc280-command-results"></div>';
    actions.insertBefore(wrap,actions.firstChild);
    $('#pc280GlobalSearch').addEventListener('input',renderGlobalSearch);
    $('#pc280GlobalSearch').addEventListener('keydown',e=>{if(e.key==='Escape'){$('#pc280SearchResults')?.classList.remove('open');e.currentTarget.blur()}});
    document.addEventListener('click',e=>{if(!e.target.closest('#pc280Command'))$('#pc280SearchResults')?.classList.remove('open')});
  }

  function installDashboardShortcuts(){
    const dash=$('#dashboard');
    if(!dash||$('#pc280Shortcuts'))return;
    const bar=document.createElement('div');
    bar.id='pc280Shortcuts';bar.className='pc280-shortcuts';
    const defs=[
      ['newDeliveryPc','＋ Nova entrega','primary'],
      ['batchDeliveryPc','👥 Entrega em grupo',''],
      ['employeeSheetsPc','📄 Fichas de EPI',''],
      ['stock','📦 Estoque',''],
      ['nfImportPc','🧾 Nota Fiscal IA',''],
      ['alertsPc','⚠ Alertas',''],
      ['managerReportsPc','▥ Relatórios','']
    ];
    defs.forEach(([id,label,cls])=>{
      if(!$('.sidebar .nav[data-view="'+id+'"]'))return;
      const b=document.createElement('button');b.type='button';b.className='pc280-shortcut '+cls;b.textContent=label;b.onclick=()=>clickView(id);bar.appendChild(b);
    });
    const first=dash.firstElementChild;
    if(first)dash.insertBefore(bar,first);else dash.appendChild(bar);
  }

  function decorateDataViews(){
    for(const id of ['workers','epis','deliveries','stock','companies','employeeSheetsPc','receiptsPc']){
      $('#'+id)?.classList.add('pc280-focus-view');
    }
    const user=window.GestaoEpiAuth?.user?.()||{};
    document.body.classList.toggle('pc280-role-readonly',String(user.role||'')==='consulta');
  }

  function installKeyboard(){
    if(window.__pc280Keyboard)return;
    window.__pc280Keyboard=true;
    document.addEventListener('keydown',e=>{
      if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='k'){
        e.preventDefault();const q=$('#pc280GlobalSearch');if(q){q.focus();q.select()}
      }
      if(e.altKey&&e.key==='1'){e.preventDefault();clickView('dashboard')}
      if(e.altKey&&e.key==='2'){e.preventDefault();clickView('newDeliveryPc')}
      if(e.altKey&&e.key==='3'){e.preventDefault();clickView('workers')}
      if(e.altKey&&e.key==='4'){e.preventDefault();clickView('stock')}
    });
  }

  function pass(){
    document.body.classList.add('pc-desktop-v280');
    installStyles();
    cleanLegacyArtifacts();
    arrangeNavigation();
    installIdentity();
    installCommandBar();
    installDashboardShortcuts();
    decorateDataViews();
    installKeyboard();
  }

  function boot(){
    [0,120,350,800,1500,2800,5000,8000].forEach(ms=>setTimeout(pass,ms));
    window.addEventListener('focus',()=>setTimeout(pass,80));
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();