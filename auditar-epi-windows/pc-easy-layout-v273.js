(()=>{
  const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
  let arranging=false;

  const LABELS={
    dashboard:'Início',alertsPc:'Alertas',fastDeliveryPc:'Entregar EPI',newDeliveryPc:'Nova entrega',employeeSheetsPc:'Fichas de EPI',workers:'Funcionários',deliveries:'Histórico de entregas',returnsPc:'Devoluções',replacementPc:'Trocas previstas',stock:'Estoque',inventoryPc:'Conferir estoque',purchasesPc:'Compras',epis:'Cadastro de EPIs',caSmartPc:'Conferência de CA',rolePpePc:'EPIs por função',qrPeoplePc:'QR dos funcionários',faceEnrollPc:'Biometria facial',externalsPc:'Terceiros',importWorkersPc:'Importar funcionários',managerReportsPc:'Relatórios',indicators:'Indicadores',inspectionPc:'Fiscalização',dataQualityPc:'Qualidade dos cadastros',dataSafetyPc:'Segurança e backup',auditPc:'Auditoria',companies:'Empresas',pending:'Pendências detalhadas'
  };
  const GROUPS=[
    {title:'USO DIÁRIO',ids:['dashboard','fastDeliveryPc','newDeliveryPc','employeeSheetsPc','workers','deliveries','alertsPc']},
    {title:'ESTOQUE E TROCAS',ids:['stock','inventoryPc','returnsPc','replacementPc','purchasesPc']},
    {title:'CADASTROS',ids:['epis','caSmartPc','rolePpePc','qrPeoplePc','faceEnrollPc','externalsPc','importWorkersPc']},
    {title:'GESTÃO',ids:['managerReportsPc','indicators','inspectionPc','dataQualityPc','dataSafetyPc','auditPc','companies','pending']}
  ];

  function css(){if($('#v273EasyCss'))return;const s=document.createElement('style');s.id='v273EasyCss';s.textContent=`
    :root{--easy-gap:14px}
    .sidebar{width:260px!important}.main{margin-left:0!important}.sidebar nav{padding:6px 9px 14px!important}.sidebar .nav{min-height:42px!important;margin:2px 0!important;border-radius:10px!important;font-size:12px!important;font-weight:750!important;padding:9px 11px!important;gap:9px!important}.sidebar .nav span{font-size:12px!important}.sidebar .nav.active{font-weight:900!important}.v273-nav-group{padding:14px 10px 5px;color:#8ba09c;font-size:8px;font-weight:950;letter-spacing:.11em;text-transform:uppercase;user-select:none}.v273-nav-group:first-child{padding-top:7px}.topbar{gap:14px!important;align-items:center!important;padding:15px 20px!important}.topbar>div:first-child h1{font-size:20px!important}.topbar>div:first-child p{font-size:10.5px!important}.top-actions{gap:8px!important}.main{padding-bottom:24px!important}.view{padding-left:20px!important;padding-right:20px!important}.panel,.v260-card,.v25c,.v270-card,.v272-card{border-radius:14px!important}.primary,.secondary,.v260-btn,.v25btn,.v270-btn,.v272-open,.worker-sheet-btn{min-height:38px!important;font-size:11px!important}.data-table,.v260-table,.v25t,.v270-table,.v272-table,.worker-sheet-table{font-size:11px!important}.data-table th,.v260-table th,.v25t th,.v270-table th,.v272-table th,.worker-sheet-table th{font-size:9.5px!important}.data-table td,.v260-table td,.v25t td,.v270-table td,.v272-table td,.worker-sheet-table td{padding-top:9px!important;padding-bottom:9px!important}.v260-home{margin:0 0 18px!important}.v260-home>h2{font-size:18px!important;margin-bottom:5px!important}.v260-home>h2::after{content:' Escolha uma ação para começar.';display:block;font-size:10px;font-weight:500;color:#70847f;margin-top:4px}.v260-home-grid{grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:10px!important}.v260-home-grid button{min-height:98px!important;padding:14px!important;border-radius:14px!important}.v260-home-grid span{font-size:25px!important}.v260-home-grid b{font-size:12px!important}.v260-home-grid small{font-size:9.5px!important;line-height:1.35!important}.v273-welcome{display:flex;justify-content:space-between;align-items:center;gap:12px;background:#f5faf9;border:1px solid #dbe8e5;border-radius:14px;padding:12px 14px;margin:0 0 13px}.v273-welcome b{display:block;color:#173d39;font-size:13px}.v273-welcome small{display:block;color:#6d827e;font-size:10px;margin-top:2px}.v273-welcome .tag{white-space:nowrap;background:#ecfdf3;color:#166534;border-radius:999px;padding:6px 9px;font-size:9px;font-weight:900}.company-filter{font-size:9px!important}.company-filter select{min-height:38px!important}.v273-hide-duplicate{display:none!important}@media(max-width:1050px){.v260-home-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}.sidebar{width:230px!important}}@media(max-width:720px){.sidebar{width:auto!important}.view{padding-left:12px!important;padding-right:12px!important}.v260-home-grid{grid-template-columns:1fr 1fr!important}.v273-welcome{align-items:flex-start}.topbar{padding:12px!important}}
  `;document.head.appendChild(s)}

  function rename(){for(const [id,label] of Object.entries(LABELS)){const el=$(`.sidebar .nav[data-view="${id}"] span`);if(el&&el.textContent!==label)el.textContent=label}}

  function group(title){const d=document.createElement('div');d.className='v273-nav-group';d.textContent=title;return d}

  function arrangeNav(){if(arranging)return;const nav=$('.sidebar nav');if(!nav)return;arranging=true;try{
    rename();
    $$('.v273-nav-group',nav).forEach(x=>x.remove());
    const used=new Set();
    for(const g of GROUPS){const available=g.ids.map(id=>nav.querySelector(`.nav[data-view="${id}"]`)).filter(Boolean);if(!available.length)continue;nav.appendChild(group(g.title));for(const b of available){nav.appendChild(b);used.add(b)}}
    const extras=$$('.nav[data-view]',nav).filter(b=>!used.has(b));if(extras.length){nav.appendChild(group('OUTROS'));extras.forEach(b=>nav.appendChild(b))}
  }finally{arranging=false}}

  function easyHome(){const home=$('#v260Home');if(!home)return false;const h=home.querySelector('h2');if(h)h.textContent='Acesso rápido';const map={fastDeliveryPc:['Entregar EPI','Registrar uma entrega rapidamente.'],workers:['Funcionários','Consultar dados e histórico.'],returnsPc:['Devoluções','Registrar devolução ou desligamento.'],alertsPc:['Alertas','Ver o que precisa de atenção.'],inspectionPc:['Fiscalização','Organizar documentos para fiscalização.']};for(const [id,t] of Object.entries(map)){const b=home.querySelector(`[data-v260-go="${id}"]`);if(!b)continue;const bold=b.querySelector('b'),sm=b.querySelector('small');if(bold)bold.textContent=t[0];if(sm)sm.textContent=t[1]}
    if(!$('#v273Welcome')){const d=document.createElement('div');d.id='v273Welcome';d.className='v273-welcome';d.innerHTML='<div><b>Gestão EPI</b><small>As funções mais usadas estão primeiro. As opções administrativas ficam organizadas abaixo.</small></div><span class="tag">✓ Pronto para usar</span>';home.insertAdjacentElement('afterend',d)}return true}

  function cleanDuplicates(){
    // Mantém recursos disponíveis, mas reduz duplicidade visual na navegação.
    const pending=$('.sidebar .nav[data-view="pending"]');if(pending)pending.classList.add('v273-hide-duplicate');
    const indicators=$('.sidebar .nav[data-view="indicators"]');if(indicators)indicators.classList.add('v273-hide-duplicate');
  }

  function simplifyTop(){const t=$('#viewSub');if(t&&/Veja rapidamente como está o controle de EPI/i.test(t.textContent||''))t.textContent='Resumo do controle de EPI e atalhos para as principais tarefas.'}

  function pass(){arrangeNav();easyHome();cleanDuplicates();simplifyTop()}
  function boot(){css();let n=0;const timer=setInterval(()=>{n++;pass();if(n>=20)clearInterval(timer)},350);setTimeout(pass,80)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
