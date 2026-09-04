(() => {
  const APP_KEY='auditarEpiV1';
  const BULK_KEY='gestaoEpiBulkDeliveryV1';
  const $=(s,r=document)=>r.querySelector(s);
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function read(key){try{return JSON.parse((key===BULK_KEY?sessionStorage:localStorage).getItem(key)||'null');}catch{return null;}}
  function currentWorker(){
    const id=$('#deliveryWorker')?.value||'';
    const root=read(APP_KEY)||{};
    return (root.workers||[]).find(w=>w.id===id)||null;
  }
  function bulkInfo(){
    const b=read(BULK_KEY);
    if(!b||!Array.isArray(b.ids)||!b.ids.length)return null;
    return {current:Number(b.index||0)+1,total:b.ids.length};
  }

  function ensure(){
    const body=$('#signatureFullscreen .signature-modal-body');if(!body||$('#signatureWorkerBanner'))return;
    const style=document.createElement('style');style.id='signatureWorkerBannerStyle';style.textContent=`
      .signature-worker-banner{flex:0 0 auto;text-align:center;background:#dff4f0;border:2px solid #58a89e;border-radius:14px;padding:8px 12px;color:#173d39}
      .signature-worker-banner small{display:block;font-size:10px;font-weight:900;letter-spacing:.08em;color:#39756e;text-transform:uppercase;margin-bottom:2px}
      .signature-worker-banner strong{display:block;font-size:clamp(18px,3.2vw,28px);line-height:1.05;font-weight:950;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .signature-worker-banner span{display:block;margin-top:3px;font-size:11px;font-weight:850;color:#4f6f6b}
      @media(orientation:landscape){.signature-worker-banner{padding:6px 10px}.signature-worker-banner strong{font-size:clamp(17px,2.5vw,24px)}}
    `;document.head.appendChild(style);
    const banner=document.createElement('div');banner.id='signatureWorkerBanner';banner.className='signature-worker-banner';body.insertBefore(banner,body.firstChild);update();
  }

  function update(){
    ensure();const box=$('#signatureWorkerBanner');if(!box)return;
    const w=currentWorker(),bulk=bulkInfo();
    const name=w?.name||$('#deliveryWorker')?.selectedOptions?.[0]?.textContent?.split(' • ')[0]?.trim()||'COLABORADOR NÃO SELECIONADO';
    const extra=[w?.reg?`Matrícula: ${w.reg}`:'',bulk?`Entrega em lote • ${bulk.current} de ${bulk.total}`:''].filter(Boolean).join(' • ');
    box.innerHTML=`<small>Assinatura de</small><strong>${esc(name)}</strong>${extra?`<span>${esc(extra)}</span>`:''}`;
    const old=$('#signatureWorkerName');if(old)old.textContent='Confira o nome antes de assinar';
  }

  function init(){
    const tryBind=()=>{
      ensure();
      $('#deliveryWorker')?.addEventListener('change',update);
      $('#btnSignatureFullscreen')?.addEventListener('click',()=>setTimeout(update,20),true);
      document.addEventListener('click',e=>{if(e.target.closest('#bioUseSign'))setTimeout(update,20);},true);
      const modal=$('#signatureFullscreen');if(modal)new MutationObserver(()=>{if(modal.classList.contains('open'))update();}).observe(modal,{attributes:true,attributeFilter:['class']});
    };
    tryBind();setTimeout(tryBind,250);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();