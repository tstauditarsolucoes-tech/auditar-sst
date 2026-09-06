(() => {
  const CACHE='auditarEpiGestaoCacheV1';
  const HUMAN_SRC='https://cdn.jsdelivr.net/npm/@vladmandic/human@3.3.6/dist/human.js';
  const MODEL_BASE='https://cdn.jsdelivr.net/npm/@vladmandic/human@3.3.6/models';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const digits=(v='')=>String(v||'').replace(/\D/g,'');
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,9)}`;
  const now=()=>new Date().toISOString();
  let human=null,humanLoading=null,stream=null,enrollWorkerId='',standaloneEnrollment=false;

  function read(){
    try{
      const root=JSON.parse(localStorage.getItem(CACHE)||'{}');
      root.app=root.app&&typeof root.app==='object'?root.app:{};
      root.app.companies=Array.isArray(root.app.companies)?root.app.companies:[];
      root.app.workers=Array.isArray(root.app.workers)?root.app.workers:[];
      root.app.epis=Array.isArray(root.app.epis)?root.app.epis:[];
      root.app.deliveries=Array.isArray(root.app.deliveries)?root.app.deliveries:[];
      return root;
    }catch(_){return {app:{companies:[],workers:[],epis:[],deliveries:[]}};}
  }
  function write(root){root.updatedAt=now();localStorage.setItem(CACHE,JSON.stringify(root));}
  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);}
  function role(){return window.GestaoEpiAuth?.user?.()?.role||document.body.dataset.epiRole||'';}
  function canWrite(){const r=role();return r==='admin'||r==='campo';}
  function companyName(id,root=read()){return root.app.companies.find(c=>c.id===id)?.name||'—';}
  function deliveriesFor(workerId,root=read()){return root.app.deliveries.filter(d=>d.workerId===workerId&&d.cancelled!==true);}

  function styles(){
    if($('#pcExternalFaceStyles'))return;
    const s=document.createElement('style');s.id='pcExternalFaceStyles';s.textContent=`
      .pc-person-type{grid-column:1/-1}.pc-external-fields{display:none;grid-column:1/-1;grid-template-columns:1fr 1fr;gap:12px;padding:13px;border:1px solid #dbe8e5;border-radius:13px;background:#f7fbfa}.pc-external-fields.open{display:grid}.pc-external-fields .full{grid-column:1/-1}.pc-external-badge{display:inline-flex;align-items:center;gap:5px;border-radius:999px;padding:4px 8px;background:#fff6dc;color:#7b5a12;font-size:9px;font-weight:900}.pc-external-list{display:grid;gap:9px}.pc-external-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center;padding:12px;border:1px solid #dbe8e5;border-radius:13px;background:#fff}.pc-external-row b{display:block;color:#173d39}.pc-external-row small{display:block;color:#6c827e;margin-top:3px}.pc-external-actions{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}.pc-external-actions button{border:1px solid #c7dcd8;background:#f7fbfa;color:#315d57;border-radius:9px;padding:7px 9px;font-size:10px;font-weight:900;cursor:pointer}.pc-external-actions button.primaryx{background:#0f766e;color:white;border-color:#0f766e}.pc-face-enroll-status{padding:11px 12px;border-radius:11px;background:#f5faf9;border:1px solid #dceae7;color:#496660;font-size:11px;line-height:1.45}.pc-face-enroll-status.ok{background:#ecfdf3;border-color:#c7efd3;color:#166534}.pc-enroll-overlay{display:none;position:fixed;inset:0;z-index:12500;background:#062724;color:#fff;flex-direction:column}.pc-enroll-overlay.open{display:flex}.pc-enroll-head{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:15px 18px}.pc-enroll-head h2{margin:0;font-size:19px}.pc-enroll-head p{margin:4px 0 0;color:#c5dcd9;font-size:11px}.pc-enroll-close{width:44px;height:44px;border:0;border-radius:12px;background:rgba(255,255,255,.12);color:#fff;font-size:22px}.pc-enroll-stage{position:relative;flex:1;min-height:0;display:flex;align-items:center;justify-content:center;background:#041d1b;overflow:hidden}.pc-enroll-stage video{width:100%;height:100%;object-fit:cover;transform:scaleX(-1)}.pc-enroll-frame{position:absolute;width:min(52vw,340px);aspect-ratio:3/4;border:3px solid rgba(255,255,255,.9);border-radius:44%;box-shadow:0 0 0 9999px rgba(0,0,0,.24);pointer-events:none}.pc-enroll-tip{position:absolute;left:20px;right:20px;bottom:20px;background:rgba(5,31,29,.9);padding:12px 14px;border-radius:14px;text-align:center;font-weight:900}.pc-enroll-consent{padding:11px 18px;background:#0b3a36;display:flex;gap:8px;align-items:flex-start;color:#d0e3e0;font-size:10px}.pc-enroll-consent input{margin-top:1px}.pc-enroll-actions{padding:12px 18px 18px;background:#0b3a36;display:flex;justify-content:center}.pc-enroll-capture{min-width:250px;min-height:50px;border:0;border-radius:13px;background:#fff;color:#0f766e;font-weight:900;font-size:14px}.pc-enroll-capture:disabled{opacity:.55}
      @media(max-width:800px){.pc-external-fields{grid-template-columns:1fr}.pc-external-fields .full{grid-column:auto}.pc-external-row{grid-template-columns:1fr}.pc-external-actions{justify-content:flex-start}}
    `;document.head.appendChild(s);
  }

  function openView(id,title,sub){
    $$('.view').forEach(v=>v.classList.toggle('active',v.id===id));
    $$('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view===id));
    if($('#viewTitle'))$('#viewTitle').textContent=title||'';
    if($('#viewSub'))$('#viewSub').textContent=sub||'';
    if(id==='externalsPc')renderExternals();
    if(id==='faceEnrollPc')refreshEnrollView();
  }

  function addNav(view,label,icon,before){
    const nav=$('.sidebar nav');if(!nav||nav.querySelector(`[data-view="${view}"]`))return;
    const b=document.createElement('button');b.className='nav pc-new';b.dataset.view=view;b.innerHTML=`${icon} <span>${label}</span>`;
    const ref=before?nav.querySelector(`[data-view="${before}"]`):null;ref?nav.insertBefore(b,ref):nav.appendChild(b);
    b.addEventListener('click',()=>openView(view,view==='externalsPc'?'Externos / Terceiros':'Biometria facial',view==='externalsPc'?'Pessoas não contratadas com entrega de EPI.':'Cadastre ou atualize o rosto do trabalhador pelo computador.'));
  }

  function ensureViews(){
    const main=$('.main');if(!main)return false;
    if(!$('#externalsPc')){
      const s=document.createElement('section');s.id='externalsPc';s.className='view pc-modern-view';s.innerHTML=`<div class="pc-modern-head"><div><h2>Externos / Terceiros</h2><p>Prestadores, terceirizados, temporários e pessoas avulsas não entram como empregados contratados.</p></div><button id="pcExternalNewDelivery" class="primary" type="button">＋ Nova entrega para externo</button></div><div class="pc-card pc-grid"><label>Empresa onde o EPI foi entregue<select id="pcExternalCompany"></select></label><label>Buscar<input id="pcExternalSearch" placeholder="Nome, CPF ou empresa de origem"></label></div><div class="pc-card"><div id="pcExternalList" class="pc-external-list"></div></div>`;main.appendChild(s);
    }
    if(!$('#faceEnrollPc')){
      const s=document.createElement('section');s.id='faceEnrollPc';s.className='view pc-modern-view';s.innerHTML=`<div class="pc-modern-head"><div><h2>Cadastro de biometria facial</h2><p>Cadastre o rosto uma vez. A foto não é guardada e não é necessário piscar.</p></div></div><div class="pc-card pc-grid"><label>Empresa<select id="pcEnrollCompany"></select></label><label>Tipo<select id="pcEnrollType"><option value="all">Funcionários e externos</option><option value="employee">Somente funcionários</option><option value="external">Somente externos / terceiros</option></select></label><label class="full">Pessoa<select id="pcEnrollWorker"></select></label><div class="full"><div id="pcEnrollStatus" class="pc-face-enroll-status">Selecione uma pessoa para consultar a biometria.</div></div><div class="full pc-actions"><button id="pcEnrollStart" class="primary" type="button">🙂 Cadastrar / Atualizar rosto</button></div></div>`;main.appendChild(s);
    }
    addNav('externalsPc','Externos / Terceiros','👷','workers');
    if(canWrite())addNav('faceEnrollPc','Biometria facial','🙂','workers');
    bindViews();
    return true;
  }

  function enhanceDelivery(){
    const view=$('#newDeliveryPc');if(!view||$('#pcDeliveryPersonType'))return false;
    const grid=view.querySelector('.pc-card.pc-grid');if(!grid)return false;
    const companyLabel=$('#pcDeliveryCompany')?.closest('label');if(!companyLabel)return false;
    const type=document.createElement('label');type.className='pc-person-type';type.innerHTML=`Tipo de pessoa<select id="pcDeliveryPersonType"><option value="employee">Funcionário contratado</option><option value="third_party">Terceirizado / Prestador</option><option value="temporary">Temporário / Avulso</option></select>`;
    companyLabel.after(type);
    const searchLabel=$('#pcDeliverySearch')?.closest('label'),workerLabel=$('#pcDeliveryWorker')?.closest('label');
    searchLabel?.classList.add('pc-employee-only');workerLabel?.classList.add('pc-employee-only');
    const ext=document.createElement('div');ext.id='pcExternalDeliveryFields';ext.className='pc-external-fields';ext.innerHTML=`<label>Nome completo<input id="pcExternalName" placeholder="Nome da pessoa"></label><label>CPF / Documento<input id="pcExternalCpf" placeholder="Opcional, mas recomendado"></label><label>Empresa de origem<input id="pcExternalOrigin" placeholder="Ex.: Empresa prestadora"></label><label>Função / Atividade<input id="pcExternalRole" placeholder="Ex.: Eletricista, motorista"></label><label class="full">Observação do vínculo<input id="pcExternalRelationNote" placeholder="Ex.: Prestador de serviço na manutenção"></label><div class="full pc-actions"><span class="pc-hint">Esse registro fica separado como pessoa externa e não conta como empregado contratado.</span><button id="pcExternalEnrollHere" type="button" class="secondary">🙂 Cadastrar rosto deste externo</button></div>`;
    (workerLabel||type).after(ext);
    $('#pcDeliveryPersonType').addEventListener('change',toggleDeliveryType);
    $('#pcExternalEnrollHere').addEventListener('click',()=>{
      const prepared=prepareExternalWorker(true);if(!prepared.ok)return;
      beginEnrollment(prepared.workerId,false);
    });
    toggleDeliveryType();return true;
  }

  function toggleDeliveryType(){
    const t=$('#pcDeliveryPersonType')?.value||'employee',external=t!=='employee';
    $$('.pc-employee-only').forEach(el=>el.style.display=external?'none':'');
    $('#pcExternalDeliveryFields')?.classList.toggle('open',external);
    if(external){const sel=$('#pcDeliveryWorker');if(sel)sel.value='';}
  }

  function prepareExternalWorker(allowCreateForFace=false){
    const type=$('#pcDeliveryPersonType')?.value||'employee';
    if(type==='employee')return {ok:true,employee:true};
    if(!canWrite()){toast('Seu perfil não pode cadastrar pessoas externas.');return {ok:false};}
    const companyId=$('#pcDeliveryCompany')?.value||'',name=String($('#pcExternalName')?.value||'').trim(),cpf=String($('#pcExternalCpf')?.value||'').trim(),origin=String($('#pcExternalOrigin')?.value||'').trim(),job=String($('#pcExternalRole')?.value||'').trim(),note=String($('#pcExternalRelationNote')?.value||'').trim();
    if(!companyId){toast('Selecione a empresa onde o EPI será entregue.');return {ok:false};}
    if(!name){toast('Informe o nome da pessoa externa.');return {ok:false};}
    if(type==='third_party'&&!origin){toast('Informe a empresa de origem do terceirizado/prestador.');return {ok:false};}
    const root=read();const cpfDigits=digits(cpf);
    let w=root.app.workers.find(x=>x.workerType==='external'&&x.companyId===companyId&&((cpfDigits&&digits(x.cpf)===cpfDigits)||(!cpfDigits&&norm(x.name)===norm(name)&&norm(x.originCompany)===norm(origin))));
    const stamp=now();
    if(!w){
      w={id:uid('ext'),companyId,name,cpf,reg:'',role:job,sector:'Externo',active:false,workerType:'external',employmentType:'external',externalCategory:type,originCompany:origin,externalRelationNote:note,createdAt:stamp,updatedAt:stamp};root.app.workers.push(w);
    }else{
      w.name=name;w.cpf=cpf||w.cpf||'';w.role=job||w.role||'';w.originCompany=origin||w.originCompany||'';w.externalCategory=type;w.externalRelationNote=note||w.externalRelationNote||'';w.workerType='external';w.employmentType='external';w.active=false;w.updatedAt=stamp;
    }
    write(root);
    const sel=$('#pcDeliveryWorker');if(sel){let opt=[...sel.options].find(o=>o.value===w.id);if(!opt){opt=document.createElement('option');opt.value=w.id;opt.textContent=`${w.name} • Externo`;sel.appendChild(opt);}sel.value=w.id;}
    if(allowCreateForFace)toast('Pessoa externa preparada para cadastro facial.');
    return {ok:true,workerId:w.id,companyId,w};
  }

  function bindViews(){
    if($('#pcExternalNewDelivery')&&!$('#pcExternalNewDelivery').dataset.bound){$('#pcExternalNewDelivery').dataset.bound='1';$('#pcExternalNewDelivery').addEventListener('click',()=>openExternalDelivery());}
    $('#pcExternalCompany')?.addEventListener('change',renderExternals);$('#pcExternalSearch')?.addEventListener('input',renderExternals);
    $('#pcEnrollCompany')?.addEventListener('change',refreshEnrollWorkers);$('#pcEnrollType')?.addEventListener('change',refreshEnrollWorkers);$('#pcEnrollWorker')?.addEventListener('change',renderEnrollStatus);
    if($('#pcEnrollStart')&&!$('#pcEnrollStart').dataset.bound){$('#pcEnrollStart').dataset.bound='1';$('#pcEnrollStart').addEventListener('click',()=>{const id=$('#pcEnrollWorker')?.value||'';if(!id)return toast('Selecione a pessoa.');beginEnrollment(id,true);});}
  }

  function fillCompanySelect(sel,allLabel='Selecione a empresa'){
    if(!sel)return;const root=read(),old=sel.value;const rows=root.app.companies.slice().sort((a,b)=>String(a.name||'').localeCompare(String(b.name||'')));sel.innerHTML=`<option value="">${allLabel}</option>`+rows.map(c=>`<option value="${esc(c.id)}">${esc(c.name||'Empresa')}</option>`).join('');if(rows.some(c=>c.id===old))sel.value=old;
  }

  function renderExternals(){
    fillCompanySelect($('#pcExternalCompany'),'Todas as empresas');const root=read(),company=$('#pcExternalCompany')?.value||'',q=norm($('#pcExternalSearch')?.value||'');
    const rows=root.app.workers.filter(w=>w.workerType==='external'&&(!company||w.companyId===company)&&(!q||[w.name,w.cpf,w.originCompany,w.role].some(v=>norm(v).includes(q)))).sort((a,b)=>String(a.name||'').localeCompare(String(b.name||'')));
    const box=$('#pcExternalList');if(!box)return;
    if(!rows.length){box.innerHTML='<div class="empty">Nenhuma pessoa externa cadastrada. Ela será criada automaticamente na primeira entrega.</div>';return;}
    box.innerHTML=rows.map(w=>{const count=deliveriesFor(w.id,root).length,cat=w.externalCategory==='temporary'?'Temporário / Avulso':'Terceirizado / Prestador',bio=Array.isArray(w?.biometric?.embedding)&&w.biometric.embedding.length;return `<div class="pc-external-row"><div><b>${esc(w.name||'Pessoa externa')} <span class="pc-external-badge">${esc(cat)}</span></b><small>${esc(companyName(w.companyId,root))}${w.originCompany?` • Origem: ${esc(w.originCompany)}`:''}${w.role?` • ${esc(w.role)}`:''}</small><small>${w.cpf?`CPF/Doc.: ${esc(w.cpf)} • `:''}${count} entrega(s) • ${bio?'Biometria cadastrada':'Sem biometria'}</small></div><div class="pc-external-actions">${canWrite()?`<button type="button" data-ext-delivery="${esc(w.id)}" class="primaryx">＋ Entrega</button><button type="button" data-ext-face="${esc(w.id)}">🙂 ${bio?'Atualizar rosto':'Cadastrar rosto'}</button>`:''}</div></div>`;}).join('');
  }

  function openExternalDelivery(workerId=''){
    const root=read(),w=workerId?root.app.workers.find(x=>x.id===workerId):null;
    openView('newDeliveryPc','Nova entrega','Registre EPI para funcionário ou pessoa externa.');
    setTimeout(()=>{
      const type=$('#pcDeliveryPersonType');if(type)type.value=w?.externalCategory||'third_party';toggleDeliveryType();
      if(w){$('#pcDeliveryCompany').value=w.companyId||'';$('#pcExternalName').value=w.name||'';$('#pcExternalCpf').value=w.cpf||'';$('#pcExternalOrigin').value=w.originCompany||'';$('#pcExternalRole').value=w.role||'';$('#pcExternalRelationNote').value=w.externalRelationNote||'';prepareExternalWorker(false);}
    },30);
  }

  function refreshEnrollView(){fillCompanySelect($('#pcEnrollCompany'),'Todas as empresas');refreshEnrollWorkers();}
  function refreshEnrollWorkers(){
    const root=read(),company=$('#pcEnrollCompany')?.value||'',type=$('#pcEnrollType')?.value||'all',sel=$('#pcEnrollWorker');if(!sel)return;const old=sel.value;
    const rows=root.app.workers.filter(w=>{
      const external=w.workerType==='external';if(company&&w.companyId!==company)return false;if(type==='employee'&&external)return false;if(type==='external'&&!external)return false;if(!external&&w.active===false)return false;return true;
    }).sort((a,b)=>String(a.name||'').localeCompare(String(b.name||'')));
    sel.innerHTML='<option value="">Selecione a pessoa</option>'+rows.map(w=>`<option value="${esc(w.id)}">${esc(w.name||'Pessoa')}${w.workerType==='external'?' • EXTERNO':''}</option>`).join('');if(rows.some(w=>w.id===old))sel.value=old;renderEnrollStatus();
  }
  function renderEnrollStatus(){
    const id=$('#pcEnrollWorker')?.value||'',box=$('#pcEnrollStatus');if(!box)return;if(!id){box.className='pc-face-enroll-status';box.textContent='Selecione uma pessoa para consultar a biometria.';return;}const w=read().app.workers.find(x=>x.id===id),ok=Array.isArray(w?.biometric?.embedding)&&w.biometric.embedding.length;box.className='pc-face-enroll-status'+(ok?' ok':'');box.innerHTML=ok?`<b>✓ Biometria cadastrada</b><br>${w.biometric.enrolledAt?`Cadastrada em ${esc(new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(w.biometric.enrolledAt)))}`:'Rosto já cadastrado.'} • Você pode atualizar quando precisar.`:'Ainda não há biometria facial cadastrada para esta pessoa.';
  }

  async function loadHuman(){
    if(window.Human?.Human)return;if(document.querySelector('script[data-pc-enroll-human]')){await new Promise((resolve,reject)=>{const s=document.querySelector('script[data-pc-enroll-human]');if(window.Human?.Human)return resolve();s.addEventListener('load',resolve,{once:true});s.addEventListener('error',()=>reject(new Error('Falha ao carregar a biometria.')),{once:true});});return;}
    await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=HUMAN_SRC;s.dataset.pcEnrollHuman='1';s.onload=resolve;s.onerror=()=>reject(new Error('Falha ao carregar o motor biométrico. Verifique a internet.'));document.head.appendChild(s);});
  }
  async function ensureHuman(){
    if(human)return human;if(humanLoading)return humanLoading;humanLoading=(async()=>{await loadHuman();if(!window.Human?.Human)throw new Error('Motor biométrico não disponível.');human=new window.Human.Human({backend:'webgl',modelBasePath:MODEL_BASE,cacheSensitivity:0.01,filter:{enabled:true,equalization:true},face:{enabled:true,detector:{rotation:true,return:true,maxDetected:2,minConfidence:0.6},mesh:{enabled:true},description:{enabled:true},iris:{enabled:false},emotion:{enabled:false},antispoof:{enabled:false},liveness:{enabled:false}},body:{enabled:false},hand:{enabled:false},object:{enabled:false},gesture:{enabled:false}});await human.load();return human;})().catch(err=>{human=null;humanLoading=null;throw err;});return humanLoading;
  }
  function roundEmbedding(a){return Array.from(a||[]).map(n=>Math.round(Number(n)*1000000)/1000000);}

  function ensureOverlay(){
    if($('#pcEnrollOverlay'))return;const d=document.createElement('div');d.id='pcEnrollOverlay';d.className='pc-enroll-overlay';d.innerHTML=`<div class="pc-enroll-head"><div><h2>Cadastrar biometria facial</h2><p>Olhe normalmente para a câmera. Não precisa piscar, sorrir ou virar a cabeça.</p></div><button id="pcEnrollClose" class="pc-enroll-close" type="button">×</button></div><div class="pc-enroll-stage"><video id="pcEnrollVideo" autoplay muted playsinline></video><div class="pc-enroll-frame"></div><div class="pc-enroll-tip">Centralize somente o rosto da pessoa</div></div><label class="pc-enroll-consent"><input id="pcEnrollConsent" type="checkbox"><span>A pessoa foi informada sobre o cadastro da biometria facial para confirmação de entregas de EPI. A foto não será armazenada.</span></label><div class="pc-enroll-actions"><button id="pcEnrollCapture" class="pc-enroll-capture" type="button">🙂 Cadastrar rosto</button></div>`;document.body.appendChild(d);$('#pcEnrollClose').onclick=closeEnrollment;$('#pcEnrollCapture').onclick=captureEnrollment;
  }

  async function beginEnrollment(workerId,standalone=true){
    if(!canWrite())return toast('Seu perfil não pode cadastrar biometria.');const w=read().app.workers.find(x=>x.id===workerId);if(!w)return toast('Pessoa não encontrada.');enrollWorkerId=workerId;standaloneEnrollment=standalone;ensureOverlay();$('#pcEnrollConsent').checked=false;$('#pcEnrollOverlay').classList.add('open');const btn=$('#pcEnrollCapture');btn.disabled=true;btn.textContent='Carregando biometria…';
    try{await ensureHuman();if(!navigator.mediaDevices?.getUserMedia)throw new Error('A câmera não está disponível neste computador.');stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{width:{ideal:720},height:{ideal:900},facingMode:'user'}});const v=$('#pcEnrollVideo');v.srcObject=stream;await v.play();btn.disabled=false;btn.textContent='🙂 Cadastrar rosto';}catch(err){toast(err.message||'Não foi possível abrir a câmera.');closeEnrollment();}
  }
  function closeEnrollment(){if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}const v=$('#pcEnrollVideo');if(v)v.srcObject=null;$('#pcEnrollOverlay')?.classList.remove('open');enrollWorkerId='';}
  async function captureEnrollment(){
    if(!$('#pcEnrollConsent')?.checked)return toast('Confirme que a pessoa foi informada sobre o cadastro facial.');const video=$('#pcEnrollVideo'),btn=$('#pcEnrollCapture');if(!video?.videoWidth)return toast('Aguarde a câmera carregar.');btn.disabled=true;btn.textContent='Analisando rosto…';
    try{const engine=await ensureHuman(),c=document.createElement('canvas');c.width=Math.min(640,video.videoWidth);c.height=Math.max(1,Math.round(c.width*(video.videoHeight/video.videoWidth)));c.getContext('2d').drawImage(video,0,0,c.width,c.height);const result=await engine.detect(c),faces=result?.face||[];if(faces.length!==1)throw new Error(faces.length>1?'Deixe somente uma pessoa na câmera.':'Rosto não encontrado. Aproxime-se e melhore a iluminação.');const face=faces[0],score=Number(face.faceScore||face.boxScore||0);if(score<0.60)throw new Error('Não consegui ler o rosto com segurança. Tente novamente.');const embedding=roundEmbedding(face.embedding);if(!embedding.length)throw new Error('Não foi possível gerar a biometria facial.');const root=read(),w=root.app.workers.find(x=>x.id===enrollWorkerId);if(!w)throw new Error('Pessoa não encontrada.');w.biometric={type:'face-1to1',engine:'human-faceres',version:1,embedding,enrolledAt:now(),blinkRequired:false};w.updatedAt=now();write(root);const keep=standaloneEnrollment;closeEnrollment();toast('Biometria facial cadastrada. Não foi necessário piscar.');if(keep){setTimeout(()=>location.reload(),650);}else{renderExternals();}}
    catch(err){toast(err.message||'Falha ao cadastrar biometria.');}
    finally{btn.disabled=false;btn.textContent='🙂 Cadastrar rosto';}
  }

  document.addEventListener('click',e=>{
    const save=e.target.closest('#pcSaveDelivery');if(save){const type=$('#pcDeliveryPersonType')?.value||'employee';if(type!=='employee'){const r=prepareExternalWorker(false);if(!r.ok){e.preventDefault();e.stopImmediatePropagation();return;}}}
    const verify=e.target.closest('#pcFaceVerify');if(verify&&($('#pcDeliveryPersonType')?.value||'employee')!=='employee'){const r=prepareExternalWorker(false);if(!r.ok){e.preventDefault();e.stopImmediatePropagation();return;}}
    const del=e.target.closest('[data-ext-delivery]');if(del){e.preventDefault();openExternalDelivery(del.dataset.extDelivery);}
    const face=e.target.closest('[data-ext-face]');if(face){e.preventDefault();beginEnrollment(face.dataset.extFace,true);}
  },true);

  function boot(){styles();ensureOverlay();let tries=0;const timer=setInterval(()=>{tries++;const a=ensureViews(),b=enhanceDelivery();if(a&&b||tries>100){clearInterval(timer);refreshEnrollView();renderExternals();}},100);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();