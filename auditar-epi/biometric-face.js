(() => {
  const APP_KEY='auditarEpiV1';
  const THRESHOLD=0.60;
  const MODEL_BASE='https://cdn.jsdelivr.net/npm/@vladmandic/human@3.3.6/models';
  const $=(s,r=document)=>r.querySelector(s);
  let human=null;
  let loading=null;
  let mode='signature';
  let verified=false;
  let verifiedAt='';
  let verifiedSimilarity=0;
  let pendingAction=null;
  let pendingWorkerId='';

  function toast(msg){
    const el=$('#toast');
    if(!el) return alert(msg);
    el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2700);
  }
  function loadRoot(){try{return JSON.parse(localStorage.getItem(APP_KEY)||'{}');}catch{return {};}}
  function saveRoot(root){localStorage.setItem(APP_KEY,JSON.stringify(root));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed'));}
  function workerById(id){return (loadRoot().workers||[]).find(w=>w.id===id);}
  function esc(v=''){return String(v??'').replace(/[&<>'\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[c]));}
  function roundEmbedding(a){return Array.from(a||[]).map(n=>Math.round(Number(n)*1000000)/1000000);}

  async function ensureHuman(){
    if(human) return human;
    if(loading) return loading;
    loading=(async()=>{
      if(!window.Human?.Human) throw new Error('Motor biométrico não carregou. Conecte à internet e tente novamente.');
      human=new window.Human.Human({
        backend:'webgl',
        modelBasePath:MODEL_BASE,
        cacheSensitivity:0.01,
        filter:{enabled:true,equalization:true},
        face:{
          enabled:true,
          detector:{rotation:true,return:true,maxDetected:2,minConfidence:0.6},
          mesh:{enabled:true},
          description:{enabled:true},
          iris:{enabled:false},
          emotion:{enabled:false},
          antispoof:{enabled:false},
          liveness:{enabled:false}
        },
        body:{enabled:false},hand:{enabled:false},object:{enabled:false},gesture:{enabled:false}
      });
      await human.load();
      return human;
    })().catch(err=>{human=null;loading=null;throw err;});
    return loading;
  }

  function imageFromDataUrl(src){
    return new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(new Error('Não foi possível abrir a foto.'));img.src=src;});
  }
  function readFile(file){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result||''));r.onerror=()=>reject(new Error('Não foi possível ler a foto.'));r.readAsDataURL(file);});}

  async function descriptorFromFile(file){
    if(!file||!file.type?.startsWith('image/')) throw new Error('Tire uma foto válida do rosto.');
    const engine=await ensureHuman();
    const src=await readFile(file);
    const img=await imageFromDataUrl(src);
    const result=await engine.detect(img);
    const faces=result?.face||[];
    if(faces.length!==1) throw new Error(faces.length>1?'Deixe somente uma pessoa na foto.':'Rosto não encontrado. Tente novamente com boa iluminação.');
    const face=faces[0];
    const score=Number(face.faceScore||face.boxScore||0);
    if(score<0.60) throw new Error('Não foi possível ler o rosto com segurança. Tente novamente.');
    const embedding=face.embedding;
    if(!embedding?.length) throw new Error('Não foi possível gerar a biometria facial.');
    return {embedding:roundEmbedding(embedding),score};
  }

  function styles(){
    if($('#bioFaceStyle'))return;
    const s=document.createElement('style');s.id='bioFaceStyle';s.textContent=`
      .bio-worker-btn{margin-left:6px}.bio-worker-ok{color:#166534!important;background:#ecfdf3!important;border-color:#bbefcc!important}
      .bio-methods{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:12px 0}.bio-methods button{min-height:56px;border:1px solid #cbdad8;background:#fff;color:#355b57;border-radius:14px;font-weight:900;font-size:14px}.bio-methods button.active{background:#e8f5f3;border-color:#0f766e;color:#0f766e}
      .bio-panel{display:none;border:1px solid #d7e6e3;background:#f8fbfb;border-radius:16px;padding:14px;margin-top:10px}.bio-panel.open{display:block}.bio-panel h4{margin:0 0 5px}.bio-panel p{margin:0 0 10px;color:#607a76;font-size:12px;line-height:1.45}
      .bio-main-btn{width:100%;min-height:58px;border:0;border-radius:14px;background:#0f766e;color:#fff;font-size:16px;font-weight:900}.bio-status{margin-top:10px;padding:10px 12px;border-radius:12px;background:#fff8e6;color:#8a6418;font-size:12px;font-weight:850}.bio-status.ok{background:#ecfdf3;color:#166534}.bio-status.fail{background:#fff0ee;color:#b42318}
      .bio-signature-mode .signature-fast,.bio-signature-mode #signature,.bio-signature-mode .signature-hint,.bio-signature-mode #btnClearSignature{display:none!important}
      .bio-modal{display:none;position:fixed;inset:0;z-index:10020;background:rgba(10,42,39,.82);padding:18px;align-items:center;justify-content:center}.bio-modal.open{display:flex}.bio-card{width:min(460px,100%);background:#fff;border-radius:22px;padding:20px}.bio-card h2{margin:0 0 5px}.bio-card p{margin:0 0 14px;color:#647b78;font-size:12px;line-height:1.45}.bio-notice{display:flex;gap:9px;align-items:flex-start;padding:10px;border:1px solid #dce7e5;border-radius:12px;font-size:12px}.bio-notice input{margin-top:2px}.bio-actions{display:grid;gap:8px;margin-top:14px}.bio-actions button{min-height:50px;border:0;border-radius:13px;font-weight:900}.bio-actions .primaryx{background:#0f766e;color:white}.bio-actions .cancelx{background:#eef5f4;color:#355b57}
      .bio-proof-note{margin-top:12px;padding:10px 12px;border-radius:10px;background:#eef8f6;color:#315d57;font-size:11px;line-height:1.45}
      @media(max-width:520px){.bio-methods{grid-template-columns:1fr}.bio-card{padding:17px}}
    `;document.head.appendChild(s);
  }

  function setupModal(){
    if($('#bioModal'))return;
    const d=document.createElement('div');d.id='bioModal';d.className='bio-modal';d.innerHTML=`
      <div class="bio-card"><h2 id="bioModalTitle">Biometria facial</h2><p id="bioModalText">Tire uma foto de frente, com boa iluminação e somente uma pessoa.</p>
      <label class="bio-notice"><input id="bioConsent" type="checkbox"><span id="bioConsentText">O colaborador foi informado sobre o uso da biometria facial para confirmar entregas de EPI.</span></label>
      <input id="bioCamera" type="file" accept="image/*" capture="user" hidden>
      <div class="bio-actions"><button id="bioTake" type="button" class="primaryx">📷 Abrir câmera</button><button id="bioCancel" type="button" class="cancelx">Cancelar</button></div></div>`;
    document.body.appendChild(d);
    $('#bioTake').addEventListener('click',()=>{if(!$('#bioConsent').checked)return toast('Confirme que o colaborador foi informado.');$('#bioCamera').value='';$('#bioCamera').click();});
    $('#bioCancel').addEventListener('click',closeModal);
    $('#bioCamera').addEventListener('change',onCameraFile);
  }
  function openModal(action,workerId){
    pendingAction=action;pendingWorkerId=workerId;$('#bioConsent').checked=false;
    const w=workerById(workerId);
    $('#bioModalTitle').textContent=action==='enroll'?'Cadastrar biometria facial':'Verificar biometria facial';
    $('#bioModalText').textContent=action==='enroll'?`Cadastre o rosto de ${w?.name||'colaborador'} uma única vez. A foto não será guardada; será salvo o vetor biométrico.`:`O rosto capturado agora será comparado somente com a biometria cadastrada de ${w?.name||'colaborador'}.`;
    $('#bioModal').classList.add('open');
  }
  function closeModal(){$('#bioModal')?.classList.remove('open');pendingAction=null;pendingWorkerId='';}

  async function onCameraFile(e){
    const file=e.target.files?.[0];if(!file)return;
    const btn=$('#bioTake');const old=btn.textContent;btn.disabled=true;btn.textContent='Analisando rosto…';
    try{
      const desc=await descriptorFromFile(file);
      if(pendingAction==='enroll') await enroll(pendingWorkerId,desc.embedding);
      else if(pendingAction==='verify') await verify(pendingWorkerId,desc.embedding);
      closeModal();
    }catch(err){toast(err.message||'Falha na biometria.');}
    finally{btn.disabled=false;btn.textContent=old;}
  }

  async function enroll(workerId,embedding){
    const root=loadRoot();const w=(root.workers||[]).find(x=>x.id===workerId);if(!w)throw new Error('Colaborador não encontrado.');
    w.biometric={type:'face-1to1',engine:'human-faceres',version:1,embedding,enrolledAt:new Date().toISOString()};w.updatedAt=new Date().toISOString();saveRoot(root);
    decorateWorkers();toast('Biometria facial cadastrada.');
  }

  async function verify(workerId,embedding){
    const w=workerById(workerId);const ref=w?.biometric?.embedding;
    if(!Array.isArray(ref)||!ref.length)throw new Error('Esse colaborador ainda não tem biometria cadastrada.');
    const engine=await ensureHuman();
    const similarity=Number(engine.match.similarity(ref,embedding,{order:2,multiplier:25,min:0.2,max:0.8})||0);
    verifiedSimilarity=similarity;verifiedAt=new Date().toISOString();verified=similarity>=THRESHOLD;
    renderVerifyStatus();
    if(!verified)throw new Error(`Rosto não confirmado (${Math.round(similarity*100)}%). Tente novamente.`);
    markSignatureForBiometric();
    toast(`Rosto confirmado • ${Math.round(similarity*100)}%`);
  }

  function decorateWorkers(){
    const list=$('#workerList');if(!list)return;
    list.querySelectorAll('.list-item').forEach(item=>{
      const del=item.querySelector('[data-del-worker]');const id=del?.dataset.delWorker;if(!id||item.querySelector('[data-bio-worker]'))return;
      const w=workerById(id);const b=document.createElement('button');b.type='button';b.className='tiny bio-worker-btn'+(w?.biometric?.embedding?.length?' bio-worker-ok':'');b.dataset.bioWorker=id;b.textContent=w?.biometric?.embedding?.length?'✓ Rosto cadastrado':'🙂 Cadastrar rosto';
      (item.querySelector('.list-actions')||item).appendChild(b);
    });
  }

  function setupDelivery(){
    const sig=$('#signature');if(!sig||$('#bioDeliveryPanel'))return;
    const card=sig.closest('.card');const title=card?.querySelector('.section-title');if(title){const h=title.querySelector('h3');const p=title.querySelector('p');if(h)h.textContent='Confirmação do colaborador';if(p)p.textContent='Assine na tela ou confirme pelo rosto.';}
    const chooser=document.createElement('div');chooser.className='bio-methods';chooser.innerHTML='<button id="bioUseSign" type="button" class="active">✍️ Assinar na tela</button><button id="bioUseFace" type="button">🙂 Verificar rosto</button>';
    const fast=card.querySelector('.signature-fast');(fast||sig).parentNode.insertBefore(chooser,fast||sig);
    const panel=document.createElement('div');panel.id='bioDeliveryPanel';panel.className='bio-panel';panel.innerHTML='<h4>🙂 Verificação biométrica</h4><p>O app compara o rosto capturado agora somente com o cadastro biométrico do colaborador selecionado.</p><button id="bioVerifyNow" type="button" class="bio-main-btn">📷 Verificar rosto agora</button><div id="bioVerifyStatus" class="bio-status">Biometria ainda não verificada.</div>';
    card.appendChild(panel);
    $('#bioUseSign').addEventListener('click',()=>setMode('signature'));$('#bioUseFace').addEventListener('click',()=>setMode('face'));$('#bioVerifyNow').addEventListener('click',beginVerify);
    $('#deliveryWorker')?.addEventListener('change',resetVerification);
    $('#btnSaveDelivery')?.addEventListener('click',guardSave,true);
    $('#btnSaveDelivery')?.addEventListener('click',afterSave);
  }

  function setMode(next){
    mode=next;verified=false;verifiedAt='';verifiedSimilarity=0;
    const card=$('#signature')?.closest('.card');card?.classList.toggle('bio-signature-mode',mode==='face');
    $('#bioDeliveryPanel')?.classList.toggle('open',mode==='face');$('#bioUseFace')?.classList.toggle('active',mode==='face');$('#bioUseSign')?.classList.toggle('active',mode!=='face');
    if(mode==='face'){$('#btnClearSignature')?.click();renderVerifyStatus();}
  }
  function resetVerification(){verified=false;verifiedAt='';verifiedSimilarity=0;renderVerifyStatus();}
  function renderVerifyStatus(){const s=$('#bioVerifyStatus');if(!s)return;s.className='bio-status'+(verified?' ok':'');s.textContent=verified?`✓ Rosto confirmado • ${Math.round(verifiedSimilarity*100)}% de compatibilidade`:'Biometria ainda não verificada.';}
  function beginVerify(){
    const id=$('#deliveryWorker')?.value;if(!id)return toast('Selecione o colaborador primeiro.');const w=workerById(id);if(!w?.biometric?.embedding?.length)return toast('Cadastre primeiro a biometria deste colaborador em Colaboradores.');openModal('verify',id);
  }

  function markSignatureForBiometric(){
    const canvas=$('#signature');if(!canvas)return;const ctx=canvas.getContext('2d');ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#173d39';ctx.font='bold 30px sans-serif';ctx.textAlign='center';ctx.fillText('BIOMETRIA FACIAL',canvas.width/2,canvas.height/2-10);ctx.font='20px sans-serif';ctx.fillText('ROSTO VERIFICADO',canvas.width/2,canvas.height/2+30);ctx.restore();
    const r=canvas.getBoundingClientRect();const E=window.PointerEvent||window.MouseEvent;try{canvas.dispatchEvent(new E('pointerdown',{bubbles:true,clientX:r.left+2,clientY:r.top+2,pointerId:99}));canvas.dispatchEvent(new E('pointermove',{bubbles:true,clientX:r.left+4,clientY:r.top+4,pointerId:99}));canvas.dispatchEvent(new E('pointerup',{bubbles:true,clientX:r.left+4,clientY:r.top+4,pointerId:99}));}catch(_){canvas.dispatchEvent(new Event('pointerdown',{bubbles:true}));canvas.dispatchEvent(new Event('pointermove',{bubbles:true}));canvas.dispatchEvent(new Event('pointerup',{bubbles:true}));}
  }
  function guardSave(e){if(mode!=='face')return;if(!verified){e.preventDefault();e.stopImmediatePropagation();toast('Faça a verificação biométrica antes de finalizar.');}}
  function afterSave(){
    if(mode!=='face'||!verified)return;const sim=verifiedSimilarity,at=verifiedAt,workerId=$('#deliveryWorker')?.value;
    setTimeout(()=>{try{const root=loadRoot();const rows=Array.isArray(root.deliveries)?root.deliveries:[];const d=rows[0];if(d&&Date.now()-new Date(d.createdAt||0).getTime()<15000){d.confirmationMethod='face-biometric';d.biometricVerified=true;d.biometricSimilarity=Math.round(sim*10000)/10000;d.biometricThreshold=THRESHOLD;d.biometricVerifiedAt=at;d.biometricWorkerId=workerId;d.biometricEngine='human-faceres';d.updatedAt=new Date().toISOString();saveRoot(root);patchReceipt(d.id);}}catch(_){} setMode('signature');},100);
  }

  function patchReceipt(id){
    try{const root=loadRoot();const d=(root.deliveries||[]).find(x=>x.id===id);if(!d||d.confirmationMethod!=='face-biometric')return;const content=$('#receiptContent');if(!content)return;const line=content.querySelector('.sign-line');if(line){const name=(line.innerHTML.split('<br>')[0]||'Colaborador');line.innerHTML=`${name}<br>Biometria facial verificada`;}
      if(!content.querySelector('.bio-proof-note')){const sign=content.querySelector('.receipt-sign');sign?.insertAdjacentHTML('afterend',`<div class="bio-proof-note"><b>🙂 Verificação biométrica facial</b><br>Rosto comparado com o cadastro biométrico do colaborador. Compatibilidade: <b>${Math.round(Number(d.biometricSimilarity||0)*100)}%</b>${d.biometricVerifiedAt?' • '+new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(d.biometricVerifiedAt)):''}.</div>`);}}
    catch(_){}
  }

  function setup(){
    styles();setupModal();setupDelivery();decorateWorkers();
    $('#workerList')&&new MutationObserver(decorateWorkers).observe($('#workerList'),{childList:true,subtree:true});
    document.addEventListener('click',e=>{const b=e.target.closest('[data-bio-worker]');if(b)openModal('enroll',b.dataset.bioWorker);const r=e.target.closest('[data-receipt]');if(r)setTimeout(()=>patchReceipt(r.dataset.receipt),60);if(e.target.closest('[data-go="delivery"]'))setTimeout(()=>{setMode('signature');resetVerification();},30);});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup);else setup();
})();
