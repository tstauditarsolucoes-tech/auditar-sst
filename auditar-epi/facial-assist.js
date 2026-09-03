(() => {
  const APP_KEY='auditarEpiV1';
  const $=(s,r=document)=>r.querySelector(s);
  let facialMode=false;
  let facialReady=false;
  let facialCapturedAt='';
  let facialData='';

  function toast(msg){
    const el=$('#toast');
    if(!el) return alert(msg);
    el.textContent=msg;
    el.classList.add('show');
    setTimeout(()=>el.classList.remove('show'),2400);
  }

  function style(){
    if($('#facialAssistStyle')) return;
    const el=document.createElement('style');
    el.id='facialAssistStyle';
    el.textContent=`
      .confirm-method{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:12px 0}
      .confirm-method button{min-height:54px;border:1px solid #cbdad8;background:#fff;color:#355b57;border-radius:14px;font-weight:900;font-size:14px;padding:10px}
      .confirm-method button.active{background:#e8f5f3;border-color:#0f766e;color:#0f766e;box-shadow:0 0 0 2px rgba(15,118,110,.07)}
      .facial-panel{display:none;border:1px solid #d7e6e3;background:#f8fbfb;border-radius:16px;padding:14px;margin-top:10px}
      .facial-panel.open{display:block}
      .facial-panel h4{margin:0 0 4px;font-size:16px}.facial-panel p{margin:0 0 10px;color:#607a76;font-size:12px;line-height:1.45}
      .facial-notice{display:flex;gap:9px;align-items:flex-start;background:#fff;border:1px solid #e1e9e8;border-radius:12px;padding:10px;font-size:12px;color:#4f6865;margin-bottom:10px}
      .facial-notice input{margin-top:2px;transform:scale(1.2)}
      .facial-camera{width:100%;min-height:56px;border:0;border-radius:14px;background:#0f766e;color:#fff;font-size:16px;font-weight:900}
      .facial-preview{display:none;margin-top:12px;text-align:center}.facial-preview.show{display:block}
      .facial-preview img{width:min(220px,72vw);max-height:260px;object-fit:cover;border-radius:16px;border:3px solid #fff;box-shadow:0 8px 24px rgba(15,118,110,.18)}
      .facial-ok{margin-top:9px;display:inline-flex;align-items:center;gap:6px;background:#ecfdf3;color:#166534;border-radius:999px;padding:7px 11px;font-size:12px;font-weight:900}
      .facial-retry{margin-top:8px;border:0;background:transparent;color:#0f766e;font-weight:900;padding:8px}
      .facial-mode .signature-fast,.facial-mode #signature,.facial-mode .signature-hint,.facial-mode #btnClearSignature{display:none!important}
      .facial-proof-note{margin-top:12px;padding:10px 12px;border-radius:10px;background:#eef8f6;color:#315d57;font-size:11px;line-height:1.4}
      @media(max-width:520px){.confirm-method{grid-template-columns:1fr}.confirm-method button{min-height:58px}}
    `;
    document.head.appendChild(el);
  }

  function setup(){
    const signature=$('#signature');
    if(!signature || $('#facialConfirmPanel')) return;
    style();
    const card=signature.closest('.card');
    if(!card) return;

    const title=card.querySelector('.section-title');
    if(title){
      const h=title.querySelector('h3');
      const p=title.querySelector('p');
      if(h) h.textContent='Confirmação do colaborador';
      if(p) p.textContent='Escolha assinatura na tela ou confirmação facial.';
    }

    const chooser=document.createElement('div');
    chooser.className='confirm-method';
    chooser.innerHTML=`
      <button id="btnConfirmSignature" type="button" class="active">✍️ Assinar na tela</button>
      <button id="btnConfirmFace" type="button">📷 Confirmação facial</button>`;
    const fast=card.querySelector('.signature-fast');
    (fast||signature).parentNode.insertBefore(chooser,fast||signature);

    const panel=document.createElement('div');
    panel.id='facialConfirmPanel';
    panel.className='facial-panel';
    panel.innerHTML=`
      <h4>📷 Foto do colaborador</h4>
      <p>Faça a foto no momento da entrega. Ela ficará vinculada ao comprovante.</p>
      <label class="facial-notice"><input id="facialNoticeCheck" type="checkbox"><span>O colaborador foi informado de que a foto será registrada como confirmação desta entrega de EPI.</span></label>
      <input id="facialCameraInput" type="file" accept="image/*" capture="user" hidden>
      <button id="btnFacialCamera" type="button" class="facial-camera">📷 Tirar foto agora</button>
      <div id="facialPreview" class="facial-preview"><img id="facialPreviewImg" alt="Foto de confirmação"><div><span class="facial-ok">✓ Confirmação facial pronta</span></div><button id="btnFacialRetry" type="button" class="facial-retry">↻ Refazer foto</button></div>`;
    card.appendChild(panel);

    $('#btnConfirmSignature').addEventListener('click',()=>setMode(false));
    $('#btnConfirmFace').addEventListener('click',()=>setMode(true));
    $('#btnFacialCamera').addEventListener('click',openCamera);
    $('#btnFacialRetry').addEventListener('click',openCamera);
    $('#facialCameraInput').addEventListener('change',handlePhoto);

    const save=$('#btnSaveDelivery');
    if(save){
      save.addEventListener('click',guardFacial,true);
      save.addEventListener('click',afterSave);
    }

    document.addEventListener('click',e=>{
      if(e.target.closest('[data-go="delivery"]')) setTimeout(resetFacial,30);
      const r=e.target.closest('[data-receipt]');
      if(r) setTimeout(()=>patchReceipt(r.dataset.receipt),50);
    });

    const hero=document.querySelector('#home .hero-card h1');
    if(hero && /assinatura na tela/i.test(hero.textContent)) hero.textContent='Entrega rápida, assinatura ou confirmação facial e sincronização com a Gestão.';
  }

  function setMode(face){
    facialMode=!!face;
    const card=$('#signature')?.closest('.card');
    card?.classList.toggle('facial-mode',facialMode);
    $('#facialConfirmPanel')?.classList.toggle('open',facialMode);
    $('#btnConfirmFace')?.classList.toggle('active',facialMode);
    $('#btnConfirmSignature')?.classList.toggle('active',!facialMode);
    if(facialMode){
      $('#btnClearSignature')?.click();
      if(!facialReady) setTimeout(()=>$('#btnFacialCamera')?.scrollIntoView({behavior:'smooth',block:'center'}),80);
    }else{
      facialReady=false;facialCapturedAt='';facialData='';
      const input=$('#facialCameraInput');if(input)input.value='';
      $('#facialPreview')?.classList.remove('show');
    }
  }

  function openCamera(){
    if(!$('#facialNoticeCheck')?.checked) return toast('Marque que o colaborador foi informado sobre a foto.');
    $('#facialCameraInput')?.click();
  }

  function handlePhoto(e){
    const file=e.target.files?.[0];
    if(!file) return;
    if(!file.type.startsWith('image/')) return toast('Selecione uma foto válida.');
    const reader=new FileReader();
    reader.onload=()=>compressPhoto(String(reader.result||''));
    reader.readAsDataURL(file);
  }

  function compressPhoto(src){
    const img=new Image();
    img.onload=()=>{
      const maxW=360,maxH=480;
      const scale=Math.min(1,maxW/img.width,maxH/img.height);
      const w=Math.max(1,Math.round(img.width*scale)),h=Math.max(1,Math.round(img.height*scale));
      const c=document.createElement('canvas');c.width=w;c.height=h;
      c.getContext('2d').drawImage(img,0,0,w,h);
      facialData=c.toDataURL('image/jpeg',0.68);
      facialCapturedAt=new Date().toISOString();
      facialReady=true;
      const preview=$('#facialPreviewImg');if(preview)preview.src=facialData;
      $('#facialPreview')?.classList.add('show');
      copyFaceToSignature();
      toast('Confirmação facial pronta.');
    };
    img.onerror=()=>toast('Não foi possível abrir a foto.');
    img.src=src;
  }

  function markSignatureDirty(canvas){
    const rect=canvas.getBoundingClientRect();
    const E=window.PointerEvent||window.MouseEvent;
    try{
      canvas.dispatchEvent(new E('pointerdown',{bubbles:true,clientX:rect.left+2,clientY:rect.top+2,pointerId:77}));
      canvas.dispatchEvent(new E('pointermove',{bubbles:true,clientX:rect.left+3,clientY:rect.top+3,pointerId:77}));
      canvas.dispatchEvent(new E('pointerup',{bubbles:true,clientX:rect.left+3,clientY:rect.top+3,pointerId:77}));
    }catch(_){
      canvas.dispatchEvent(new Event('pointerdown',{bubbles:true}));
      canvas.dispatchEvent(new Event('pointermove',{bubbles:true}));
      canvas.dispatchEvent(new Event('pointerup',{bubbles:true}));
    }
  }

  function copyFaceToSignature(){
    const canvas=$('#signature');
    if(!canvas||!facialData) return;
    markSignatureDirty(canvas);
    const img=new Image();
    img.onload=()=>{
      const ctx=canvas.getContext('2d');
      ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,canvas.width,canvas.height);
      ctx.fillStyle='#ffffff';ctx.fillRect(0,0,canvas.width,canvas.height);
      const scale=Math.max(canvas.width/img.width,canvas.height/img.height);
      const dw=img.width*scale,dh=img.height*scale;
      ctx.drawImage(img,(canvas.width-dw)/2,(canvas.height-dh)/2,dw,dh);
      ctx.restore();
    };
    img.src=facialData;
  }

  function guardFacial(e){
    if(!facialMode) return;
    if(!facialReady){
      e.preventDefault();e.stopImmediatePropagation();
      toast('Tire a foto do colaborador antes de finalizar.');
      return;
    }
    copyFaceToSignature();
  }

  function afterSave(){
    if(!facialMode||!facialReady) return;
    const capturedAt=facialCapturedAt;
    setTimeout(()=>{
      try{
        const root=JSON.parse(localStorage.getItem(APP_KEY)||'{}');
        const rows=Array.isArray(root.deliveries)?root.deliveries:[];
        const d=rows[0];
        if(d && Date.now()-new Date(d.createdAt||0).getTime()<15000){
          d.confirmationMethod='facial';
          d.facialCapturedAt=capturedAt;
          d.facialNoticeRecorded=true;
          d.updatedAt=new Date().toISOString();
          localStorage.setItem(APP_KEY,JSON.stringify(root));
          sessionStorage.setItem('auditarEpiLastFacialDelivery',d.id);
          patchReceipt(d.id);
        }
      }catch(_){ }
      resetFacial();
    },80);
  }

  function patchReceipt(id){
    try{
      const root=JSON.parse(localStorage.getItem(APP_KEY)||'{}');
      const d=(root.deliveries||[]).find(x=>x.id===id);
      if(!d||d.confirmationMethod!=='facial') return;
      const content=$('#receiptContent');if(!content)return;
      const line=content.querySelector('.sign-line');
      if(line){
        const name=(line.innerHTML.split('<br>')[0]||'Colaborador');
        line.innerHTML=`${name}<br>Confirmação facial do colaborador`;
      }
      if(!content.querySelector('.facial-proof-note')){
        const sign=content.querySelector('.receipt-sign');
        sign?.insertAdjacentHTML('afterend',`<div class="facial-proof-note"><b>📷 Confirmação facial</b><br>Foto registrada no momento da entrega${d.facialCapturedAt?' em '+new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(d.facialCapturedAt)):''}.</div>`);
      }
    }catch(_){ }
  }

  function resetFacial(){
    facialMode=false;facialReady=false;facialCapturedAt='';facialData='';
    const card=$('#signature')?.closest('.card');card?.classList.remove('facial-mode');
    $('#facialConfirmPanel')?.classList.remove('open');
    $('#btnConfirmFace')?.classList.remove('active');$('#btnConfirmSignature')?.classList.add('active');
    const check=$('#facialNoticeCheck');if(check)check.checked=false;
    const input=$('#facialCameraInput');if(input)input.value='';
    $('#facialPreview')?.classList.remove('show');
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',setup);
  else setup();
})();