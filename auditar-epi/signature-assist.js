(() => {
  const $ = (s, root=document) => root.querySelector(s);
  let modalCanvas, modalCtx, drawing=false, dirty=false, previousOverflow='';
  let orientationPlugin=null;

  function toast(msg){
    const el=$('#toast');
    if(!el) return alert(msg);
    el.textContent=msg; el.classList.add('show');
    setTimeout(()=>el.classList.remove('show'),2400);
  }

  function getOrientationPlugin(){
    if(orientationPlugin) return orientationPlugin;
    try{
      if(window.Capacitor?.Plugins?.ScreenOrientation){
        orientationPlugin=window.Capacitor.Plugins.ScreenOrientation;
      }else if(window.Capacitor?.registerPlugin){
        orientationPlugin=window.Capacitor.registerPlugin('ScreenOrientation');
      }
    }catch(_){ orientationPlugin=null; }
    return orientationPlugin;
  }

  async function landscape(){
    try{
      const plugin=getOrientationPlugin();
      if(plugin?.lock){ await plugin.lock({orientation:'landscape'}); return true; }
    }catch(_){ }
    try{
      if(screen.orientation?.lock){ await screen.orientation.lock('landscape'); return true; }
    }catch(_){ }
    return false;
  }

  async function portrait(){
    try{
      const plugin=getOrientationPlugin();
      if(plugin?.lock){ await plugin.lock({orientation:'portrait'}); return; }
    }catch(_){ }
    try{ screen.orientation?.unlock?.(); }catch(_){ }
  }

  function style(){
    if($('#signatureAssistStyle')) return;
    const el=document.createElement('style');
    el.id='signatureAssistStyle';
    el.textContent=`
      .signature-fast{display:grid;gap:9px;margin-bottom:10px}
      .signature-fast-btn{width:100%;min-height:58px;border:0;border-radius:15px;background:#0f766e;color:#fff;font-size:17px;font-weight:900;box-shadow:0 8px 22px rgba(15,118,110,.18)}
      .bio-methods + .signature-fast .signature-fast-btn{display:none!important}
      .signature-fast-status{display:flex;align-items:center;gap:7px;font-size:12px;font-weight:800;color:#7b5d16;background:#fff8e6;border:1px solid #f5dfae;border-radius:12px;padding:9px 11px}
      .signature-fast-status.ok{color:#166534;background:#ecfdf3;border-color:#bbefcc}
      .signature-preview-label{margin:7px 0 6px;font-size:11px;font-weight:850;color:#6a807d;text-align:center}
      #signature{pointer-events:none!important;touch-action:none!important;user-select:none!important;background:#fff;cursor:default}
      #btnClearSignature{display:none!important}
      .signature-fullscreen{display:none;position:fixed;inset:0;z-index:9999;background:#eef5f4;padding:0;}
      .signature-fullscreen.open{display:flex;flex-direction:column}
      .signature-modal-head{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 14px;background:#fff;border-bottom:1px solid #dce7e5;min-height:58px}
      .signature-modal-head h2{margin:0;font-size:18px}.signature-modal-head p{margin:2px 0 0;color:#647b78;font-size:11px}
      .signature-close{border:0;background:#e8f5f3;color:#0f766e;border-radius:11px;width:42px;height:42px;font-size:21px;font-weight:900}
      .signature-modal-body{flex:1;display:flex;flex-direction:column;min-height:0;padding:8px 12px;gap:6px}
      .signature-instruction{text-align:center;font-size:12px;font-weight:850;color:#536d69}
      #signatureLarge{width:100%;height:100%;flex:1;min-height:150px;background:#fff;border:3px dashed #87aaa6;border-radius:16px;touch-action:none;display:block;box-shadow:inset 0 0 0 1px #eef5f4}
      .signature-modal-actions{display:grid;grid-template-columns:1fr 1fr 1.7fr;gap:8px;padding:6px 12px 10px;background:#eef5f4}
      .signature-modal-actions button{border:0;border-radius:13px;min-height:48px;font-weight:900;font-size:14px}
      .signature-cancel,.signature-clear{background:#fff;color:#4d6663;border:1px solid #dce7e5!important}.signature-confirm{background:#0f766e;color:#fff}
      .signature-orientation-note{display:none;text-align:center;font-size:11px;font-weight:800;color:#7b5d16;background:#fff8e6;padding:6px 10px}
      @media(orientation:portrait){.signature-fullscreen.open .signature-orientation-note{display:block}}
      @media(orientation:landscape){
        .signature-modal-head{min-height:52px;padding:6px 12px}.signature-modal-head h2{font-size:17px}
        .signature-modal-body{padding:6px 10px}.signature-instruction{font-size:11px}
        .signature-modal-actions{padding:5px 10px 7px}.signature-modal-actions button{min-height:44px}
      }
    `;
    document.head.appendChild(el);
  }

  function setupUi(){
    const original=$('#signature');
    if(!original || $('#btnSignatureFullscreen')) return;
    style();
    original.setAttribute('aria-label','Prévia da assinatura. Para assinar, use o botão Assinar na tela.');

    const fast=document.createElement('div');
    fast.className='signature-fast';
    fast.innerHTML=`
      <button id="btnSignatureFullscreen" type="button" class="signature-fast-btn">✍️ Assinar na tela</button>
      <div id="signatureFastStatus" class="signature-fast-status">● Assinatura pendente</div>`;
    original.parentNode.insertBefore(fast, original);

    const previewLabel=document.createElement('div');
    previewLabel.className='signature-preview-label';
    previewLabel.textContent='Prévia da assinatura • não é possível riscar aqui';
    original.parentNode.insertBefore(previewLabel,original);

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
      <div class="signature-orientation-note">↻ A assinatura deve ser feita com o celular na horizontal.</div>
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
      if(e.target.closest('#bioUseSign')) setTimeout(()=>openModal(),0);
    });

    window.AuditarSignature={
      open:openModal,
      status:setStatus,
      isOpen:()=>$('#signatureFullscreen')?.classList.contains('open')||false
    };
  }

  function workerLabel(){
    const sel=$('#deliveryWorker');
    const text=sel?.selectedOptions?.[0]?.textContent?.trim()||'';
    return sel?.value ? text : 'Colaborador ainda não selecionado';
  }

  async function openModal(){
    const modal=$('#signatureFullscreen');
    if(!modal || modal.classList.contains('open')) return;
    $('#signatureWorkerName').textContent=workerLabel();
    previousOverflow=document.body.style.overflow;
    document.body.style.overflow='hidden';
    await landscape();
    modal.classList.add('open');
    dirty=false;
    setTimeout(()=>{ resizeLarge(); clearLarge(false); },180);
  }

  async function closeModal(){
    $('#signatureFullscreen')?.classList.remove('open');
    document.body.style.overflow=previousOverflow;
    drawing=false;
    await portrait();
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

  async function confirmSignature(){
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
    await closeModal();
    toast('Assinatura confirmada.');
    setTimeout(()=>$('#btnSaveDelivery')?.scrollIntoView({behavior:'smooth',block:'center'}),120);
  }

  function setStatus(ok){
    const status=$('#signatureFastStatus');
    if(!status) return;
    status.classList.toggle('ok',!!ok);
    status.textContent=ok?'✓ Assinatura confirmada':'● Assinatura pendente';
    const btn=$('#btnSignatureFullscreen');
    if(btn) btn.textContent=ok?'✍️ Refazer assinatura':'✍️ Assinar na tela';
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',setupUi);
  else setupUi();
})();
