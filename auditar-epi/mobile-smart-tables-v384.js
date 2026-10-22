(()=>{
'use strict';
/* Apresentação responsiva v3.8.4: não altera estoque, dados ou cálculos. */
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
function setupCss(){
 if($('#smart384Style'))return;
 const style=document.createElement('style');style.id='smart384Style';
 style.textContent=".sm350-table td.sm384-negative{background:#fff0ee;border-radius:8px;color:#9a2727;font-weight:800;padding-left:6px;padding-right:6px}"+"\n#smartManagementV350{min-width:0;max-width:100%;overflow-x:hidden}\n#smartManagementV350 .sm350-wrap,#smartManagementV350 #smartContent{min-width:0;max-width:100%;overflow-x:hidden}\n#smartManagementV350 .sm350-tabs{max-width:100%;overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch}\n#smartManagementV350 .sm350-tabs button{flex:0 0 auto}\n#smartManagementV350 .sm350-toolbar label{min-width:0;max-width:100%;flex:1 1 185px}\n#smartManagementV350 .sm350-toolbar select{min-width:0;max-width:100%}\n@media(max-width:760px){\n#smartManagementV350 .view-head{min-width:0}\n#smartManagementV350 .view-head>div:last-child{min-width:0}\n#smartManagementV350 .view-head h2{font-size:clamp(20px,6vw,27px)!important;line-height:1.12;overflow-wrap:anywhere}\n#smartManagementV350 .sm350-card{min-width:0;max-width:100%;overflow:hidden!important}\n#smartManagementV350 .sm350-table,#smartManagementV350 .sm350-table tbody,#smartManagementV350 .sm350-table tr,#smartManagementV350 .sm350-table td{display:block;width:100%;min-width:0;max-width:100%}\n#smartManagementV350 .sm350-table thead{display:none!important}\n#smartManagementV350 .sm350-table tr{padding:9px 12px;background:#fff;border:1px solid #dce8e5;border-radius:13px;margin:0 0 11px}\n#smartManagementV350 .sm350-table td{display:grid;grid-template-columns:minmax(100px,40%) minmax(0,60%);gap:8px;border:0;border-bottom:1px solid #edf1f0;padding:9px 0;align-items:start;font-size:13px;overflow-wrap:anywhere}\n#smartManagementV350 .sm350-table td:last-child{border-bottom:0}\n#smartManagementV350 .sm350-table td::before{content:attr(data-smart384-label);font-size:12px;font-weight:850;color:#526f69;overflow-wrap:anywhere}\n#smartManagementV350 .sm350-table td input{min-width:0;max-width:100%;width:100%}\n#smartManagementV350 .sm350-table td .sm350-pill{display:inline-block;max-width:100%;white-space:normal}\n#smartManagementV350 .sm350-row{flex-wrap:wrap;overflow-wrap:anywhere;min-width:0}\n#smartManagementV350 .sm350-row>div{min-width:0;max-width:100%}\n#smartManagementV350 .sm350-note{font-size:13px;line-height:1.45;overflow-wrap:anywhere}\n}";
 document.head.appendChild(style);
}
function annotate(){
 const root=$('#smartContent');if(!root)return;
 $$('.sm350-table',root).forEach(table=>{
  const headers=$$('thead th',table).map(th=>th.textContent.trim());
  $$('tbody tr',table).forEach(row=>$$('td',row).forEach((cell,i)=>{
   const label=headers[i]||'Informação';
   if(cell.dataset.smart384Label!==label)cell.dataset.smart384Label=label;
   if(label.toLowerCase()==='saldo'){
     const value=Number((cell.textContent||'').replace(/[^0-9.-]/g,''));
     cell.classList.toggle('sm384-negative',Number.isFinite(value)&&value<0);
     if(Number.isFinite(value)&&value<0)cell.setAttribute('title','Saldo negativo: conferir entradas, entregas e movimentações. Não houve ajuste automático.');
   }
  }));
 });
}
let observedRoot=null;
function connect(){
 const root=$('#smartContent');
 if(!root)return;
 if(root!==observedRoot){
  new MutationObserver(annotate).observe(root,{childList:true,subtree:false});
  observedRoot=root;
 }
 annotate();
}
function boot(){
 setupCss();connect();
 document.addEventListener('click',e=>{
  if(e.target.closest?.('[data-smart-tab],#smartRefresh,[data-go="smartManagementV350"]')){
   setTimeout(connect,0);
   setTimeout(connect,120);
  }
 });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();