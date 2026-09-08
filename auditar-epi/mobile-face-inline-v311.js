(() => {
  'use strict';
  const APP_KEY='auditarEpiV1';
  const $=(s,r=document)=>r.querySelector(s);

  function readApp(){try{return {workers:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')};}catch{return {workers:[]};}}
  function selectedWorker(){const id=$('#deliveryWorker')?.value||'';return (readApp().workers||[]).find(w=>w.id===id)||null;}
  function hasFace(w){return !!w?.biometric?.embedding?.length;}

  function injectStyle(){
    if($('#mobileFaceInline311Style'))return;
    const s=document.createElement('style');s.id='mobileFaceInline311Style';s.textContent=`
      .v311-inline-face{display:none;margin:10px 0 0;padding:11px;border:1px solid #f0d7a0;border-radius:13px;background:#fff8e8}
      .v311-inline-face.show{display:block}
      .v311-inline-face b{display:block;color:#765412;font-size:12px;margin-bottom:6px}
      .v311-inline-face p{margin:0 0 9px;color:#806a39;font-size:11px;line-height:1.4}
      .v311-inline-face button{width:100%;min-height:50px;border:0;border-radius:13px;background:#0f766e;color:#fff;font-weight:950;font-size:14px}
      .v311-face-ok{display:none;margin:10px 0 0;padding:9px 11px;border:1px solid #c9ead3;border-radius:12px;background:#ecfdf3;color:#166534;font-size:11px;font-weight:850}
      .v311-face-ok.show{display:block}
    `;document.head.appendChild(s);
  }

  function ensureUi(){
    const panel=$('#bioDeliveryPanel');
    if(!panel||$('#v311InlineFace'))return;
    const box=document.createElement('div');box.id='v311InlineFace';box.className='v311-inline-face';
    box.innerHTML='<b>Este trabalhador ainda não tem facial cadastrada.</b><p>Cadastre agora e continue a entrega sem sair desta tela.</p><button id="v311EnrollFaceNow" type="button">🙂 Cadastrar rosto agora</button>';
    panel.insertBefore(box,$('#bioVerifyNow')||panel.firstChild);
    const ok=document.createElement('div');ok.id='v311FaceOk';ok.className='v311-face-ok';ok.textContent='✓ Facial já cadastrada. Use “Verificar rosto agora”.';panel.insertBefore(ok,$('#bioVerifyStatus')||null);
    $('#v311EnrollFaceNow').addEventListener('click',()=>{
      const w=selectedWorker();if(!w)return;
      // O módulo biométrico já trata qualquer elemento com data-bio-worker como cadastro facial.
      const proxy=document.createElement('button');proxy.type='button';proxy.dataset.bioWorker=w.id;proxy.style.display='none';document.body.appendChild(proxy);proxy.click();proxy.remove();
    });
  }

  function refresh(){
    ensureUi();
    const w=selectedWorker(),missing=!!w&&!hasFace(w);
    $('#v311InlineFace')?.classList.toggle('show',missing);
    $('#v311FaceOk')?.classList.toggle('show',!!w&&hasFace(w));
    const verify=$('#bioVerifyNow');if(verify)verify.style.display=missing?'none':'';
    const status=$('#bioVerifyStatus');if(status&&missing){status.className='bio-status';status.textContent='Cadastre o rosto acima para usar a confirmação facial.';}
  }

  function cleanWrongQuickActions(){
    // Remove atalhos que não eram o pedido do usuário nesta tela.
    $('#v31QuickBox')?.remove();
    $('#v31DeliveryShortcuts')?.remove();
  }

  function boot(){
    injectStyle();cleanWrongQuickActions();ensureUi();refresh();
    $('#deliveryWorker')?.addEventListener('change',()=>setTimeout(refresh,20));
    document.addEventListener('auditar-epi-data-changed',()=>setTimeout(refresh,60));
    document.addEventListener('auditar-epi-state-refreshed',()=>setTimeout(refresh,60));
    document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(()=>{cleanWrongQuickActions();ensureUi();refresh();},120));
    new MutationObserver(()=>{cleanWrongQuickActions();ensureUi();refresh();}).observe(document.body,{childList:true,subtree:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
