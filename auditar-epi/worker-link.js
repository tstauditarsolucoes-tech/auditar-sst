(() => {
  const APP_KEY='auditarEpiV1';
  const STYLE_ID='gestaoEpiWorkerLinkStyles';
  const OPTIONS=[
    ['employee','Funcionário'],
    ['pending','Aguardando admissão'],
    ['third_party','Terceirizado'],
    ['temporary','Temporário'],
    ['visitor','Visitante / prestador']
  ];
  const $=(s,r=document)=>r.querySelector(s);
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;
  const now=()=>new Date().toISOString();
  const label=v=>OPTIONS.find(x=>x[0]===(v||'employee'))?.[1]||'Funcionário';
  const optionsHtml=(selected='employee')=>OPTIONS.map(([v,t])=>`<option value="${v}" ${v===selected?'selected':''}>${t}</option>`).join('');
  let pendingWorker=null,lastReceiptWorkerId='';

  function load(){try{return JSON.parse(localStorage.getItem(APP_KEY)||'{}');}catch{return {};}}
  function save(root){localStorage.setItem(APP_KEY,JSON.stringify(root));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed'));}
  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2400);}
  function roleAllowsQuick(){const r=document.body.dataset.epiRole;return !r||r==='admin'||r==='campo';}

  function ensureStyles(){
    if($('#'+STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .worker-link-badge{display:inline-flex;align-items:center;gap:5px;margin-top:5px;padding:4px 8px;border-radius:999px;background:#edf7f5;color:#17665e;font-size:10px;font-weight:850}
      .worker-link-edit{margin-left:6px;border:0;background:transparent;color:#0f766e;font-size:10px;font-weight:900;text-decoration:underline;cursor:pointer}
      .quick-worker-btn{width:100%;margin-top:8px}
      .worker-link-modal{position:fixed;inset:0;z-index:26000;background:rgba(8,35,32,.72);display:none;align-items:center;justify-content:center;padding:18px}.worker-link-modal.open{display:flex}.worker-link-card{width:min(500px,100%);max-height:90vh;overflow:auto;background:#fff;border-radius:22px;padding:20px;box-shadow:0 24px 70px rgba(0,0,0,.22)}.worker-link-card h2{margin:0;color:#173d39}.worker-link-card p{color:#617b77;font-size:12px;line-height:1.45}.worker-link-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.worker-link-grid label{display:grid;gap:5px;font-size:11px;font-weight:850;color:#355b57}.worker-link-grid .full{grid-column:1/-1}.worker-link-grid input,.worker-link-grid select{width:100%;box-sizing:border-box;min-height:46px;border:1px solid #cededa;border-radius:12px;padding:0 12px}.worker-link-actions{display:flex;gap:9px;justify-content:flex-end;margin-top:16px}.worker-link-actions button{min-height:46px;border-radius:12px;padding:0 16px;font-weight:900;border:1px solid #cfe0dd;background:#fff}.worker-link-actions .primary{border:0;background:#0f766e;color:#fff}@media(max-width:520px){.worker-link-grid{grid-template-columns:1fr}.worker-link-grid .full{grid-column:auto}}
    `;document.head.appendChild(s);
  }

  function injectWorkerField(){
    const form=$('#workerForm');if(!form||$('#workerLinkType'))return;
    const btn=form.querySelector('button[type="submit"]');
    const lab=document.createElement('label');lab.innerHTML=`Tipo de vínculo<select id="workerLinkType">${optionsHtml('employee')}</select>`;
    if(btn)form.insertBefore(lab,btn);else form.appendChild(lab);
    form.addEventListener('submit',()=>{
      pendingWorker={companyId:$('#workerCompany')?.value||'',name:($('#workerName')?.value||'').trim(),cpf:($('#workerCpf')?.value||'').trim(),linkType:$('#workerLinkType')?.value||'employee'};
      setTimeout(applyPendingWorker,40);
    },true);
  }

  function applyPendingWorker(){
    if(!pendingWorker)return;
    const root=load();root.workers=Array.isArray(root.workers)?root.workers:[];
    const rows=root.workers.filter(w=>w.companyId===pendingWorker.companyId&&String(w.name||'').trim()===pendingWorker.name);
    const w=rows.sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')))[0];
    if(w){w.linkType=pendingWorker.linkType;w.updatedAt=now();save(root);renderWorkerBadges();}
    pendingWorker=null;
  }

  function quickModal(){
    if($('#quickWorkerLinkModal'))return $('#quickWorkerLinkModal');
    const d=document.createElement('div');d.id='quickWorkerLinkModal';d.className='worker-link-modal';d.innerHTML=`<div class="worker-link-card"><h2>Cadastrar pessoa agora</h2><p>Cadastre sem sair da entrega. Depois ela já fica selecionada para receber o EPI.</p><div class="worker-link-grid"><label class="full">Nome completo<input id="qwName"></label><label>CPF<input id="qwCpf" inputmode="numeric"></label><label>Matrícula<input id="qwReg"></label><label>Cargo / atividade<input id="qwRole"></label><label>Setor<input id="qwSector"></label><label class="full">Tipo de vínculo<select id="qwLink">${optionsHtml('pending')}</select></label></div><div class="worker-link-actions"><button id="qwCancel" type="button">Cancelar</button><button id="qwSave" class="primary" type="button">Salvar e selecionar</button></div></div>`;document.body.appendChild(d);$('#qwCancel').onclick=()=>d.classList.remove('open');$('#qwSave').onclick=saveQuickWorker;return d;
  }

  function injectQuickButton(){
    const box=$('#delivery .worker-search-box');if(!box||$('#btnQuickWorker')||!roleAllowsQuick())return;
    const b=document.createElement('button');b.id='btnQuickWorker';b.type='button';b.className='secondary quick-worker-btn';b.textContent='＋ Cadastrar pessoa agora';b.onclick=()=>{
      if(!$('#deliveryCompany')?.value)return toast('Selecione a empresa primeiro.');
      const d=quickModal();['#qwName','#qwCpf','#qwReg','#qwRole','#qwSector'].forEach(s=>{$(s).value='';});$('#qwLink').value='pending';d.classList.add('open');setTimeout(()=>$('#qwName')?.focus(),50);
    };box.appendChild(b);
  }

  function saveQuickWorker(){
    const companyId=$('#deliveryCompany')?.value||'',name=($('#qwName')?.value||'').trim();if(!companyId)return toast('Selecione a empresa.');if(!name)return toast('Informe o nome.');
    const rootBefore=load(),before=new Set((rootBefore.workers||[]).map(w=>w.id));
    $('#workerCompany').value=companyId;$('#workerName').value=name;$('#workerCpf').value=$('#qwCpf').value.trim();$('#workerReg').value=$('#qwReg').value.trim();$('#workerRole').value=$('#qwRole').value.trim();$('#workerSector').value=$('#qwSector').value.trim();$('#workerLinkType').value=$('#qwLink').value||'pending';
    $('#workerForm').requestSubmit();
    setTimeout(()=>{
      const root=load();const w=(root.workers||[]).filter(x=>!before.has(x.id)).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')))[0];
      if(w){const sel=$('#deliveryWorker');if(sel){sel.value=w.id;sel.dispatchEvent(new Event('change',{bubbles:true}));}lastReceiptWorkerId=w.id;toast('Pessoa cadastrada e selecionada.');}
      $('#quickWorkerLinkModal')?.classList.remove('open');
    },120);
  }

  function editModal(){
    if($('#editWorkerLinkModal'))return $('#editWorkerLinkModal');
    const d=document.createElement('div');d.id='editWorkerLinkModal';d.className='worker-link-modal';d.innerHTML=`<div class="worker-link-card"><h2>Alterar vínculo</h2><p id="ewName"></p><div class="worker-link-grid"><label class="full">Tipo de vínculo<select id="ewLink">${optionsHtml()}</select></label></div><div class="worker-link-actions"><button id="ewCancel" type="button">Cancelar</button><button id="ewSave" class="primary" type="button">Salvar</button></div></div>`;document.body.appendChild(d);$('#ewCancel').onclick=()=>d.classList.remove('open');$('#ewSave').onclick=()=>{const id=d.dataset.workerId,root=load(),w=(root.workers||[]).find(x=>x.id===id);if(!w)return;w.linkType=$('#ewLink').value;w.updatedAt=now();save(root);d.classList.remove('open');renderWorkerBadges();toast('Vínculo atualizado.');};return d;
  }

  function renderWorkerBadges(){
    const list=$('#workerList');if(!list)return;const root=load();const workers=root.workers||[];
    list.querySelectorAll('.list-item').forEach(item=>{
      if(item.dataset.workerLinkDone==='1')return;
      const name=item.querySelector('.list-main b')?.textContent?.trim()||'';const small=item.querySelector('.list-main small')?.textContent||'';
      const w=workers.find(x=>String(x.name||'').trim()===name&&small.includes((root.companies||[]).find(c=>c.id===x.companyId)?.name||''));if(!w)return;
      item.dataset.workerLinkDone='1';const wrap=document.createElement('div');wrap.innerHTML=`<span class="worker-link-badge">${esc(label(w.linkType))}</span><button class="worker-link-edit" type="button">Alterar vínculo</button>`;const main=item.querySelector('.list-main');main?.appendChild(wrap);wrap.querySelector('button').onclick=()=>{const d=editModal();d.dataset.workerId=w.id;$('#ewName').textContent=w.name;$('#ewLink').value=w.linkType||'employee';d.classList.add('open');};
    });
  }

  function captureReceiptWorker(){
    $('#btnSaveDelivery')?.addEventListener('click',()=>{lastReceiptWorkerId=$('#deliveryWorker')?.value||'';},true);
    document.addEventListener('click',e=>{const b=e.target.closest('[data-receipt]');if(!b)return;const root=load(),d=(root.deliveries||[]).find(x=>x.id===b.dataset.receipt);if(d)lastReceiptWorkerId=d.workerId||'';},true);
    const box=$('#receiptContent');if(box)new MutationObserver(()=>injectReceiptLink()).observe(box,{childList:true,subtree:true});
  }
  function injectReceiptLink(){
    const box=$('#receiptContent');if(!box||box.querySelector('[data-worker-link-meta]')||!lastReceiptWorkerId)return;const root=load(),w=(root.workers||[]).find(x=>x.id===lastReceiptWorkerId);if(!w)return;const meta=box.querySelector('.receipt-meta');if(!meta)return;const div=document.createElement('div');div.dataset.workerLinkMeta='1';div.innerHTML=`<b>Vínculo</b><br>${esc(label(w.linkType))}`;meta.appendChild(div);
  }

  function init(){ensureStyles();injectWorkerField();injectQuickButton();captureReceiptWorker();renderWorkerBadges();const list=$('#workerList');if(list)new MutationObserver(renderWorkerBadges).observe(list,{childList:true,subtree:true});document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(injectQuickButton,50));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();