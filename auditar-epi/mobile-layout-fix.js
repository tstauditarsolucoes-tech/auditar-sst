(() => {
  const STYLE_ID='gestaoEpiMobileLayoutFix';

  function injectStyle(){
    if(document.getElementById(STYLE_ID)) return;
    const style=document.createElement('style');
    style.id=STYLE_ID;
    style.textContent=`
      html,body{width:100%;max-width:100%;overflow-x:hidden!important}
      body{position:relative}
      .topbar,.app-shell,.view,.card,.hero-card,.receipt-paper{min-width:0;max-width:100%}
      .topbar{width:100%;gap:8px}
      .topbar>*{min-width:0}
      .topbar>div:first-child{min-width:0}
      .epi-user-chip{min-width:0!important;max-width:100%!important}
      .epi-user-chip>span{min-width:0;overflow:hidden}
      .epi-tenant-name{max-width:100%!important}
      input,select,textarea,button{max-width:100%}

      /* Tela de login padronizada em CAIXA ALTA.
         O text-transform altera somente a exibição; o valor real do usuário
         continua intacto para não interferir na autenticação. */
      .epi-auth-card h1,
      .epi-auth-card>p,
      .epi-auth-card label,
      .epi-auth-card button,
      .epi-auth-error{ text-transform:uppercase!important; }
      #epiTenantCode,
      #epiAuthUser{ text-transform:uppercase!important; }
      #epiTenantCode::placeholder,
      #epiAuthUser::placeholder,
      #epiAuthPass::placeholder{ text-transform:uppercase!important; }

      @media(max-width:520px){
        .topbar{display:grid!important;grid-template-columns:minmax(0,1fr) auto;align-items:center;padding:8px 10px!important;gap:7px 8px!important}
        .topbar>div:first-child{grid-column:1;grid-row:1;overflow:hidden}
        .topbar>div:first-child .brand{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .topbar>div:not(:first-child):not(#epiUserChip){grid-column:2;grid-row:1;justify-self:end;min-width:0}
        #epiUserChip{grid-column:1/-1;grid-row:2;width:100%;display:flex!important;justify-content:space-between;align-items:center;border-top:1px solid #e4efed;padding-top:6px;gap:8px}
        #epiUserChip>span{display:block;flex:1;line-height:1.15}
        #epiLogout{flex:0 0 auto}
        #epiCloudStatus{max-width:62px!important}
        .topbar .icon-btn{width:38px!important;height:38px!important;border-radius:12px!important}
        .app-shell{width:100%;padding-left:12px!important;padding-right:12px!important}
        .view-head,.section-title,.list-item{min-width:0}
        .section-title{flex-wrap:wrap}
        .section-title>*,.view-head>*{min-width:0}
        .delivery-item{width:100%;max-width:100%}
      }
    `;
    document.head.appendChild(style);
  }

  function resetHorizontalScroll(){
    try{
      const y=window.scrollY||document.documentElement.scrollTop||document.body.scrollTop||0;
      window.scrollTo(0,y);
      document.documentElement.scrollLeft=0;
      document.body.scrollLeft=0;
    }catch(_){}
  }

  function scheduleReset(){
    [0,120,320,650].forEach(ms=>setTimeout(resetHorizontalScroll,ms));
  }

  injectStyle();
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',()=>{injectStyle();scheduleReset();});
  }else{
    scheduleReset();
  }

  window.addEventListener('orientationchange',scheduleReset);
  window.addEventListener('resize',()=>{
    if(window.innerWidth<=520) setTimeout(resetHorizontalScroll,60);
  });
  if(window.visualViewport){
    window.visualViewport.addEventListener('resize',()=>{
      if(window.innerWidth<=520) setTimeout(resetHorizontalScroll,60);
    });
  }
})();
