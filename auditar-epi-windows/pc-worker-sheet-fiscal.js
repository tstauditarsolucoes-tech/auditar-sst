(() => {
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  let scheduled=false;

  function esc(v=''){
    return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function fmtNow(){
    try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date());}
    catch(_){return new Date().toLocaleString('pt-BR');}
  }

  function ensureStyles(){
    if($('#workerFiscalStyles'))return;
    const s=document.createElement('style');
    s.id='workerFiscalStyles';
    s.textContent=`
      .worker-fiscal-legal{display:grid;grid-template-columns:1.3fr .7fr;gap:10px;margin:0 0 16px}
      .worker-fiscal-box{border:1px solid #cfe1dd;border-radius:11px;padding:11px 12px;background:#f7fbfa;color:#365a55;font-size:10px;line-height:1.45}
      .worker-fiscal-box b{color:#173d39}.worker-fiscal-box strong{display:block;color:#0f766e;font-size:12px;margin-bottom:3px}
      .worker-fiscal-free{display:flex;align-items:center;justify-content:center;text-align:center;background:#ecfdf3;border-color:#bce8cb;color:#166534;font-weight:900;font-size:12px}
      .worker-fiscal-free span{display:block;font-size:22px;line-height:1;margin-bottom:4px}
      .worker-fiscal-section{margin-top:18px;border:1px solid #d6e4e1;border-radius:12px;padding:13px 14px;break-inside:avoid}
      .worker-fiscal-section h2{font-size:13px;color:#173d39;margin:0 0 8px}.worker-fiscal-section p{font-size:10px;line-height:1.5;color:#49635f;margin:5px 0}
      .worker-fiscal-list{display:grid;grid-template-columns:1fr 1fr;gap:5px 18px;margin:8px 0 0;padding:0;list-style:none}.worker-fiscal-list li{position:relative;padding-left:14px;font-size:9.5px;line-height:1.4;color:#4b6560}.worker-fiscal-list li::before{content:'✓';position:absolute;left:0;color:#0f766e;font-weight:900}
      .worker-fiscal-emission{margin-top:14px;padding-top:10px;border-top:1px solid #dce7e5;display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;color:#637974;font-size:9px}
      .worker-fiscal-tag{display:inline-block;background:#eef8f6;color:#0f766e;border:1px solid #cde2de;border-radius:7px;padding:4px 6px;font-size:8.5px;font-weight:900;white-space:nowrap}
      @media(max-width:860px){.worker-fiscal-legal{grid-template-columns:1fr}.worker-fiscal-list{grid-template-columns:1fr}}
      @media print{.worker-fiscal-legal,.worker-fiscal-section{break-inside:avoid}.worker-fiscal-list{grid-template-columns:1fr 1fr}.worker-fiscal-box,.worker-fiscal-section{background:#fff!important}}
    `;
    document.head.appendChild(s);
  }

  function historyTable(paper){
    const sections=$$('.worker-sheet-section',paper);
    for(const sec of sections){
      const h=sec.querySelector('h2');
      if(/hist[oó]rico de entregas/i.test(h?.textContent||''))return sec.querySelector('table');
    }
    return null;
  }

  function addFreeColumn(table){
    if(!table||table.querySelector('[data-fiscal-free-head]'))return;
    const head=table.querySelector('thead tr');
    if(head){
      const th=document.createElement('th');
      th.dataset.fiscalFreeHead='1';
      th.textContent='Fornecimento';
      const cells=[...head.children];
      const confirm=cells.find(x=>/confirma/i.test(x.textContent||''));
      confirm?head.insertBefore(th,confirm):head.appendChild(th);
    }
    table.querySelectorAll('tbody tr').forEach(tr=>{
      if(tr.querySelector('[data-fiscal-free-cell]'))return;
      const td=document.createElement('td');
      td.dataset.fiscalFreeCell='1';
      td.innerHTML='<span class="worker-fiscal-tag">GRATUITO</span>';
      const cells=[...tr.children];
      const confirm=cells[cells.length-1];
      confirm?tr.insertBefore(td,confirm):tr.appendChild(td);
    });
  }

  function enhance(){
    scheduled=false;
    const paper=$('#workerSheetPaper');
    if(!paper||!paper.children.length||paper.querySelector('.worker-fiscal-legal'))return;
    ensureStyles();

    const company=$('.worker-sheet-company',paper);
    const legal=document.createElement('div');
    legal.className='worker-fiscal-legal';
    legal.innerHTML=`
      <div class="worker-fiscal-box">
        <strong>Registro eletrônico de fornecimento de EPI</strong>
        Documento extraído do sistema eletrônico de controle de EPI, conforme a NR-6, item 6.5.1, alínea “d”. O sistema permite a extração deste relatório, conforme item 6.5.1.1.
      </div>
      <div class="worker-fiscal-box worker-fiscal-free"><div><span>✓</span>FORNECIMENTO GRATUITO<br><small>NR-6, item 6.5.1, “c”</small></div></div>`;
    company?.insertAdjacentElement('afterend',legal);

    addFreeColumn(historyTable(paper));

    const note=$('.worker-sheet-note',paper);
    const responsibilities=document.createElement('section');
    responsibilities.className='worker-fiscal-section';
    responsibilities.innerHTML=`
      <h2>Ciência e responsabilidades relacionadas ao uso do EPI</h2>
      <p>As confirmações por assinatura ou biometria apresentadas nesta ficha permanecem vinculadas aos respectivos registros de entrega. Quanto ao EPI recebido, aplicam-se ao trabalhador as responsabilidades previstas no item 6.6.1 da NR-6:</p>
      <ul class="worker-fiscal-list">
        <li>usar o EPI fornecido pela organização;</li>
        <li>utilizá-lo apenas para a finalidade a que se destina;</li>
        <li>responsabilizar-se pela limpeza, guarda e conservação;</li>
        <li>comunicar extravio, dano ou alteração que torne o EPI impróprio para uso;</li>
        <li>cumprir as determinações da organização sobre o uso adequado.</li>
      </ul>
    `;

    const information=document.createElement('section');
    information.className='worker-fiscal-section';
    information.innerHTML=`
      <h2>Informações no fornecimento</h2>
      <p>A organização deve assegurar as informações previstas na NR-6, item 6.7.2, incluindo descrição do equipamento, risco contra o qual protege, restrições e limitações, forma adequada de uso e ajuste, manutenção/substituição e cuidados de limpeza, higienização, guarda e conservação. Quando as características do EPI exigirem, deve ser realizado o treinamento aplicável.</p>
      <p><b>Observação:</b> esta ficha comprova os registros de fornecimento existentes no sistema e não substitui os demais registros de capacitação, seleção de EPI ou documentos de SST aplicáveis.</p>
    `;

    const user=window.GestaoEpiAuth?.user?.()||{};
    const emission=document.createElement('div');
    emission.className='worker-fiscal-emission';
    emission.innerHTML=`<span>Relatório extraído em <b>${esc(fmtNow())}</b></span><span>Usuário responsável pela extração: <b>${esc(user.name||user.username||user.user||'usuário autenticado')}</b></span><span>Confirmações aceitas pelo sistema: <b>assinatura eletrônica ou biometria facial</b></span>`;

    if(note){
      note.insertAdjacentElement('beforebegin',responsibilities);
      responsibilities.insertAdjacentElement('afterend',information);
      note.insertAdjacentElement('afterend',emission);
    }else{
      paper.appendChild(responsibilities);paper.appendChild(information);paper.appendChild(emission);
    }
  }

  function schedule(){if(scheduled)return;scheduled=true;setTimeout(enhance,0);}

  function boot(){
    ensureStyles();schedule();
    const paper=$('#workerSheetPaper');
    if(paper)new MutationObserver(schedule).observe(paper,{childList:true,subtree:false});
    document.addEventListener('click',e=>{if(e.target.closest('[data-worker-sheet]'))setTimeout(schedule,20);});
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();