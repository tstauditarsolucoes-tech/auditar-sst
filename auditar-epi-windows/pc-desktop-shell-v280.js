(()=>{
  const VERSION='PC v2.8.0';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];

  const GROUPS=[
    {title:'OPERAÇÃO',ids:['dashboard','fastDeliveryPc','newDeliveryPc','batchDeliveryPc','employeeSheetsPc','workers','deliveries']},
    {title:'ESTOQUE',ids:['stock','inventoryPc','purchasesPc','returnsPc','replacementPc']},
    {title:'CADASTROS',ids:['epis','caSmartPc','rolePpePc','importWorkersPc','qrPeoplePc','faceEnrollPc','externalsPc']},
    {title:'GESTÃO E CONTROLE',ids:['alertsPc','managerReportsPc','indicators','inspectionPc','dataQualityPc','dataSafetyPc','auditPc','companies','pending']}
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
    $$('.v273-nav-group').forEach(x=>x.remove());
    $$('.v273-hide-duplicate').forEach(x=>x.classList.remove('v273-hide-duplicate'));
  }

  function pass(){
    document.body.classList.add('pc-desktop-v280');
    installStyles();
    cleanLegacyArtifacts();
    arrangeNavigation();
    installIdentity();
  }

  function boot(){
    [0,120,350,800,1500,2800,5000,8000].forEach(ms=>setTimeout(pass,ms));
    window.addEventListener('focus',()=>setTimeout(pass,80));
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();