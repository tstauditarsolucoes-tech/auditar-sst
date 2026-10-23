(()=>{
'use strict';
/* Restauracao visual v3.8.5: nao escreve dados, estoque nem credenciais. */
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
function style(){
 if($('#epi385CardStyle'))return;
 const e=document.createElement('style');e.id='epi385CardStyle';
 e.textContent="#workerList .list-item{max-width:100%;min-width:0;overflow:visible}\n#workerList .list-main{min-width:0;width:100%}\n#workerList .list-main b,#workerList .list-main small{white-space:normal;overflow-wrap:anywhere}\n#workerList .list-actions{display:flex;flex-wrap:wrap;align-items:center;gap:8px;width:100%;min-width:0;flex-shrink:1}\n#workerList .list-actions .tiny,#workerList .list-actions .worker-portal-share{min-height:43px;border-radius:11px;padding:9px 12px;font-size:13px;font-weight:800;line-height:1.2}\n#workerList .list-actions [data-ficha382-worker]{order:0;background:#0d8370;color:#fff}\n#workerList .list-actions [data-ux-worker]{order:1;background:#e4f5f0;color:#0a6d5b}\n#workerList .list-actions [data-bio-worker]{order:2;background:#e9f7f4;color:#0c7563}\n#workerList .list-actions [data-worker-portal-share]{order:3;background:#e4f3f0;color:#16685d}\n#workerList .list-actions .f382-admin-actions{order:7;align-self:center}\n#workerList .list-actions .f382-admin-actions summary{padding:11px 6px;cursor:pointer;color:#526e68;font-size:13px;font-weight:700}\n#workerList .list-actions .f382-admin-actions [data-del-worker]{background:#fff0ed;color:#982c25;min-height:44px}\n#workerList .list-actions button{max-width:100%;white-space:normal;overflow-wrap:anywhere}\n@media(max-width:420px){#workerList .list-actions{gap:7px}#workerList .list-actions [data-ficha382-worker],#workerList .list-actions [data-ux-worker],#workerList .list-actions [data-bio-worker],#workerList .list-actions [data-worker-portal-share]{flex:1 1 calc(50% - 5px)}#workerList .list-actions .f382-admin-actions{flex:1 1 100%;text-align:right}}";
 document.head.appendChild(e);
}
function update(){
 const list=$('#workerList');if(!list)return;
 $$('.list-item',list).forEach(card=>{
  const del=$('[data-del-worker]',card);
  if(!del)return;
  const actions=$('.list-actions',card);if(!actions)return;
  const face=$('[data-bio-worker]',card),portal=$('[data-worker-portal-share]',card);
  const fiche=$('[data-ficha382-worker]',card),summary=$('[data-ux-worker]',card);
  if(fiche)fiche.textContent='📑 Ficha completa';
  if(summary)summary.textContent='Resumo 360°';
  if(face)face.setAttribute('aria-label',face.textContent?.trim()||'Cadastrar biometria facial');
  if(portal)portal.setAttribute('aria-label','Portal do Trabalhador');
  if(!del.closest('.f382-admin-actions')){
   let more=$('.f382-admin-actions',actions);
   if(!more){
    more=document.createElement('details');more.className='f382-admin-actions';
    const label=document.createElement('summary');label.textContent='Mais opções';more.appendChild(label);actions.appendChild(more);
   }
   more.appendChild(del);
  }
 });
}
function boot(){
 style();update();
 const list=$('#workerList');
 if(list){
  let scheduled=false;
  new MutationObserver(()=>{
   if(scheduled)return;scheduled=true;
   requestAnimationFrame(()=>{scheduled=false;update()});
  }).observe(list,{childList:true});
 }
 document.addEventListener('gestao-epi-sync-applied',update);
 document.addEventListener('auditar-epi-data-changed',update);
 [250,900,1900].forEach(ms=>setTimeout(update,ms));
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();