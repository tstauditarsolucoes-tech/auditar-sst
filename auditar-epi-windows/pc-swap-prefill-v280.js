(()=>{
  'use strict';
  const KEY='gestaoEpiSwapDraftV350';
  const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
  function toast(msg){const e=$('#toast');if(!e)return;e.textContent=msg;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2600);}
  function readDraft(){try{return JSON.parse(localStorage.getItem(KEY)||'null');}catch{return null;}}
  function applyDraft(){
    const d=readDraft();if(!d||!d.workerId||!d.epiId)return;
    const company=$('#pcDeliveryCompany'),search=$('#pcDeliverySearch'),worker=$('#pcDeliveryWorker'),reason=$('#pcDeliveryReason');
    if(!company||!worker)return;
    company.value=d.companyId||'';company.dispatchEvent(new Event('change',{bubbles:true}));
    setTimeout(()=>{
      const cache=(()=>{try{return JSON.parse(localStorage.getItem('auditarEpiGestaoCacheV1')||'{}');}catch{return {};}})();
      const w=cache?.app?.workers?.find?.(x=>x.id===d.workerId);
      if(search&&w?.name){search.value=w.name;search.dispatchEvent(new Event('input',{bubbles:true}));}
      setTimeout(()=>{
        worker.value=d.workerId;worker.dispatchEvent(new Event('change',{bubbles:true}));
        if(reason){const value=d.reason||'Substituição por vencimento previsto';if(![...reason.options].some(o=>o.value===value)){const o=document.createElement('option');o.value=o.textContent=value;reason.appendChild(o);}reason.value=value;}
        $('#pcAddDeliveryItem')?.click();
        setTimeout(()=>{const sel=$$('.pc-delivery-item .pc-item-epi').at(-1);if(sel){sel.value=d.epiId;sel.dispatchEvent(new Event('change',{bubbles:true}));}localStorage.removeItem(KEY);toast('Troca preparada com trabalhador e EPI preenchidos.');},100);
      },120);
    },120);
  }
  document.addEventListener('click',e=>{if(e.target.closest?.('.sidebar .nav[data-view="newDeliveryPc"],[data-v260-go="newDeliveryPc"],[data-pc-go="newDeliveryPc"]'))setTimeout(applyDraft,180);},true);
  document.addEventListener('DOMContentLoaded',()=>setTimeout(applyDraft,700),{once:true});
})();
