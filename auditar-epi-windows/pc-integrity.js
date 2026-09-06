(() => {
  const CACHE='auditarEpiGestaoCacheV1';
  const PENDING='gestaoEpiPcPendingReloadV220';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,9)}`;
  const now=()=>new Date().toISOString();

  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);}
  function read(){
    try{
      const root=JSON.parse(localStorage.getItem(CACHE)||'{}');
      root.app=root.app&&typeof root.app==='object'?root.app:{};
      root.app.companies=Array.isArray(root.app.companies)?root.app.companies:[];
      root.app.workers=Array.isArray(root.app.workers)?root.app.workers:[];
      root.app.epis=Array.isArray(root.app.epis)?root.app.epis:[];
      root.app.deliveries=Array.isArray(root.app.deliveries)?root.app.deliveries:[];
      root.stock=root.stock&&typeof root.stock==='object'?root.stock:{};
      root.stock.movements=Array.isArray(root.stock.movements)?root.stock.movements:[];
      root.stock.minimums=root.stock.minimums&&typeof root.stock.minimums==='object'?root.stock.minimums:{};
      root.stock.processedDeliveryIds=Array.isArray(root.stock.processedDeliveryIds)?root.stock.processedDeliveryIds:[];
      return root;
    }catch(_){return {version:1,revision:0,updatedAt:'',app:{companies:[],workers:[],epis:[],deliveries:[]},stock:{startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}}};}
  }
  function writeAndReload(root,message,receiptId=''){
    root.updatedAt=now();
    localStorage.setItem(CACHE,JSON.stringify(root));
    sessionStorage.setItem(PENDING,JSON.stringify({message,receiptId,at:Date.now()}));
    setTimeout(()=>location.reload(),70);
  }

  function currentRole(){return window.GestaoEpiAuth?.user?.()?.role||document.body.dataset.epiRole||'';}
  function canAdmin(){return currentRole()==='admin';}
  function canDeliver(){const r=currentRole();return r==='admin'||r==='campo';}
  function isConfirmedFace(d){return d?.biometricVerified===true||((d?.confirmationType==='face-1to1'||d?.confirmationMethod==='face-biometric')&&Boolean(d?.biometricVerifiedAt||d?.facialVerifiedAt));}

  function applyPermissions(){
    const role=currentRole(),admin=role==='admin',deliver=role==='admin'||role==='campo';
    const set=(sel,show)=>$$(sel).forEach(el=>{el.style.display=show?'':'none';});
    set('.nav[data-view="importWorkersPc"]',admin);set('[data-pc-go="importWorkersPc"]',admin);set('[data-pc-go="epis"]',admin);
    set('.nav[data-view="newDeliveryPc"]',deliver);set('[data-pc-go="newDeliveryPc"]',deliver);
    if($('#importWorkersPc')?.classList.contains('active')&&!admin)document.querySelector('.nav[data-view="dashboard"]')?.click();
    if($('#newDeliveryPc')?.classList.contains('active')&&!deliver)document.querySelector('.nav[data-view="dashboard"]')?.click();
    const v=$('.pc-version');if(v)v.textContent='PC v2.2.0';
  }

  function previewRows(){
    return $$('#pcImportPreview tbody tr').map(tr=>{const t=[...tr.querySelectorAll('td')].map(td=>String(td.textContent||'').trim()).map(v=>v==='—'?'':v);return{name:t[0]||'',cpf:t[1]||'',reg:t[2]||'',role:t[3]||'',sector:t[4]||''};}).filter(x=>x.name);
  }

  function importWorkers(){
    if(!canAdmin())return toast('Somente o Administrador pode importar funcionários.');
    const companyId=$('#pcImportCompany')?.value||'',rows=previewRows();if(!companyId)return toast('Selecione a empresa.');if(!rows.length)return toast('Nenhum funcionário pronto para cadastrar.');
    const root=read();let added=0,skipped=0;
    for(const row of rows){
      const same=root.app.workers.some(w=>w.companyId===companyId&&((row.cpf&&String(w.cpf||'').replace(/\D/g,'')===String(row.cpf).replace(/\D/g,''))||(norm(w.name)===norm(row.name)&&(!row.reg||norm(w.reg)===norm(row.reg)))));
      if(same){skipped++;continue;}
      root.app.workers.push({id:uid('w'),companyId,name:row.name.trim(),cpf:row.cpf.trim(),reg:row.reg.trim(),role:row.role.trim(),sector:row.sector.trim(),active:true,createdAt:now(),updatedAt:now()});added++;
    }
    writeAndReload(root,`${added} funcionário(s) cadastrado(s)${skipped?` • ${skipped} já existia(m)`:''}.`);
  }

  function canvasHasInk(canvas){
    try{const d=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;for(let i=3;i<d.length;i+=4)if(d[i]>12)return true;return false;}catch(_){return false;}
  }
  function stockKey(companyId,epiId){return `${companyId}::${epiId}`;}

  function saveDelivery(){
    if(!canDeliver())return toast('Seu perfil não tem permissão para registrar entrega.');
    const root=read(),companyId=$('#pcDeliveryCompany')?.value||'',workerId=$('#pcDeliveryWorker')?.value||'';
    if(!companyId)return toast('Selecione a empresa.');if(!workerId)return toast('Selecione o trabalhador.');
    const worker=root.app.workers.find(w=>w.id===workerId);if(!worker||worker.companyId!==companyId)return toast('O trabalhador não pertence à empresa selecionada.');
    const items=$$('.pc-delivery-item').map(r=>({epiId:r.querySelector('.pc-item-epi')?.value||'',qty:Math.max(0,Number(r.querySelector('.pc-item-qty')?.value||0))})).filter(i=>i.epiId&&i.qty>0);if(!items.length)return toast('Adicione pelo menos um EPI.');
    const guard=window.GestaoEpiV270Guard?.validateDelivery?.(root,companyId,worker,items);
    if(guard?.ok===false)return toast(guard.message||'Entrega bloqueada por uma validação de segurança.');
    if(guard?.confirm&&!window.confirm(guard.confirm))return;
    const face=window.GestaoEpiPcFace?.getConfirmation?.()||{mode:'signature',valid:true,confirmationType:'signature'};
    const canvas=$('#pcSignature');
    if(face.mode==='face'&&!face.valid)return toast('Faça a verificação biométrica do trabalhador antes de finalizar.');
    if(face.mode!=='face'&&(!canvas||!canvasHasInk(canvas)))return toast('Colete a assinatura do trabalhador.');

    const createdAt=now(),delivery={
      id:uid('d'),companyId,workerId,reason:$('#pcDeliveryReason')?.value||'Primeira entrega',responsible:String($('#pcDeliveryResponsible')?.value||'').trim(),notes:String($('#pcDeliveryNotes')?.value||'').trim(),items,
      signature:face.mode==='face'?'':canvas.toDataURL('image/png'),confirmationType:face.mode==='face'?'face-1to1':'signature',confirmationMethod:face.mode==='face'?'face-biometric':'signature',source:'pc',createdAt,updatedAt:createdAt
    };
    if(face.mode==='face'){
      delivery.biometricVerified=true;delivery.biometricSimilarity=Math.round(Number(face.facialSimilarity||0)*10000)/10000;delivery.biometricThreshold=0.60;delivery.biometricVerifiedAt=face.facialVerifiedAt||createdAt;delivery.biometricWorkerId=workerId;delivery.biometricEngine=face.biometricEngine||'human-faceres';delivery.biometricVersion=face.biometricVersion||1;delivery.facialBlinkRequired=false;
    }

    root.app.deliveries.unshift(delivery);
    if(!root.stock.startedAt)root.stock.startedAt=createdAt;
    const totals={};for(const item of items)totals[item.epiId]=(totals[item.epiId]||0)+Number(item.qty||0);
    for(const [epiId,qty] of Object.entries(totals)){
      root.stock.movements.unshift({id:uid('sm'),type:'OUT',delta:-qty,companyId,epiId,deliveryId:delivery.id,workerId,note:`Entrega para ${worker.name||'trabalhador'}`,createdAt,updatedAt:createdAt});
      const key=stockKey(companyId,epiId);if(root.stock.minimums[key]==null)root.stock.minimums[key]=5;
    }
    if(!root.stock.processedDeliveryIds.includes(delivery.id))root.stock.processedDeliveryIds.push(delivery.id);
    root.stock.processedDeliveryIds=root.stock.processedDeliveryIds.slice(-5000);
    writeAndReload(root,'Entrega registrada e estoque atualizado.',delivery.id);
  }

  function patchFaceReceipt(id){
    setTimeout(()=>{
      const root=read(),d=root.app.deliveries.find(x=>x.id===id);if(!d||!isConfirmedFace(d))return;const paper=$('#pcReceiptPaper');if(!paper)return;const w=root.app.workers.find(x=>x.id===d.workerId)||{};const pct=Math.round(Number(d.biometricSimilarity||d.facialSimilarity||0)*100);const at=d.biometricVerifiedAt||d.facialVerifiedAt;
      const sign=paper.querySelector('.pc-receipt-sign');if(sign)sign.innerHTML=`<div class="pc-face-proof"><b>✓ Confirmação biométrica facial</b><br>Rosto comparado com a biometria cadastrada do trabalhador${pct?` • compatibilidade ${pct}%`:''}${at?` • ${esc(new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(at)))}`:''}.<br>A foto da verificação não foi armazenada e não foi exigido piscar.</div><div class="line">${esc(w.name||'Trabalhador')}<br>Biometria facial verificada</div>`;
    },80);
  }

  function renderConfirmationPending(){
    const box=$('#pendingSignature');if(!box)return;const root=read(),company=$('#globalCompany')?.value||'';const invalid=root.app.deliveries.filter(d=>(!company||d.companyId===company)&&!String(d.signature||'').trim()&&!isConfirmedFace(d));
    const head=box.closest('.panel')?.querySelector('.panel-head h2');if(head)head.textContent='✍️ Entregas sem confirmação';const sub=box.closest('.panel')?.querySelector('.panel-head p');if(sub)sub.textContent='Registros sem assinatura ou biometria facial verificada.';
    if(!invalid.length){box.innerHTML='<div class="empty">Nenhuma entrega sem confirmação.</div>';return;}
    box.innerHTML=`<table class="data-table"><thead><tr><th>Data</th><th>Colaborador</th><th>Situação</th></tr></thead><tbody>${invalid.slice(0,12).map(d=>{const w=root.app.workers.find(x=>x.id===d.workerId)||{};let date='—';try{date=new Intl.DateTimeFormat('pt-BR',{dateStyle:'short'}).format(new Date(d.createdAt));}catch(_){}return `<tr><td>${esc(date)}</td><td>${esc(w.name||'Colaborador')}</td><td><span class="status low">Sem confirmação</span></td></tr>`;}).join('')}</tbody></table>`;
  }

  function afterReload(){
    let pending=null;try{pending=JSON.parse(sessionStorage.getItem(PENDING)||'null');}catch(_){}if(!pending)return;sessionStorage.removeItem(PENDING);setTimeout(()=>toast(pending.message||'Dados salvos.'),650);
  }

  document.addEventListener('click',e=>{
    const imp=e.target.closest('#pcImportCommit');if(imp){e.preventDefault();e.stopImmediatePropagation();importWorkers();return;}
    const save=e.target.closest('#pcSaveDelivery');if(save){e.preventDefault();e.stopImmediatePropagation();saveDelivery();return;}
    const nav=e.target.closest('.nav[data-view], [data-pc-go]');if(nav){const id=nav.dataset.view||nav.dataset.pcGo;if(id==='importWorkersPc'&&!canAdmin()){e.preventDefault();e.stopImmediatePropagation();toast('Somente o Administrador pode importar funcionários.');return;}if(id==='newDeliveryPc'&&!canDeliver()){e.preventDefault();e.stopImmediatePropagation();toast('Seu perfil não pode registrar entregas.');return;}}
    const receipt=e.target.closest('[data-pc-receipt]');if(receipt)patchFaceReceipt(receipt.dataset.pcReceipt);
    if(e.target.closest('.nav[data-view="pending"]'))setTimeout(renderConfirmationPending,80);
  },true);

  function boot(){applyPermissions();afterReload();setTimeout(renderConfirmationPending,500);new MutationObserver(()=>applyPermissions()).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['data-epi-role']});const pending=$('#pendingSignature');if(pending)new MutationObserver(()=>setTimeout(renderConfirmationPending,0)).observe(pending,{childList:true,subtree:true});window.addEventListener('storage',e=>{if(e.key===CACHE)setTimeout(renderConfirmationPending,0);});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();