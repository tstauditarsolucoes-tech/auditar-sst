(() => {
  const APP_KEY='auditarEpiV1';
  const MODEL_BASE='https://cdn.jsdelivr.net/npm/@vladmandic/human@3.3.6/models';
  const FACE_MIN=0.62;
  const REAL_MIN=0.52;
  const LIVE_MIN=0.52;
  const $=(s,r=document)=>r.querySelector(s);
  let engine=null,loading=null,stream=null,running=false,blinkSeen=false,goodFrames=0;
  let livePassedAt='',liveWorkerId='',lastReal=0,lastLive=0;

  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);}
  function root(){try{return JSON.parse(localStorage.getItem(APP_KEY)||'{}');}catch{return {};}}
  function saveRoot(x){localStorage.setItem(APP_KEY,JSON.stringify(x));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed'));}

  async function getEngine(){
    if(engine)return engine;if(loading)return loading;
    loading=(async()=>{
      if(!window.Human?.Human)throw new Error('Motor facial não carregou. Conecte à internet e tente novamente.');
      engine=new window.Human.Human({backend:'webgl',modelBasePath:MODEL_BASE,cacheSensitivity:0.01,filter:{enabled:true,equalization:true},face:{enabled:true,detector:{rotation:true,return:true,maxDetected:2,minConfidence:0.55},mesh:{enabled:true},description:{enabled:true},iris:{enabled:true},emotion:{enabled:false},antispoof:{enabled:true},liveness:{enabled:true}},body:{enabled:false},hand:{enabled:false},object:{enabled:false},gesture:{enabled:true}});
      await engine.load();return engine;
    })().catch(e=>{engine=null;loading=null;throw e;});
    return loading;
  }

  function styles(){
    if($('#liveFaceStyle'))return;
    const s=document.createElement('style');s.id='liveFaceStyle';s.textContent=`
      .live-overlay{display:none;position:fixed;inset:0;z-index:10050;background:#092e2b;color:#fff;flex-direction:column}.live-overlay.open{display:flex}
      .live-head{padding:16px;display:flex;align-items:center;justify-content:space-between;gap:12px}.live-head h2{margin:0;font-size:20px}.live-head p{margin:4px 0 0;color:#c7dedb;font-size:12px}.live-close{width:44px;height:44px;border:0;border-radius:12px;background:rgba(255,255,255,.12);color:#fff;font-size:22px}
      .live-stage{flex:1;min-height:0;position:relative;display:flex;align-items:center;justify-content:center;background:#051f1d;overflow:hidden}.live-stage video{width:100%;height:100%;object-fit:cover;transform:scaleX(-1)}
      .live-frame{position:absolute;width:min(72vw,330px);aspect-ratio:3/4;border:3px solid rgba(255,255,255,.85);border-radius:45% 45% 42% 42%;box-shadow:0 0 0 9999px rgba(0,0,0,.24);pointer-events:none}.live-instruction{position:absolute;left:15px;right:15px;bottom:18px;background:rgba(5,31,29,.88);border:1px solid rgba(255,255,255,.15);border-radius:16px;padding:12px;text-align:center;font-weight:900}.live-instruction small{display:block;font-weight:600;color:#c7dedb;margin-top:4px}
      .live-steps{padding:13px 15px;background:#0c3b37;display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.live-step{border-radius:11px;background:rgba(255,255,255,.08);padding:9px 7px;text-align:center;font-size:11px;font-weight:850;color:#bdd7d3}.live-step.ok{background:#dcfce7;color:#166534}.live-step.wait{background:#fff7d6;color:#825b08}
      .live-note{padding:10px 15px 16px;background:#0c3b37;color:#c7dedb;font-size:10px;text-align:center}.bio-liveness-badge{display:block;margin-top:6px;color:#166534;font-size:11px;font-weight:900}
    `;document.head.appendChild(s);
  }

  function setupOverlay(){
    if($('#liveOverlay'))return;
    const d=document.createElement('div');d.id='liveOverlay';d.className='live-overlay';d.innerHTML=`
      <div class="live-head"><div><h2>Prova de vida</h2><p>Olhe de frente para a câmera e pisque normalmente.</p></div><button id="liveClose" type="button" class="live-close">×</button></div>
      <div class="live-stage"><video id="liveVideo" autoplay muted playsinline></video><div class="live-frame"></div><div class="live-instruction" id="liveInstruction">Posicione o rosto dentro da marca<small>Depois pisque uma vez</small></div></div>
      <div class="live-steps"><div id="liveFaceStep" class="live-step wait">1. Rosto</div><div id="liveBlinkStep" class="live-step wait">2. Piscar</div><div id="liveRealStep" class="live-step wait">3. Pessoa real</div></div>
      <div class="live-note">A prova de vida é usada apenas para confirmar esta entrega. A assinatura manual continua disponível.</div>`;
    document.body.appendChild(d);$('#liveClose').addEventListener('click',cancelLive);
  }

  function setStep(id,ok){const e=$(id);if(!e)return;e.classList.toggle('ok',!!ok);e.classList.toggle('wait',!ok);}
  function gesturesOf(result){const g=result?.gesture||[];return Object.values(g).flatMap(x=>Array.isArray(x)?x:[x]).map(x=>String(x?.gesture||x||'').toLowerCase());}

  async function startLive(){
    const modal=$('#bioModal');if(!modal?.classList.contains('open'))return;
    const workerId=$('#deliveryWorker')?.value||'';if(!workerId)return;
    modal.classList.remove('open');
    styles();setupOverlay();blinkSeen=false;goodFrames=0;lastReal=0;lastLive=0;running=true;liveWorkerId=workerId;
    $('#liveOverlay').classList.add('open');setStep('#liveFaceStep',false);setStep('#liveBlinkStep',false);setStep('#liveRealStep',false);
    $('#liveInstruction').innerHTML='Preparando câmera…<small>Aguarde um instante</small>';
    try{
      await getEngine();
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('A câmera ao vivo não está disponível neste aparelho.');
      stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:'user',width:{ideal:640},height:{ideal:800}}});
      const v=$('#liveVideo');v.srcObject=stream;await v.play();
      $('#liveInstruction').innerHTML='Olhe de frente para a câmera<small>Pisque uma vez normalmente</small>';
      requestAnimationFrame(loop);
    }catch(err){toast(err.message||'Não foi possível abrir a câmera.');cancelLive();}
  }

  async function loop(){
    if(!running)return;
    const video=$('#liveVideo');
    try{
      const result=await engine.detect(video);const faces=result?.face||[];const exactlyOne=faces.length===1;setStep('#liveFaceStep',exactlyOne);
      if(!exactlyOne){goodFrames=0;$('#liveInstruction').innerHTML=faces.length>1?'Deixe somente uma pessoa na câmera<small>Depois pisque uma vez</small>':'Posicione o rosto dentro da marca<small>Depois pisque uma vez</small>';return schedule();}
      const f=faces[0];const score=Number(f.faceScore||f.boxScore||0);lastReal=Number(f.real||0);lastLive=Number(f.live||0);
      const gs=gesturesOf(result);if(gs.some(x=>x.includes('blink')))blinkSeen=true;
      setStep('#liveBlinkStep',blinkSeen);
      const realOk=score>=FACE_MIN&&lastReal>=REAL_MIN&&lastLive>=LIVE_MIN;setStep('#liveRealStep',realOk);
      if(!blinkSeen){$('#liveInstruction').innerHTML='Agora pisque uma vez<small>Mantenha o rosto olhando para a câmera</small>';goodFrames=0;return schedule();}
      if(!realOk){$('#liveInstruction').innerHTML='Mantenha o rosto bem iluminado<small>Verificando se é uma pessoa real…</small>';goodFrames=0;return schedule();}
      goodFrames++;
      $('#liveInstruction').innerHTML='Prova de vida aprovada ✓<small>Comparando com o cadastro biométrico…</small>';
      if(goodFrames>=2)return passLive();
    }catch(_){goodFrames=0;}
    schedule();
  }
  function schedule(){if(running)setTimeout(()=>requestAnimationFrame(loop),120);}

  async function passLive(){
    if(!running)return;running=false;livePassedAt=new Date().toISOString();
    const video=$('#liveVideo');const c=document.createElement('canvas');c.width=video.videoWidth||640;c.height=video.videoHeight||800;c.getContext('2d').drawImage(video,0,0,c.width,c.height);
    const blob=await new Promise(res=>c.toBlob(res,'image/jpeg',0.86));stopStream();$('#liveOverlay').classList.remove('open');
    if(!blob){toast('Não foi possível capturar o rosto.');return clearPending();}
    try{
      const file=new File([blob],'prova-vida.jpg',{type:'image/jpeg',lastModified:Date.now()});const dt=new DataTransfer();dt.items.add(file);const input=$('#bioCamera');input.files=dt.files;input.dispatchEvent(new Event('change',{bubbles:true}));
      watchVerification();
    }catch(err){toast('Falha ao encaminhar a prova de vida para a biometria.');clearPending();}
  }

  function watchVerification(){
    let tries=0;const timer=setInterval(()=>{tries++;const s=$('#bioVerifyStatus');if(s?.classList.contains('ok')){clearInterval(timer);s.insertAdjacentHTML('beforeend','<span class="bio-liveness-badge">✓ Prova de vida aprovada • piscar + detecção de rosto real</span>');}else if(tries>80)clearInterval(timer);},100);
  }

  function stopStream(){if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}const v=$('#liveVideo');if(v)v.srcObject=null;}
  function clearPending(){stopStream();running=false;$('#liveOverlay')?.classList.remove('open');$('#bioCancel')?.click();}
  function cancelLive(){clearPending();toast('Prova de vida cancelada.');}

  function patchSavedDelivery(){
    if(!livePassedAt||!liveWorkerId)return;const at=livePassedAt,wid=liveWorkerId,real=lastReal,live=lastLive;
    setTimeout(()=>{try{const x=root();const d=(x.deliveries||[])[0];if(!d||d.confirmationMethod!=='face-biometric'||d.biometricWorkerId!==wid)return;d.biometricLivenessVerified=true;d.biometricLivenessAt=at;d.biometricBlinkVerified=true;d.biometricAntispoofScore=Math.round(real*10000)/10000;d.biometricLiveScore=Math.round(live*10000)/10000;d.updatedAt=new Date().toISOString();saveRoot(x);patchReceipt(d.id);}catch(_){} livePassedAt='';liveWorkerId='';},320);
  }

  function patchReceipt(id){
    try{const x=root();const d=(x.deliveries||[]).find(a=>a.id===id);if(!d?.biometricLivenessVerified)return;const box=$('#receiptContent .bio-proof-note');if(box&&!box.querySelector('.live-receipt'))box.insertAdjacentHTML('beforeend','<span class="live-receipt"><br><b>✓ Prova de vida aprovada:</b> piscar e verificação de rosto real no momento da entrega.</span>');}catch(_){}
  }

  function bind(){
    const btn=$('#bioVerifyNow');if(btn&&!btn.dataset.liveBound){btn.dataset.liveBound='1';btn.textContent='🙂 Prova de vida + verificar rosto';btn.addEventListener('click',()=>setTimeout(startLive,0));}
    $('#deliveryWorker')?.addEventListener('change',()=>{livePassedAt='';liveWorkerId='';});
    $('#btnSaveDelivery')?.addEventListener('click',patchSavedDelivery);
    document.addEventListener('click',e=>{const r=e.target.closest('[data-receipt]');if(r)setTimeout(()=>patchReceipt(r.dataset.receipt),150);});
  }
  function setup(){styles();setupOverlay();bind();const p=$('#bioDeliveryPanel');if(p)new MutationObserver(bind).observe(p,{childList:true,subtree:true});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(setup,0));else setTimeout(setup,0);
})();
