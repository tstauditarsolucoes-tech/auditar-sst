(() => {
  const TENANT_CODE_KEY='gestaoEpiTenantCode';
  const CACHE='auditarEpiGestaoCacheV1';
  const THRESHOLD=0.60;
  const HUMAN_SRC='https://cdn.jsdelivr.net/npm/@vladmandic/human@3.3.6/dist/human.js';
  const MODEL_BASE='https://cdn.jsdelivr.net/npm/@vladmandic/human@3.3.6/models';
  const nativeGet=Storage.prototype.getItem;
  const nativeSet=Storage.prototype.setItem;
  const nativeRemove=Storage.prototype.removeItem;

  nativeRemove.call(localStorage,TENANT_CODE_KEY);
  Storage.prototype.getItem=function(key){if(key===TENANT_CODE_KEY)return '';return nativeGet.call(this,key);};
  Storage.prototype.setItem=function(key,value){if(key===TENANT_CODE_KEY){nativeRemove.call(this,key);return;}return nativeSet.call(this,key,value);};
  Storage.prototype.removeItem=function(key){if(key===TENANT_CODE_KEY){nativeRemove.call(this,key);return;}return nativeRemove.call(this,key);};

  const style=document.createElement('style');
  style.id='gestaoEpiPcStableScroll';
  style.textContent=`
    @media (min-width:721px){html,body{height:100%;overflow:hidden!important}.layout{height:100vh!important;min-height:0!important;overflow:hidden!important}.sidebar{position:relative!important;top:auto!important;height:100vh!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important}.main{height:100vh!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important}}
    .pc-face-methods{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:10px 0 12px}.pc-face-methods button{min-height:48px;border:1px solid #cbdad8;background:#fff;color:#355b57;border-radius:12px;font-weight:900;cursor:pointer}.pc-face-methods button.active{background:#e8f5f3;border-color:#0f766e;color:#0f766e}.pc-face-panel{display:none;border:1px solid #d7e6e3;background:#f8fbfb;border-radius:14px;padding:13px;margin-bottom:12px}.pc-face-panel.open{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center}.pc-face-copy b{display:block;color:#173d39}.pc-face-copy span{display:block;color:#6c827e;font-size:11px;margin-top:3px}.pc-face-status{grid-column:1/-1;padding:9px 11px;border-radius:10px;background:#fff8e6;color:#8a6418;font-size:11px;font-weight:850}.pc-face-status.ok{background:#ecfdf3;color:#166534}.pc-face-status.fail{background:#fff0ee;color:#b42318}.pc-face-mode #pcSignature,.pc-face-mode #pcClearSignature{display:none!important}.pc-face-overlay{display:none;position:fixed;inset:0;z-index:12000;background:#082d2a;color:#fff;flex-direction:column}.pc-face-overlay.open{display:flex}.pc-face-head{padding:15px 18px;display:flex;align-items:center;justify-content:space-between;gap:12px}.pc-face-head h2{margin:0;font-size:20px}.pc-face-head p{margin:4px 0 0;color:#c4dcd8;font-size:12px}.pc-face-close{width:44px;height:44px;border:0;border-radius:12px;background:rgba(255,255,255,.12);color:#fff;font-size:22px}.pc-face-stage{flex:1;min-height:0;position:relative;display:flex;align-items:center;justify-content:center;background:#051f1d;overflow:hidden}.pc-face-stage video{width:100%;height:100%;object-fit:cover;transform:scaleX(-1)}.pc-face-frame{position:absolute;width:min(52vw,340px);aspect-ratio:3/4;border:3px solid rgba(255,255,255,.9);border-radius:44%;box-shadow:0 0 0 9999px rgba(0,0,0,.24);pointer-events:none}.pc-face-instruction{position:absolute;left:20px;right:20px;bottom:20px;background:rgba(5,31,29,.9);padding:12px 14px;border-radius:14px;text-align:center;font-weight:900}.pc-face-actions{padding:14px 18px 18px;background:#0c3b37;display:flex;justify-content:center}.pc-face-capture{min-width:240px;min-height:50px;border:0;border-radius:13px;background:#fff;color:#0f766e;font-weight:900;font-size:15px}.pc-face-capture:disabled{opacity:.6}.pc-face-note{padding:0 18px 14px;background:#0c3b37;color:#c7dedb;text-align:center;font-size:10px}.pc-face-proof{margin-top:12px;padding:10px 12px;border-radius:10px;background:#eef8f6;color:#315d57;font-size:11px;line-height:1.45}
  `;
  document.head.appendChild(style);

  const $=(s,r=document)=>r.querySelector(s);
  let mode='signature',verified=false,verifiedAt='',verifiedSimilarity=0,verifiedWorkerId='',stream=null,human=null,humanLoading=null;

  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2700);}
  function root(){try{const x=JSON.parse(localStorage.getItem(CACHE)||'{}');x.app=x.app&&typeof x.app==='object'?x.app:{};x.app.workers=Array.isArray(x.app.workers)?x.app.workers:[];return x;}catch(_){return {app:{workers:[]}};}}
  function worker(id){return root().app.workers.find(x=>x.id===id);}
  function roundEmbedding(a){return Array.from(a||[]).map(n=>Math.round(Number(n)*1000000)/1000000);}

  async function loadHumanScript(){
    if(window.Human?.Human)return;
    const existing=document.querySelector('script[data-pc-human]');
    if(existing){await new Promise((resolve,reject)=>{if(window.Human?.Human)return resolve();existing.addEventListener('load',resolve,{once:true});existing.addEventListener('error',()=>reject(new Error('Falha ao carregar o motor biométrico.')),{once:true});});return;}
    await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=HUMAN_SRC;s.dataset.pcHuman='1';s.onload=resolve;s.onerror=()=>reject(new Error('Falha ao carregar o motor biométrico. Verifique a internet.'));document.head.appendChild(s);});
  }

  async function ensureHuman(){
    if(human)return human;if(humanLoading)return humanLoading;
    humanLoading=(async()=>{
      await loadHumanScript();
      if(!window.Human?.Human)throw new Error('Motor biométrico não disponível.');
      human=new window.Human.Human({backend:'webgl',modelBasePath:MODEL_BASE,cacheSensitivity:0.01,filter:{enabled:true,equalization:true},face:{enabled:true,detector:{rotation:true,return:true,maxDetected:2,minConfidence:0.6},mesh:{enabled:true},description:{enabled:true},iris:{enabled:false},emotion:{enabled:false},antispoof:{enabled:false},liveness:{enabled:false}},body:{enabled:false},hand:{enabled:false},object:{enabled:false},gesture:{enabled:false}});
      await human.load();return human;
    })().catch(err=>{human=null;humanLoading=null;throw err;});
    return humanLoading;
  }

  function ensureOverlay(){
    if($('#pcFaceOverlay'))return;
    const d=document.createElement('div');d.id='pcFaceOverlay';d.className='pc-face-overlay';d.innerHTML=`<div class="pc-face-head"><div><h2>Verificação facial</h2><p>Olhe normalmente para a câmera. Não precisa piscar, sorrir ou virar a cabeça.</p></div><button id="pcFaceClose" class="pc-face-close" type="button">×</button></div><div class="pc-face-stage"><video id="pcFaceVideo" autoplay muted playsinline></video><div class="pc-face-frame"></div><div class="pc-face-instruction">Centralize somente o rosto do trabalhador</div></div><div class="pc-face-actions"><button id="pcFaceCapture" class="pc-face-capture" type="button">🙂 Verificar rosto</button></div><div class="pc-face-note">A foto não é salva. O sistema usa o rosto somente para comparar com a biometria cadastrada do trabalhador.</div>`;
    document.body.appendChild(d);$('#pcFaceClose').onclick=closeCamera;$('#pcFaceCapture').onclick=verifyFrame;
  }

  function setup(){
    const canvas=$('#pcSignature');if(!canvas||$('#pcFaceMethods'))return false;ensureOverlay();const card=canvas.closest('.pc-card');if(!card)return false;card.id='pcConfirmCard';
    const head=card.querySelector('.pc-modern-head');if(head){const h=head.querySelector('h2'),p=head.querySelector('p');if(h)h.textContent='Confirmação do trabalhador';if(p)p.textContent='Escolha assinatura ou biometria facial. A facial não exige piscar.';}
    const methods=document.createElement('div');methods.id='pcFaceMethods';methods.className='pc-face-methods';methods.innerHTML='<button id="pcUseSignature" type="button" class="active">✍️ Assinatura</button><button id="pcUseFace" type="button">🙂 Facial sem piscar</button>';canvas.parentNode.insertBefore(methods,canvas);
    const panel=document.createElement('div');panel.id='pcFacePanel';panel.className='pc-face-panel';panel.innerHTML='<div class="pc-face-copy"><b>Verificação biométrica 1:1</b><span>O rosto será comparado somente com a biometria cadastrada do trabalhador selecionado.</span></div><button id="pcFaceVerify" class="primary" type="button">📷 Abrir câmera</button><div id="pcFaceStatus" class="pc-face-status">Biometria ainda não verificada.</div>';canvas.parentNode.insertBefore(panel,canvas);
    $('#pcUseSignature').onclick=()=>setMode('signature');$('#pcUseFace').onclick=()=>setMode('face');$('#pcFaceVerify').onclick=openCamera;$('#pcDeliveryWorker')?.addEventListener('change',resetVerification);
    setTimeout(()=>{const v=$('.pc-version');if(v)v.textContent='PC v2.2.0';},100);return true;
  }

  function setMode(next){mode=next;resetVerification();const card=$('#pcConfirmCard');card?.classList.toggle('pc-face-mode',mode==='face');$('#pcFacePanel')?.classList.toggle('open',mode==='face');$('#pcUseFace')?.classList.toggle('active',mode==='face');$('#pcUseSignature')?.classList.toggle('active',mode!=='face');if(mode==='face')$('#pcClearSignature')?.click();}
  function resetVerification(){verified=false;verifiedAt='';verifiedSimilarity=0;verifiedWorkerId='';const s=$('#pcFaceStatus');if(s){s.className='pc-face-status';s.textContent='Biometria ainda não verificada.';}}

  async function openCamera(){
    const workerId=$('#pcDeliveryWorker')?.value||'';if(!workerId)return toast('Selecione o trabalhador primeiro.');const w=worker(workerId);if(!Array.isArray(w?.biometric?.embedding)||!w.biometric.embedding.length)return toast('Esse trabalhador ainda não tem biometria cadastrada. Cadastre o rosto no aplicativo Campo primeiro.');
    ensureOverlay();$('#pcFaceOverlay').classList.add('open');const btn=$('#pcFaceCapture');if(btn){btn.disabled=true;btn.textContent='Carregando biometria…';}
    try{await ensureHuman();if(!navigator.mediaDevices?.getUserMedia)throw new Error('A câmera não está disponível neste computador.');stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{width:{ideal:720},height:{ideal:900},facingMode:'user'}});const v=$('#pcFaceVideo');v.srcObject=stream;await v.play();if(btn){btn.disabled=false;btn.textContent='🙂 Verificar rosto';}}
    catch(err){toast(err.message||'Não foi possível abrir a câmera.');closeCamera();}
  }

  function closeCamera(){if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}const v=$('#pcFaceVideo');if(v)v.srcObject=null;$('#pcFaceOverlay')?.classList.remove('open');const btn=$('#pcFaceCapture');if(btn){btn.disabled=false;btn.textContent='🙂 Verificar rosto';}}

  async function verifyFrame(){
    const workerId=$('#pcDeliveryWorker')?.value||'',w=worker(workerId),ref=w?.biometric?.embedding;if(!workerId||!Array.isArray(ref)||!ref.length){closeCamera();return toast('Biometria do trabalhador não encontrada.');}
    const video=$('#pcFaceVideo');if(!video?.videoWidth)return toast('Aguarde a câmera carregar.');const btn=$('#pcFaceCapture');btn.disabled=true;btn.textContent='Analisando rosto…';
    try{
      const engine=await ensureHuman(),c=document.createElement('canvas');c.width=Math.min(640,video.videoWidth);c.height=Math.max(1,Math.round(c.width*(video.videoHeight/video.videoWidth)));c.getContext('2d').drawImage(video,0,0,c.width,c.height);
      const result=await engine.detect(c),faces=result?.face||[];if(faces.length!==1)throw new Error(faces.length>1?'Deixe somente uma pessoa na câmera.':'Rosto não encontrado. Aproxime-se e melhore a iluminação.');const face=faces[0],score=Number(face.faceScore||face.boxScore||0);if(score<0.60)throw new Error('Não consegui ler o rosto com segurança. Tente novamente.');const embedding=roundEmbedding(face.embedding);if(!embedding.length)throw new Error('Não foi possível gerar a biometria facial.');
      const similarity=Number(engine.match.similarity(ref,embedding,{order:2,multiplier:25,min:0.2,max:0.8})||0);verified=similarity>=THRESHOLD;verifiedAt=new Date().toISOString();verifiedSimilarity=similarity;verifiedWorkerId=workerId;const s=$('#pcFaceStatus');if(s){s.className='pc-face-status '+(verified?'ok':'fail');s.textContent=verified?`✓ Rosto confirmado • ${Math.round(similarity*100)}% de compatibilidade`:`Rosto não confirmado • ${Math.round(similarity*100)}%. Tente novamente.`;}
      if(!verified)throw new Error(`Rosto não confirmado (${Math.round(similarity*100)}%).`);closeCamera();toast(`Rosto confirmado • ${Math.round(similarity*100)}%`);
    }catch(err){toast(err.message||'Falha na verificação facial.');}
    finally{btn.disabled=false;btn.textContent='🙂 Verificar rosto';}
  }

  window.GestaoEpiPcFace={
    mode:()=>mode,
    reset:()=>setMode('signature'),
    getConfirmation:()=>mode==='face'?{mode:'face',valid:verified&&verifiedWorkerId===($('#pcDeliveryWorker')?.value||''),workerId:verifiedWorkerId,confirmationType:'face-1to1',facialVerifiedAt:verifiedAt,facialSimilarity:verifiedSimilarity,facialBlinkRequired:false,biometricEngine:'human-faceres',biometricVersion:1}:{mode:'signature',valid:true,confirmationType:'signature'}
  };

  function boot(){let tries=0;const timer=setInterval(()=>{tries++;if(setup()||tries>80)clearInterval(timer);},100);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,0),{once:true});else setTimeout(boot,0);
})();