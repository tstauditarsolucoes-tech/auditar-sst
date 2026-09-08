(() => {
  'use strict';
  const APP_KEY='auditarEpiV1';
  const $=(s,r=document)=>r.querySelector(s);
  let rawCache='';
  let workersCache=[];
  let timer=null;

  function workers(){
    const raw=localStorage.getItem(APP_KEY)||'{}';
    if(raw===rawCache)return workersCache;
    try{workersCache=(JSON.parse(raw)?.workers||[]);}catch{workersCache=[];}
    rawCache=raw;
    return workersCache;
  }
  function selectedWorker(){const id=$('#deliveryWorker')?.value||'';return id?workers().find(w=>w.id===id)||null:null;}
  function hasFace(w){return !!w?.biometric?.embedding?.length;}
  function schedule(ms=25){clearTimeout(timer);timer=setTimeout(refresh,ms);}

  function injectStyle(){
    if($('#mobileFaceInline311Style'))return;
    const s=document.createElement('style');s.id='mobileFaceInline311Style';s.textContent=`
      .v311-inline-face{display:none;margin:10px 0 0;padding:11px;border:1px solid #f0d7a0;border-radius:13px;background:#fff8e8}
      .v311-inline-face.show{display:block}
      .v311-inline-face b{display:block;color:#765412;font-size:12px;margin-bottom:6px}
      .v311-inline-face p{margin:0 0 9px;color:#806a39;font-size:11px;line-height:1.4}
      .v311-inline-face button{width:100%;min-height:50px;border:0;border-radius:13px;background:#0f766e;color:#fff;font-weight:950;font-size:14px}
    `;document.head.appendChild(s);
  }

  function ensureUi(){
    const panel=$('#bioDeliveryPanel');if(!panel||$('#v311InlineFace'))return;
    const box=document.createElement('div');box.id='v311InlineFace';box.className='v311-inline-face';
    box.innerHTML='<b>Este trabalhador ainda não tem facial cadastrada.</b><p>Cadastre agora e continue a entrega sem sair desta tela.</p><button id="v311EnrollFaceNow" type="button">🙂 Cadastrar rosto agora</button>';
    panel.insertBefore(box,$('#bioVerifyNow')||panel.firstChild);
    $('#v311EnrollFaceNow')?.addEventListener('click',()=>{
      const w=selectedWorker();if(!w)return;
      const proxy=document.createElement('button');proxy.type='button';proxy.dataset.bioWorker=w.id;proxy.hidden=true;document.body.appendChild(proxy);proxy.click();proxy.remove();
    });
  }

  function refresh(){
    ensureUi();
    const w=selectedWorker();const missing=!!w&&!hasFace(w);
    $('#v311InlineFace')?.classList.toggle('show',missing);
    const verify=$('#bioVerifyNow');if(verify)verify.style.display=missing?'none':'';
    const status=$('#bioVerifyStatus');
    if(status&&missing){status.className='bio-status';status.textContent='Cadastre o rosto acima para usar a confirmação facial.';}
    else if(status&&!w){status.className='bio-status';status.textContent='Selecione um colaborador para usar a biometria facial.';}
  }

  function boot(){
    injectStyle();$('#v31QuickBox')?.remove();$('#v31DeliveryShortcuts')?.remove();ensureUi();refresh();
    $('#deliveryWorker')?.addEventListener('change',()=>schedule(10));
    document.addEventListener('auditar-epi-data-changed',()=>{rawCache='';schedule(70);});
    document.addEventListener('auditar-epi-state-refreshed',()=>{rawCache='';schedule(70);});
    document.addEventListener('gestao-epi-auth-ready',()=>{rawCache='';schedule(120);});
    document.addEventListener('click',e=>{if(e.target.closest('[data-go="delivery"],#bioUseFace'))schedule(40);},{passive:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
