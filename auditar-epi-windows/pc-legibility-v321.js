(()=>{
'use strict';
function install(){
  if(document.getElementById('pcLegibilityV321Style'))return;
  const s=document.createElement('style');
  s.id='pcLegibilityV321Style';
  s.textContent=`
    /* Gestão EPI PC v3.2.1 — escala confortável para desktop 1366x768+ */
    @media (min-width:1000px){
      body{font-size:14px!important}

      .sidebar-brand .logo{font-size:19px!important}
      .sidebar-brand small{font-size:9.5px!important}
      .pc280-nav-group{font-size:9.5px!important;letter-spacing:.11em!important;padding-top:13px!important}
      .sidebar .nav{min-height:41px!important;padding:9px 10px!important;font-size:15px!important}
      .sidebar .nav span{font-size:13.5px!important;line-height:1.25!important}
      .sidebar-foot b{font-size:12px!important}
      .sidebar-foot small{font-size:10.5px!important;line-height:1.25!important}
      .pc280-user b{font-size:12px!important}
      .pc280-user small{font-size:10px!important}
      .pc280-user-avatar{font-size:13px!important}

      .topbar{min-height:88px!important;padding-top:15px!important;padding-bottom:14px!important;gap:16px!important}
      .topbar>div:first-child{
        flex:0 0 205px!important;
        min-width:205px!important;
        max-width:205px!important;
        overflow:visible!important
      }
      .topbar h1,#viewTitle{
        font-size:27px!important;
        line-height:1.08!important;
        letter-spacing:-.025em!important;
        white-space:normal!important;
        overflow:visible!important;
        text-overflow:clip!important;
        word-break:normal!important;
        overflow-wrap:normal!important
      }
      .topbar p,#viewSub{
        font-size:12.5px!important;
        line-height:1.35!important;
        margin-top:5px!important;
        white-space:normal!important;
        overflow:visible!important;
        text-overflow:clip!important;
        max-width:205px!important
      }
      .top-actions{gap:9px!important}
      .company-filter{font-size:10.5px!important;min-width:200px!important}
      .company-filter select,#globalCompany{font-size:12.5px!important;min-height:43px!important;padding:9px 11px!important}
      #btnRefresh{min-height:43px!important;font-size:12px!important;padding:9px 13px!important}

      .pc280-command{width:min(330px,25vw)!important;min-width:225px!important}
      .pc280-command input{
        min-height:43px!important;
        font-size:12.5px!important;
        padding-top:10px!important;
        padding-bottom:10px!important
      }
      .pc280-command-icon{font-size:15px!important}
      .pc280-command-kbd{font-size:9px!important}
      .pc280-search-item{padding:10px!important}
      .pc280-search-item b{font-size:12px!important}
      .pc280-search-item small{font-size:10.5px!important;line-height:1.3!important}
      .pc280-search-kind{font-size:9px!important}
      .pc280-search-empty{font-size:11px!important}

      .view{padding-top:24px!important}
      .split-head h2,.pc-modern-head h2,.v260-head h2,.v272-head h2{font-size:21px!important;line-height:1.2!important}
      .split-head p,.pc-modern-head p,.v260-head p,.v272-head p{
        font-size:12.5px!important;
        line-height:1.45!important
      }

      .metric{min-height:116px!important;padding:16px 17px!important}
      .metric span{font-size:12.5px!important;line-height:1.3!important}
      .metric strong{font-size:31px!important;margin:7px 0 3px!important}
      .metric.text strong{font-size:18px!important;line-height:1.3!important}
      .metric small{font-size:11px!important;line-height:1.3!important}

      .panel,.pc-card,.v260-card,.v25c,.v270-card,.v272-card{padding:16px!important}
      .panel-head h2{font-size:16.5px!important;line-height:1.25!important}
      .panel-head p{font-size:11.5px!important;line-height:1.4!important}
      .section-note,.muted{font-size:11.5px!important;line-height:1.45!important}

      input,select,textarea{font-size:13px!important}
      .filters input{min-height:42px!important}
      label{line-height:1.35}

      .data-table,.v260-table,.v25t,.v270-table,.v272-table,.worker-sheet-table,.pc-preview table{
        font-size:12px!important;
        line-height:1.4!important
      }
      .data-table th,.v260-table th,.v25t th,.v270-table th,.v272-table th,.worker-sheet-table th,.pc-preview th{
        font-size:10.5px!important;
        padding:9px 10px!important
      }
      .data-table td,.v260-table td,.v25t td,.v270-table td,.v272-table td,.worker-sheet-table td,.pc-preview td{
        padding:10px!important
      }
      .status,.badge{font-size:11px!important}

      .primary,.secondary,.link,.v260-btn,.v25btn,.v270-btn,.v272-open,.worker-sheet-btn{
        min-height:40px!important;
        font-size:12px!important;
        padding:9px 12px!important
      }
      .pc280-shortcut{min-height:38px!important;font-size:11.5px!important;padding:8px 11px!important}
      .pc280-section-title b{font-size:13px!important}
      .pc280-section-title small{font-size:10.5px!important}
      .pc280-density-note{font-size:10px!important}

      .v260-home>h2{font-size:17px!important}
      .v260-home-grid b{font-size:12px!important}
      .v260-home-grid small{font-size:10.5px!important;line-height:1.3!important}

      .pc310-kpi span{font-size:10.5px!important}
      .pc310-kpi strong{font-size:27px!important}
      .pc310-kpi small{font-size:10.5px!important}
      .pc310-head b{font-size:13.5px!important}
      .pc310-head small{font-size:10.5px!important}
      .pc310-row b{font-size:12px!important}
      .pc310-row small{font-size:10.5px!important;line-height:1.35!important}
      .pc310-row strong{font-size:13px!important}
      .pc310-chip,.pc310-action{font-size:10.5px!important}
      .pc310-barcol b{font-size:10.5px!important}
      .pc310-barcol small{font-size:9.5px!important}

      /* Central LGPD */
      .legal320-note{font-size:12.5px!important;line-height:1.55!important;padding:14px 16px!important}
      .legal320-card span{font-size:10.5px!important}
      .legal320-card strong{font-size:27px!important}
      .legal320-card small{font-size:10.5px!important;line-height:1.35!important}
      .legal320-panel{padding:17px!important}
      .legal320-panel h3{font-size:17px!important;line-height:1.25!important}
      .legal320-panel>p{font-size:11.5px!important;line-height:1.45!important}
      .legal320-check{padding:11px!important;gap:10px!important}
      .legal320-check input{width:16px!important;height:16px!important}
      .legal320-check b{font-size:12px!important;line-height:1.35!important}
      .legal320-check small{font-size:10.5px!important;line-height:1.4!important}
      .legal320-form label{font-size:11.5px!important;line-height:1.35!important}
      .legal320-form input,.legal320-form textarea,.legal320-form select{
        font-size:12.5px!important;
        padding:10px!important;
        min-height:42px!important
      }
      .legal320-form textarea{min-height:94px!important}
      .legal320-btn{font-size:11.5px!important;padding:10px 13px!important;min-height:40px!important}
      .legal320-doc b{font-size:12px!important}
      .legal320-doc small{font-size:10.5px!important;line-height:1.35!important}
      .legal320-table{font-size:11.5px!important}
      .legal320-table th{font-size:10px!important}
      .legal320-status{font-size:10.5px!important}

      /* alertas / atenção */
      .v260-alert-item b,.v260-attention-item b,.v260-row b{font-size:12.5px!important}
      .v260-alert-item small,.v260-attention-item small,.v260-row small{font-size:10.5px!important;line-height:1.4!important}

      .worker-sheet-paper{font-size:12px!important}
      .worker-sheet-note{font-size:11px!important;line-height:1.5!important}
    }

    @media (min-width:1000px) and (max-width:1450px){
      .topbar{
        flex-wrap:wrap!important;
        align-items:flex-end!important;
        row-gap:10px!important
      }
      .topbar>div:first-child{
        flex:0 0 190px!important;
        min-width:190px!important;
        max-width:190px!important
      }
      .topbar p,#viewSub{max-width:190px!important}
      .top-actions{
        flex:1 1 calc(100% - 210px)!important;
        min-width:0!important;
        justify-content:flex-end!important;
        flex-wrap:nowrap!important
      }
      .pc280-command{width:min(290px,24vw)!important;min-width:210px!important}
      .company-filter{min-width:180px!important}
    }

    @media (min-width:1000px) and (max-width:1180px){
      .topbar>div:first-child{
        flex:1 1 100%!important;
        min-width:0!important;
        max-width:none!important
      }
      .topbar p,#viewSub{max-width:none!important}
      .top-actions{flex:1 1 100%!important;justify-content:flex-start!important;flex-wrap:wrap!important}
      .pc280-command{width:min(360px,100%)!important}
    }
  `;
  document.head.appendChild(s);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();