(() => {
  const CACHE='auditarEpiGestaoCacheV1';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  let currentWorkerId='';
  let decorateQueued=false;

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

  function companyName(id,root){return root.app.companies.find(c=>c.id===id)?.name||'—';}
  function companyCnpj(id,root){return root.app.companies.find(c=>c.id===id)?.cnpj||'';}
  function epiById(id,root){return root.app.epis.find(e=>e.id===id)||{};}
  function fmtDate(iso,withTime=false){if(!iso)return '—';try{return new Intl.DateTimeFormat('pt-BR',withTime?{dateStyle:'short',timeStyle:'short'}:{dateStyle:'short'}).format(new Date(iso));}catch(_){return String(iso);}}
  function confirmationLabel(d){
    if(d?.biometricVerified===true||d?.confirmationType==='face-1to1'||d?.confirmationMethod==='face-biometric'){
      const pct=Math.round(Number(d.biometricSimilarity||d.facialSimilarity||0)*100);
      return `<span class="worker-sheet-confirm face">✓ Facial${pct?` • ${pct}%`:''}</span>`;
    }
    if(String(d?.signature||'').trim())return '<span class="worker-sheet-confirm sign">✓ Assinatura</span>';
    return '<span class="worker-sheet-confirm missing">Sem confirmação</span>';
  }

  function styles(){
    if($('#workerSheetStyles'))return;
    const s=document.createElement('style');
    s.id='workerSheetStyles';
    s.textContent=`
      .worker-sheet-btn{border:1px solid #bcd4cf;background:#eef8f6;color:#0f766e;border-radius:9px;padding:7px 10px;font-weight:900;font-size:11px;cursor:pointer;white-space:nowrap}
      .worker-sheet-view{display:none}.worker-sheet-view.active{display:block}
      .worker-sheet-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}.worker-sheet-toolbar .actions{display:flex;gap:8px;flex-wrap:wrap}
      .worker-sheet-paper{background:#fff;border:1px solid #dbe7e4;border-radius:16px;padding:24px;box-shadow:0 8px 28px rgba(22,61,56,.05)}
      .worker-sheet-title{text-align:center;margin-bottom:18px}.worker-sheet-title h1{font-size:21px;margin:0;color:#173d39}.worker-sheet-title p{font-size:11px;color:#6d817e;margin:5px 0 0}
      .worker-sheet-company{text-align:center;font-size:12px;color:#435e59;margin-bottom:18px}.worker-sheet-company b{font-size:14px;color:#173d39}
      .worker-sheet-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-bottom:16px}.worker-sheet-grid>div{border:1px solid #dce7e5;border-radius:10px;padding:10px;min-height:46px}.worker-sheet-grid small{display:block;color:#758985;font-size:9px;text-transform:uppercase;font-weight:900;margin-bottom:3px}.worker-sheet-grid b{display:block;color:#173d39;font-size:11px;word-break:break-word}
      .worker-sheet-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin:14px 0}.worker-sheet-metric{background:#f5faf9;border:1px solid #dceae7;border-radius:12px;padding:11px}.worker-sheet-metric strong{display:block;font-size:20px;color:#173d39}.worker-sheet-metric span{font-size:10px;color:#718681}
      .worker-sheet-section{margin-top:20px}.worker-sheet-section h2{font-size:14px;color:#173d39;margin:0 0 9px}.worker-sheet-table{width:100%;border-collapse:collapse;font-size:10px}.worker-sheet-table th,.worker-sheet-table td{border:1px solid #d7e3e0;padding:8px;vertical-align:top;text-align:left}.worker-sheet-table th{background:#f1f7f6;color:#4d6863;font-size:9px;text-transform:uppercase}.worker-sheet-table .epi-lines{display:grid;gap:5px}.worker-sheet-table .epi-line b{display:block;color:#173d39}.worker-sheet-table .epi-line small{color:#718681}.worker-sheet-confirm{display:inline-block;border-radius:8px;padding:5px 7px;font-weight:900;font-size:9px}.worker-sheet-confirm.face{background:#ecfdf3;color:#166534}.worker-sheet-confirm.sign{background:#eef8f6;color:#0f766e}.worker-sheet-confirm.missing{background:#fff0ee;color:#b42318}
      .worker-sheet-signatures{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:10px}.worker-sheet-proof{border:1px solid #dce7e5;border-radius:10px;padding:10px}.worker-sheet-proof small{color:#6d817e}.worker-sheet-proof img{display:block;max-width:220px;max-height:80px;margin:8px auto 0}.worker-sheet-face-proof{margin-top:8px;padding:8px;border-radius:8px;background:#ecfdf3;color:#166534;font-size:10px;font-weight:850;text-align:center}.worker-sheet-empty{padding:24px;border:1px dashed #c9d9d6;border-radius:12px;text-align:center;color:#728682;font-size:11px}.worker-sheet-note{margin-top:18px;border-top:1px solid #dce7e5;padding-top:14px;color:#506964;font-size:10px;line-height:1.5}
      @media(max-width:980px){.worker-sheet-grid,.worker-sheet-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.worker-sheet-signatures{grid-template-columns:1fr}}
      @media print{
        body *{visibility:hidden!important}.worker-sheet-paper,.worker-sheet-paper *{visibility:visible!important}.worker-sheet-paper{position:absolute!important;left:0!important;top:0!important;width:100%!important;max-width:none!important;border:0!important;box-shadow:none!important;border-radius:0!important;padding:12mm!important;box-sizing:border-box!important}.worker-sheet-toolbar,.sidebar,.topbar{display:none!important}.worker-sheet-table{font-size:9px}.worker-sheet-grid,.worker-sheet-metrics{break-inside:avoid}.worker-sheet-proof{break-inside:avoid}
      }
    `;
    document.head.appendChild(s);
  }

  function ensureView(){
    const main=$('.main');if(!main||$('#workerSheetPc'))return;
    const sec=document.createElement('section');
    sec.id='workerSheetPc';
    sec.className='view worker-sheet-view';
    sec.innerHTML=`
      <div class="worker-sheet-toolbar">
        <div><h2 style="margin:0;color:#173d39">Ficha individual de EPI</h2><p style="margin:4px 0 0;color:#6c827e;font-size:11px">Histórico completo do trabalhador.</p></div>
        <div class="actions"><button id="workerSheetBack" class="secondary" type="button">← Voltar</button><button id="workerSheetPrint" class="primary" type="button">🖨️ Imprimir / Salvar PDF</button></div>
      </div>
      <article id="workerSheetPaper" class="worker-sheet-paper"></article>`;
    main.appendChild(sec);
    $('#workerSheetBack').addEventListener('click',()=>document.querySelector('.nav[data-view="workers"]')?.click());
    $('#workerSheetPrint').addEventListener('click',()=>window.print());
  }

  function visibleWorkers(root){
    const company=$('#globalCompany')?.value||'';
    const q=norm($('#workerSearch')?.value||'');
    return root.app.workers.filter(w=>w.active!==false&&(!company||w.companyId===company)&&(!q||[w.name,w.cpf,w.reg,w.role,w.sector].some(v=>norm(v).includes(q)))).sort((a,b)=>String(a.name||'').localeCompare(String(b.name||'')));
  }

  function decorateWorkers(){
    decorateQueued=false;
    const table=$('#workerTable table');if(!table)return;
    const root=read(),workers=visibleWorkers(root),head=table.querySelector('thead tr');
    if(head&&!head.querySelector('[data-worker-sheet-head]')){const th=document.createElement('th');th.dataset.workerSheetHead='1';th.textContent='Ficha';head.appendChild(th);}
    const rows=[...table.querySelectorAll('tbody tr')];
    rows.forEach((tr,i)=>{
      if(tr.querySelector('[data-worker-sheet]'))return;
      const w=workers[i];if(!w)return;
      const td=document.createElement('td');
      td.innerHTML=`<button type="button" class="worker-sheet-btn" data-worker-sheet="${esc(w.id)}">Ver ficha</button>`;
      tr.appendChild(td);
    });
  }

  function queueDecorate(){if(decorateQueued)return;decorateQueued=true;setTimeout(decorateWorkers,0);}

  function renderSheet(workerId){
    const root=read(),w=root.app.workers.find(x=>x.id===workerId);if(!w)return;
    currentWorkerId=workerId;
    const c=root.app.companies.find(x=>x.id===w.companyId)||{};
    const deliveries=root.app.deliveries.filter(d=>d.workerId===workerId&&d.cancelled!==true).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')));
    const totalUnits=deliveries.reduce((sum,d)=>sum+(d.items||[]).reduce((s,i)=>s+Number(i.qty||0),0),0);
    const uniqueEpis=new Set();deliveries.forEach(d=>(d.items||[]).forEach(i=>uniqueEpis.add(i.epiId)));
    const first=deliveries.length?deliveries[deliveries.length-1].createdAt:'';
    const last=deliveries.length?deliveries[0].createdAt:'';

    const rows=deliveries.map(d=>{
      const lines=(d.items||[]).map(i=>{const e=epiById(i.epiId,root);return `<div class="epi-line"><b>${esc(e.name||'EPI')}</b><small>${e.ca?`CA ${esc(e.ca)}`:'CA não informado'}${e.model?` • ${esc(e.model)}`:''}${e.size?` • Tam. ${esc(e.size)}`:''} • Qtd. ${Number(i.qty||0)}</small></div>`;}).join('');
      return `<tr><td>${fmtDate(d.createdAt,true)}</td><td><div class="epi-lines">${lines||'—'}</div></td><td>${esc(d.reason||'—')}</td><td>${esc(d.responsible||'—')}</td><td>${confirmationLabel(d)}</td></tr>`;
    }).join('');

    const proofs=deliveries.filter(d=>String(d.signature||'').trim()||d.biometricVerified===true||d.confirmationType==='face-1to1'||d.confirmationMethod==='face-biometric').map(d=>{
      const face=d.biometricVerified===true||d.confirmationType==='face-1to1'||d.confirmationMethod==='face-biometric';
      const pct=Math.round(Number(d.biometricSimilarity||d.facialSimilarity||0)*100);
      return `<div class="worker-sheet-proof"><b>${fmtDate(d.createdAt,true)}</b><br><small>${esc(d.reason||'Entrega de EPI')}</small>${face?`<div class="worker-sheet-face-proof">✓ Biometria facial verificada${pct?` • ${pct}%`:''}<br>Sem exigência de piscar</div>`:`<img src="${d.signature}" alt="Assinatura do trabalhador">`}</div>`;
    }).join('');

    const lastByEpi=new Map();
    deliveries.slice().sort((a,b)=>String(a.createdAt||'').localeCompare(String(b.createdAt||''))).forEach(d=>(d.items||[]).forEach(i=>lastByEpi.set(i.epiId,{delivery:d,item:i})));
    const cycles=[...lastByEpi.entries()].map(([epiId,x])=>{const e=epiById(epiId,root),cycle=Number(e.cycle||0);if(!cycle)return null;const dt=new Date(x.delivery.createdAt);if(Number.isNaN(dt.getTime()))return null;const next=new Date(dt.getTime()+cycle*86400000);return {e,cycle,last:x.delivery.createdAt,next};}).filter(Boolean).sort((a,b)=>a.next-b.next);
    const cycleRows=cycles.map(x=>`<tr><td>${esc(x.e.name||'EPI')}</td><td>${fmtDate(x.last)}</td><td>${x.cycle} dias</td><td>${fmtDate(x.next)}</td></tr>`).join('');

    const paper=$('#workerSheetPaper');
    paper.innerHTML=`
      <div class="worker-sheet-title"><h1>FICHA INDIVIDUAL DE ENTREGA DE EPI</h1><p>Histórico eletrônico de fornecimento de Equipamentos de Proteção Individual</p></div>
      <div class="worker-sheet-company"><b>${esc(c.name||companyName(w.companyId,root))}</b>${c.cnpj?`<br>CNPJ: ${esc(c.cnpj)}`:''}</div>
      <div class="worker-sheet-grid">
        <div><small>Trabalhador</small><b>${esc(w.name||'—')}</b></div>
        <div><small>CPF</small><b>${esc(w.cpf||'—')}</b></div>
        <div><small>Matrícula</small><b>${esc(w.reg||'—')}</b></div>
        <div><small>Situação</small><b>${w.active===false?'Inativo':'Ativo'}</b></div>
        <div><small>Cargo</small><b>${esc(w.role||'—')}</b></div>
        <div><small>Setor</small><b>${esc(w.sector||'—')}</b></div>
        <div><small>Biometria cadastrada</small><b>${Array.isArray(w?.biometric?.embedding)&&w.biometric.embedding.length?'Sim':'Não'}</b></div>
        <div><small>Ficha atualizada</small><b>${fmtDate(new Date().toISOString(),true)}</b></div>
      </div>
      <div class="worker-sheet-metrics">
        <div class="worker-sheet-metric"><strong>${deliveries.length}</strong><span>entregas registradas</span></div>
        <div class="worker-sheet-metric"><strong>${totalUnits}</strong><span>unidades entregues</span></div>
        <div class="worker-sheet-metric"><strong>${uniqueEpis.size}</strong><span>tipos de EPI recebidos</span></div>
        <div class="worker-sheet-metric"><strong>${last?fmtDate(last):'—'}</strong><span>última entrega</span></div>
      </div>
      <div class="worker-sheet-section"><h2>Histórico de entregas</h2>${deliveries.length?`<table class="worker-sheet-table"><thead><tr><th>Data</th><th>EPI / CA / Quantidade</th><th>Motivo</th><th>Responsável</th><th>Confirmação</th></tr></thead><tbody>${rows}</tbody></table>`:'<div class="worker-sheet-empty">Este trabalhador ainda não possui entrega registrada.</div>'}</div>
      ${cycles.length?`<div class="worker-sheet-section"><h2>Controle de troca prevista</h2><table class="worker-sheet-table"><thead><tr><th>EPI</th><th>Última entrega</th><th>Ciclo cadastrado</th><th>Próxima troca prevista</th></tr></thead><tbody>${cycleRows}</tbody></table></div>`:''}
      ${proofs?`<div class="worker-sheet-section"><h2>Registros de confirmação</h2><div class="worker-sheet-signatures">${proofs}</div></div>`:''}
      <div class="worker-sheet-note">Esta ficha reúne os registros eletrônicos de entrega vinculados ao trabalhador. Cada entrega permanece identificada por data, EPI, quantidade, motivo e forma de confirmação disponível no sistema. Período registrado: <b>${first?fmtDate(first):'—'}</b> até <b>${last?fmtDate(last):'—'}</b>.</div>`;

    $$('.view').forEach(v=>v.classList.toggle('active',v.id==='workerSheetPc'));
    $$('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view==='workers'));
    if($('#viewTitle'))$('#viewTitle').textContent='Ficha individual de EPI';
    if($('#viewSub'))$('#viewSub').textContent=`Histórico completo de ${w.name||'trabalhador'}.`;
    $('.main')?.scrollTo({top:0,behavior:'smooth'});
  }

  function boot(){
    styles();ensureView();queueDecorate();
    const box=$('#workerTable');if(box)new MutationObserver(queueDecorate).observe(box,{childList:true,subtree:true});
    $('#workerSearch')?.addEventListener('input',queueDecorate);
    $('#globalCompany')?.addEventListener('change',queueDecorate);
    document.addEventListener('click',e=>{const b=e.target.closest('[data-worker-sheet]');if(b){e.preventDefault();renderSheet(b.dataset.workerSheet);}});
    const sync=$('#syncStatus');if(sync)new MutationObserver(()=>{if(/sincronizado/i.test(sync.textContent||''))setTimeout(queueDecorate,100);}).observe(sync,{childList:true,subtree:true,characterData:true});
    window.addEventListener('storage',e=>{if(e.key===CACHE){queueDecorate();if(currentWorkerId&&$('#workerSheetPc')?.classList.contains('active'))renderSheet(currentWorkerId);}});
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
