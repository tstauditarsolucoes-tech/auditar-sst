(()=>{
'use strict';
const APP='auditarEpiV1',STOCK='auditarEpiStockV1';
const LAST_COMPANY='gestaoEpiLastDeliveryCompanyV310';
const ERRORS='gestaoEpiUiDiagnosticsV310';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function read(k,f){try{return {...f,...JSON.parse(localStorage.getItem(k)||'{}')}}catch{return f}}
function app(){return read(APP,{companies:[],workers:[],epis:[],deliveries:[]})}
function stock(){return read(STOCK,{movements:[],minimums:{}})}
function toast(m){const e=$('#toast');if(!e)return;e.textContent=m;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2400)}

function recordError(kind,value){
  try{
    const rows=JSON.parse(localStorage.getItem(ERRORS)||'[]');
    rows.unshift({at:new Date().toISOString(),kind,message:String(value?.message||value||'Erro de interface').slice(0,500),stack:String(value?.stack||'').slice(0,1400)});
    localStorage.setItem(ERRORS,JSON.stringify(rows.slice(0,25)));
  }catch(_){}
}
window.addEventListener('error',e=>recordError('error',e.error||e.message));
window.addEventListener('unhandledrejection',e=>recordError('promise',e.reason));
window.GestaoEpiUiHealth={
  report:()=>{try{return JSON.parse(localStorage.getItem(ERRORS)||'[]')}catch{return[]}},
  clear:()=>localStorage.removeItem(ERRORS)
};

function installStyles(){
  if($('#qualityV310Style'))return;
  const s=document.createElement('style');s.id='qualityV310Style';s.textContent=`
    :root{--q-accent:#0c8d72;--q-soft:#edf8f5;--q-border:#d8e7e3}
    .view-head{margin-bottom:12px!important}.view-head h2{letter-spacing:-.02em}.view-head p{line-height:1.35}
    .card{border-color:var(--q-border)!important;box-shadow:0 7px 22px rgba(19,72,64,.055)!important}
    input,select,textarea{border-radius:13px!important;border-color:#d4e2df!important;background:#fcfefd!important}
    .primary,.secondary,.tiny,.menu-card{transition:transform .12s ease,box-shadow .12s ease,background .12s ease}
    button:active{transform:translateY(1px)}
    .list-item{border-color:var(--q-border)!important}
    #delivery.view.active #btnSaveDelivery{position:sticky;bottom:max(12px,env(safe-area-inset-bottom));z-index:80;box-shadow:0 15px 35px rgba(6,112,89,.28);margin-top:14px}
    .q310-delivery-progress{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:0 0 10px}
    .q310-step{background:#eef5f3;border:1px solid #dbe9e6;border-radius:11px;padding:8px;text-align:center;font-size:9px;font-weight:900;color:#6a817d}
    .q310-step.done{background:#e7f8f2;color:#08705d;border-color:#c8e9df}.q310-step.current{background:#0c8d72;color:#fff;border-color:#0c8d72}
    .q310-fastbox{margin:10px 0 0;padding:12px;border-radius:15px;background:linear-gradient(145deg,#f7fcfa,#eef8f5);border:1px solid #d8ebe5}
    .q310-fasthead{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}
    .q310-fasthead b{font-size:12px;color:#244e47}.q310-fasthead small{font-size:9px;color:#718682}
    .q310-repeat{width:100%;min-height:44px;border:0;border-radius:12px;background:#0c8d72;color:#fff;font-weight:900;font-size:12px;margin-bottom:8px}
    .q310-repeat[hidden]{display:none!important}
    .q310-chips{display:flex;gap:6px;overflow:auto;padding-bottom:2px}
    .q310-chip{flex:0 0 auto;border:1px solid #d2e5df;background:#fff;color:#23564d;border-radius:999px;padding:8px 10px;font-size:10px;font-weight:850;max-width:190px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .q310-last{font-size:9px;line-height:1.4;color:#637b76;margin-bottom:7px}
    .q310-empty{font-size:9px;color:#7a8f8b;padding:5px 0}
    .q310-health{display:inline-flex;align-items:center;gap:5px;font-size:9px;color:#6f837f}.q310-health i{width:7px;height:7px;border-radius:50%;background:#0ba77a}
    @media(max-width:420px){.card{border-radius:17px!important}.q310-chip{max-width:160px}}
  `;document.head.appendChild(s);
}

function epiName(id){return app().epis.find(e=>e.id===id)?.name||'EPI'}
function workerLastDelivery(workerId){
  return app().deliveries.filter(d=>d.workerId===workerId&&d.cancelled!==true)
    .sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')))[0]||null;
}
function frequentEpis(companyId,workerId){
  const a=app(),score=new Map();
  const now=Date.now(),windowMs=120*86400000;
  a.deliveries.forEach(d=>{
    if(d.cancelled===true)return;
    if(companyId&&d.companyId!==companyId)return;
    const age=Math.max(0,now-Date.parse(d.createdAt||0));
    if(age>windowMs)return;
    const boost=d.workerId===workerId?4:1;
    (d.items||[]).forEach(i=>score.set(i.epiId,(score.get(i.epiId)||0)+Number(i.qty||1)*boost));
  });
  return [...score.entries()].sort((x,y)=>y[1]-x[1]).slice(0,6).map(x=>x[0]);
}
function ensureRows(n){
  while($$('#deliveryItems .delivery-item').length<n)$('#btnAddItem')?.click();
}
function applyItems(items,{replace=false}={}){
  const valid=(items||[]).filter(i=>i?.epiId);
  if(!valid.length)return toast('Nenhum EPI para reutilizar.');
  let rows=$$('#deliveryItems .delivery-item');
  if(replace){
    while(rows.length>1){rows.at(-1)?.querySelector('.item-remove')?.click();rows=$$('#deliveryItems .delivery-item')}
    rows[0]?.querySelector('.item-epi')&&(rows[0].querySelector('.item-epi').value='');
  }
  ensureRows(valid.length);
  rows=$$('#deliveryItems .delivery-item');
  valid.forEach((item,i)=>{
    const row=rows[i];if(!row)return;
    const sel=row.querySelector('.item-epi'),qty=row.querySelector('.item-qty');
    if(sel){sel.value=item.epiId;sel.dispatchEvent(new Event('change',{bubbles:true}))}
    if(qty)qty.value=String(Math.max(1,Number(item.qty||1)));
  });
  toast(replace?'EPIs da última entrega preenchidos.':'EPI adicionado.');
  updateDeliveryAssistant();
}
function addOneEpi(epiId){
  let row=$$('#deliveryItems .delivery-item').find(r=>!r.querySelector('.item-epi')?.value);
  if(!row){$('#btnAddItem')?.click();row=$$('#deliveryItems .delivery-item').at(-1)}
  const sel=row?.querySelector('.item-epi');
  if(sel){sel.value=epiId;sel.dispatchEvent(new Event('change',{bubbles:true}));toast(epiName(epiId)+' adicionado.')}
  updateDeliveryAssistant();
}
function fmtDate(v){try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short'}).format(new Date(v))}catch{return''}}

function installDeliveryAssistant(){
  const view=$('#delivery');if(!view||$('#q310Fast'))return;
  const head=view.querySelector('.view-head');
  const progress=document.createElement('div');progress.id='q310Progress';progress.className='q310-delivery-progress';
  progress.innerHTML='<div class="q310-step current" data-qstep="1">1 • Trabalhador</div><div class="q310-step" data-qstep="2">2 • EPIs</div><div class="q310-step" data-qstep="3">3 • Confirmar</div>';
  head?.insertAdjacentElement('afterend',progress);

  const firstCard=view.querySelector('.card');
  const box=document.createElement('div');box.id='q310Fast';box.className='q310-fastbox';
  box.innerHTML='<div class="q310-fasthead"><b>⚡ Atalhos desta entrega</b><small>menos toques</small></div><div id="q310Last" class="q310-last"></div><button id="q310Repeat" class="q310-repeat" type="button" hidden>↻ Repetir EPIs da última entrega</button><div id="q310Chips" class="q310-chips"></div>';
  firstCard?.appendChild(box);

  $('#q310Repeat')?.addEventListener('click',()=>{
    const d=workerLastDelivery($('#deliveryWorker')?.value||'');
    if(d)applyItems(d.items||[],{replace:true});
  });
  $('#deliveryCompany')?.addEventListener('change',()=>{
    const v=$('#deliveryCompany')?.value||'';if(v)localStorage.setItem(LAST_COMPANY,v);
    setTimeout(updateDeliveryAssistant,30);
  });
  $('#deliveryWorker')?.addEventListener('change',()=>setTimeout(updateDeliveryAssistant,20));
  $('#btnAddItem')?.addEventListener('click',()=>setTimeout(updateDeliveryAssistant,20));
  $('#deliveryItems')?.addEventListener('change',updateDeliveryAssistant);
  $('#deliveryItems')?.addEventListener('click',()=>setTimeout(updateDeliveryAssistant,30));
  view.addEventListener('focusin',updateDeliveryAssistant);
}
function updateDeliveryAssistant(){
  const box=$('#q310Fast');if(!box)return;
  const companyId=$('#deliveryCompany')?.value||'',workerId=$('#deliveryWorker')?.value||'';
  const last=workerId?workerLastDelivery(workerId):null;
  const repeat=$('#q310Repeat'),lastEl=$('#q310Last'),chips=$('#q310Chips');
  if(last){
    const names=(last.items||[]).slice(0,4).map(i=>epiName(i.epiId)).join(', ');
    lastEl.textContent='Última entrega: '+fmtDate(last.createdAt)+(names?' • '+names:'');
    repeat.hidden=!(last.items||[]).length;
  }else{
    lastEl.textContent=workerId?'Primeira entrega deste trabalhador no histórico local.':'Selecione o trabalhador para ver atalhos.';
    repeat.hidden=true;
  }
  const ids=frequentEpis(companyId,workerId);
  chips.innerHTML=ids.length?ids.map(id=>'<button type="button" class="q310-chip" data-qepi="'+esc(id)+'">＋ '+esc(epiName(id))+'</button>').join(''):'<span class="q310-empty">Os EPIs frequentes aparecerão aqui conforme o uso.</span>';
  chips.querySelectorAll('[data-qepi]').forEach(b=>b.onclick=()=>addOneEpi(b.dataset.qepi));

  const hasWorker=!!workerId,hasItems=$$('#deliveryItems .item-epi').some(s=>!!s.value);
  $$('#q310Progress .q310-step').forEach((el,i)=>{
    el.classList.remove('done','current');
    if(i===0)el.classList.add(hasWorker?'done':'current');
    if(i===1)el.classList.add(!hasWorker?'':hasItems?'done':'current');
    if(i===2&&hasWorker&&hasItems)el.classList.add('current');
  });
}
function restoreLastCompany(){
  const view=$('#delivery');if(!view?.classList.contains('active'))return;
  const c=$('#deliveryCompany');if(!c||c.value)return;
  const last=localStorage.getItem(LAST_COMPANY)||'';
  if(last&&[...c.options].some(o=>o.value===last)){c.value=last;c.dispatchEvent(new Event('change',{bubbles:true}))}
}

function installHealthBadge(){
  const top=$('.topbar');if(!top||$('#q310Health'))return;
  const d=document.createElement('span');d.id='q310Health';d.className='q310-health';d.title='Interface operacional';
  d.innerHTML='<i></i><span>Estável</span>';
  const status=$('#epiCloudStatus');(status?.parentElement||top).appendChild(d);
}
function safeUiPass(){
  installStyles();installDeliveryAssistant();installHealthBadge();restoreLastCompany();updateDeliveryAssistant();
  document.body.style.pointerEvents='';
  document.documentElement.style.pointerEvents='';
}
let raf=0;
const observer=new MutationObserver(()=>{if(raf)return;raf=requestAnimationFrame(()=>{raf=0;safeUiPass()})});
function boot(){
  safeUiPass();
  observer.observe(document.body,{childList:true,subtree:true});
  document.addEventListener('click',e=>{
    if(e.target.closest('[data-go="delivery"]'))setTimeout(()=>{restoreLastCompany();$('#deliveryWorkerSearch')?.focus();updateDeliveryAssistant()},90);
  },true);
  window.addEventListener('focus',()=>setTimeout(safeUiPass,60));
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)setTimeout(safeUiPass,60)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();