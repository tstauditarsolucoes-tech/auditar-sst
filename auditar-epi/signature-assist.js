(() => {
  const $ = (s, root=document) => root.querySelector(s);
  let modalCanvas, modalCtx, drawing=false, dirty=false, previousOverflow='';

  function toast(msg){
    const el=$('#toast');
    if(!el) return alert(msg);
    el.textContent=msg; el.classList.add('show');
    setTimeout(()=>el.classList.remove('show'),2400);
  }

  function style(){
    if($('#signatureAssistStyle')) return;
    const el=document.createElement('style');
    el.id='signatureAssistStyle';
    el.textContent=`
      .signature-fast{display:grid;gap:9px;margin-bottom:10px}
      .signature-fast-btn{width:100%;min-height:58px;border:0;border-radius:15px;background:#0f766e;color:#fff;font-size:17px;font-weight:900;box-shadow:0 8px 22px rgba(15,118,110,.18)}
      .signature-fast-status{display:flex;align-items:center;gap:7px;font-size:12px;font-weight:800;color:#7b5d16;background:#fff8e6;border:1px solid #f5dfae;border-radius:12px;padding:9px 11px}
      .signature-fast-status.ok{color:#166534;background:#ecfdf3;border-color:#bbefcc}
      .signature-fullscreen{display:none;position:fixed;inset:0;z-index:9999;background:#eef5f4;padding:env(safe-area-inset-top) 0 env(safe-area-inset-bottom);}
      .signature-fullscreen.open{display:flex;flex-direction:column}
      .signature-modal-head{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:14px 15px;background:#fff;border-bottom:1px solid #dce7e5}
      .signature-modal-head h2{margin:0;font-size:19px}.signature-modal-head p{margin:3px 0 0;color:#647b78;font-size:12px}
      .signature-close{border:0;background:#e8f5f3;color:#0f766e;border-radius:12px;width:44px;height:44px;font-size:21px;font-weight:900}
      .signature-modal-body{flex:1;display:flex;flex-direction:column;min-height:0;padding:13px;gap:10px}
      .signature-instruction{text-align:center;font-size:13px;font-weight:800;color:#536d69}
      #signatureLarge{width:100%;flex:1;min-height:260px;max-height:52vh;background:#fff;border:3px dashed #87aaa6;border-radius:18px;touch-action:none;display:block;box-shadow:inset 0 0 0 1px #eef5f4}
      .signature-modal-actions{display:grid;grid-template-columns:1fr 1fr 1.6fr;gap:8px;padding:0 13px 14px}
      .signature-modal-actions button{border:0;border-radius:14px;min-height:54px;font-weight:900;font-size:14px}
      .signature-cancel,.signature-clear{background:#fff;color:#4d6663;border:1px solid #dce7e5!important}.signature-confirm{background:#0f766e;color:#fff}
      @media(max-width:520px){#signatureLarge{min-height:300px;max-height:none}.signature-modal-body{padding:10px}.signature-modal-actions{grid-template-columns:1fr 1fr}.signature-confirm{grid-column:1/-1;min-height:60px!important;font-size:17px!important}}
    `;
    document.head.appendChild(el);
  }

  function setupUi(){
    const original=$('#signature');
    if(!original || $('#btnSignatureFullscreen')) return;
    style();

    const fast=document.createElement('div');
    fast.className='signature-fast';
    fast.innerHTML=`
      <button id="btnSignatureFullscreen" type="button" class="signature-fast-btn">✍️ Assinar em tela cheia</button>
      <div id="signatureFastStatus" class="signature-fast-status">● Assinatura pendente</div>`;
    original.parentNode.insertBefore(fast, original);

    const modal=document.createElement('div');
    modal.id='signatureFullscreen';
    modal.className='signature-fullscreen';
    modal.setAttribute('role','dialog');
    modal.setAttribute('aria-modal','true');
    modal.innerHTML=`
      <div class="signature-modal-head">
        <div><h2>Assinatura do colaborador</h2><p id="signatureWorkerName">Assine no quadro abaixo</p></div>
        <button type="button" id="signatureClose" class="signature-close" aria-label="Fechar">×</button>
      </div>
      <div class="signature-modal-body">
        <div class="signature-instruction">✍️ Assine com o dedo dentro do quadro</div>
        <canvas id="signatureLarge"></canvas>
      </div>
      <div class="signature-modal-actions">
        <button type="button" id="signatureCancel" class="signature-cancel">Cancelar</button>
        <button type="button" id="signatureClearLarge" class="signature-clear">Limpar</button>
        <button type="button" id="signatureConfirm" class="signature-confirm">✓ Confirmar assinatura</button>
      </div>`;
    document.body.appendChild(modal);

    modalCanvas=$('#signatureLarge');
    modalCtx=modalCanvas.getContext('2d');

    $('#btnSignatureFullscreen').addEventListener('click',openModal);
    $('#signatureClose').addEventListener('click',closeModal);
    $('#signatureCancel').addEventListener('click',closeModal);
    $('#signatureClearLarge').addEventListener('click',clearLarge);
    $('#signatureConfirm').addEventListener('click',confirmSignature);

    modalCanvas.addEventListener('pointerdown',start);
    modalCanvas.addEventListener('pointermove',move);
    ['pointerup','pointerleave','pointercancel'].forEach(n=>modalCanvas.addEventListener(n,end));

    $('#btnClearSignature')?.addEventListener('click',()=>setStatus(false));
    document.addEventListener('click',e=>{
      if(e.target.closest('[data-go="delivery"]')) setTimeout(()=>setStatus(false),20);
    });
  }

  function workerLabel(){
    const sel=$('#deliveryWorker');
    const text=sel?.selectedOptions?.[0]?.textContent?.trim()||'';
    return sel?.value ? text : 'Colaborador ainda não selecionado';
  }

  function openModal(){
    const modal=$('#signatureFullscreen');
    if(!modal) return;
    $('#signatureWorkerName').textContent=workerLabel();
    previousOverflow=document.body.style.overflow;
    document.body.style.overflow='hidden';
    modal.classList.add('open');
    dirty=false;
    requestAnimationFrame(()=>{ resizeLarge(); clearLarge(false); });
  }

  function closeModal(){
    $('#signatureFullscreen')?.classList.remove('open');
    document.body.style.overflow=previousOverflow;
    drawing=false;
  }

  function resizeLarge(){
    if(!modalCanvas) return;
    const rect=modalCanvas.getBoundingClientRect();
    const ratio=Math.max(window.devicePixelRatio||1,1);
    modalCanvas.width=Math.max(1,Math.floor(rect.width*ratio));
    modalCanvas.height=Math.max(1,Math.floor(rect.height*ratio));
    modalCtx.setTransform(ratio,0,0,ratio,0,0);
    modalCtx.lineCap='round'; modalCtx.lineJoin='round'; modalCtx.lineWidth=3;
    modalCtx.strokeStyle='#173d39';
  }

  function point(ev){
    const r=modalCanvas.getBoundingClientRect();
    return {x:ev.clientX-r.left,y:ev.clientY-r.top};
  }
  function start(ev){ ev.preventDefault(); drawing=true; const p=point(ev); modalCtx.beginPath(); modalCtx.moveTo(p.x,p.y); }
  function move(ev){ if(!drawing) return; ev.preventDefault(); const p=point(ev); modalCtx.lineTo(p.x,p.y); modalCtx.stroke(); dirty=true; }
  function end(){ drawing=false; }

  function clearLarge(mark=true){
    if(!modalCanvas) return;
    modalCtx.save(); modalCtx.setTransform(1,0,0,1,0,0);
    modalCtx.clearRect(0,0,modalCanvas.width,modalCanvas.height); modalCtx.restore();
    dirty=false;
    if(mark) toast('Assinatura limpa.');
  }

  function markOriginalDirty(original){
    const r=original.getBoundingClientRect();
    const E=window.PointerEvent || window.MouseEvent;
    const base={bubbles:true,clientX:r.left+2,clientY:r.top+2,pointerId:1};
    try{
      original.dispatchEvent(new E('pointerdown',base));
      original.dispatchEvent(new E('pointermove',{...base,clientX:r.left+3,clientY:r.top+3}));
      original.dispatchEvent(new E('pointerup',{...base,clientX:r.left+3,clientY:r.top+3}));
    }catch(_){
      original.dispatchEvent(new Event('pointerdown',{bubbles:true}));
      original.dispatchEvent(new Event('pointermove',{bubbles:true}));
      original.dispatchEvent(new Event('pointerup',{bubbles:true}));
    }
  }

  function confirmSignature(){
    if(!dirty) return toast('Peça ao colaborador para assinar primeiro.');
    const original=$('#signature');
    if(!original) return;
    const octx=original.getContext('2d');
    octx.save(); octx.setTransform(1,0,0,1,0,0);
    octx.clearRect(0,0,original.width,original.height);
    octx.drawImage(modalCanvas,0,0,original.width,original.height);
    octx.restore();
    markOriginalDirty(original);
    setStatus(true);
    closeModal();
    toast('Assinatura confirmada.');
    setTimeout(()=>$('#btnSaveDelivery')?.scrollIntoView({behavior:'smooth',block:'center'}),100);
  }

  function setStatus(ok){
    const status=$('#signatureFastStatus');
    if(!status) return;
    status.classList.toggle('ok',!!ok);
    status.textContent=ok?'✓ Assinatura confirmada':'● Assinatura pendente';
    const btn=$('#btnSignatureFullscreen');
    if(btn) btn.textContent=ok?'✍️ Refazer assinatura':'✍️ Assinar em tela cheia';
  }

  document.addEventListener('DOMContentLoaded',setupUi);
})();
