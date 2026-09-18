(function(){
  const q=(s,r=document)=>r.querySelector(s);
  const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const uid=p=>p+'_'+Date.now()+'_'+Math.random().toString(36).slice(2,9);
  const now=()=>new Date().toISOString();
  const endpoint=()=>String(window.SST_EPI_ENDPOINT||'');
  const key=()=>String(window.SST_EPI_SYNC_KEY||'');
  let analyzed=null;
  let fileData='';
  let dialog=null;

  function managementMode(){return !!q('#btnStockEntry');}

  function normalizeSnapshot(x){
    x=x&&typeof x==='object'?x:{};
    x.app=x.app&&typeof x.app==='object'?x.app:{};
    x.stock=x.stock&&typeof x.stock==='object'?x.stock:{};
    ['companies','workers','epis','deliveries','purchases','batches','auditLog'].forEach(k=>{
      x.app[k]=Array.isArray(x.app[k])?x.app[k]:[];
    });
    x.stock.movements=Array.isArray(x.stock.movements)?x.stock.movements:[];
    x.stock.minimums=x.stock.minimums&&typeof x.stock.minimums==='object'?x.stock.minimums:{};
    x.stock.processedDeliveryIds=Array.isArray(x.stock.processedDeliveryIds)?x.stock.processedDeliveryIds:[];
    x.version=Number(x.version||2);
    x.revision=Number(x.revision||0);
    return x;
  }

  function load(){
    if(managementMode()){
      let x={};
      try{x=JSON.parse(localStorage.getItem('sstGestaoEpiGestaoCacheV1')||'{}');}catch(_){}
      return normalizeSnapshot(x);
    }
    let app={},stock={};
    try{app=JSON.parse(localStorage.getItem('sstGestaoEpiV1')||'{}');}catch(_){}
    try{stock=JSON.parse(localStorage.getItem('sstGestaoEpiStockV1')||'{}');}catch(_){}
    return normalizeSnapshot({
      version:2,
      revision:Number(localStorage.getItem('sstGestaoEpiServerRevision')||0),
      app,
      stock
    });
  }

  function save(x){
    x=normalizeSnapshot(x);
    x.updatedAt=now();
    if(managementMode()){
      localStorage.setItem('sstGestaoEpiGestaoCacheV1',JSON.stringify(x));
    }else{
      localStorage.setItem('sstGestaoEpiV1',JSON.stringify(x.app));
      localStorage.setItem('sstGestaoEpiStockV1',JSON.stringify(x.stock));
      localStorage.setItem('sstGestaoEpiServerRevision',String(x.revision||0));
    }
  }

  async function api(action,extra){
    if(!endpoint()||!key())throw new Error('Central SST Gestão não configurada.');
    const body=Object.assign({action,syncKey:key()},extra||{});
    const res=await fetch(endpoint(),{
      method:'POST',
      headers:{'Content-Type':'text/plain;charset=utf-8'},
      body:JSON.stringify(body)
    });
    const json=await res.json();
    if(!json||json.ok!==true)throw new Error((json&&json.message)||'Falha na Central SST Gestão.');
    return json;
  }

  function ensureDialog(){
    if(dialog)return dialog;
    dialog=document.createElement('dialog');
    dialog.id='sstEpiNfDialog';
    dialog.innerHTML=
      '<form method="dialog" style="min-width:min(900px,92vw);max-width:92vw">'+
      '<div style="display:flex;justify-content:space-between;gap:12px;align-items:center">'+
      '<div><h2 style="margin:0">📄 Entrada por Nota Fiscal + IA</h2>'+
      '<p style="margin:5px 0;color:#64748b">A IA lê o DANFE, separa apenas EPIs e prepara a entrada de estoque.</p></div>'+
      '<button value="cancel" type="submit">×</button></div>'+
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0">'+
      '<label>Empresa<select id="sstNfCompany"></select></label>'+
      '<label>PDF da NF-e / DANFE<input id="sstNfFile" type="file" accept="application/pdf,.pdf"></label></div>'+
      '<div style="display:flex;gap:8px;flex-wrap:wrap">'+
      '<button id="sstNfAnalyze" type="button" class="primary">✨ Ler nota com IA</button>'+
      '<button id="sstNfConfirm" type="button" class="primary" disabled>✓ Confirmar entrada no estoque</button></div>'+
      '<div id="sstNfStatus" style="margin:12px 0;font-weight:700"></div>'+
      '<div id="sstNfPreview" style="max-height:45vh;overflow:auto"></div></form>';
    document.body.appendChild(dialog);

    q('#sstNfFile',dialog).addEventListener('change',async e=>{
      const f=e.target.files&&e.target.files[0];
      fileData=f?await new Promise((ok,no)=>{
        const r=new FileReader();
        r.onload=()=>ok(String(r.result||''));
        r.onerror=no;
        r.readAsDataURL(f);
      }):'';
    });
    q('#sstNfAnalyze',dialog).addEventListener('click',analyze);
    q('#sstNfConfirm',dialog).addEventListener('click',confirmEntry);
    return dialog;
  }

  function open(){
    const d=ensureDialog();
    const snap=load();
    const sel=q('#sstNfCompany',d);
    sel.innerHTML='<option value="">Selecione a empresa</option>'+
      snap.app.companies.map(c=>'<option value="'+esc(c.id)+'">'+esc(c.name)+'</option>').join('');
    analyzed=null;
    fileData='';
    q('#sstNfPreview',d).innerHTML='';
    q('#sstNfStatus',d).textContent='';
    q('#sstNfConfirm',d).disabled=true;
    q('#sstNfFile',d).value='';
    d.showModal();
  }

  async function analyze(){
    const d=ensureDialog();
    const companyId=q('#sstNfCompany',d).value;
    if(!companyId){q('#sstNfStatus',d).textContent='Selecione a empresa.';return;}
    if(!fileData){q('#sstNfStatus',d).textContent='Selecione o PDF da nota fiscal.';return;}
    const btn=q('#sstNfAnalyze',d);
    btn.disabled=true;
    q('#sstNfStatus',d).textContent='Lendo a nota fiscal com IA…';

    try{
      const result=await api('epi_ai_assistant',{payload:{mode:'invoice_pdf_import',document:fileData}});
      analyzed=result.result&&result.result.invoice?result.result.invoice:null;
      const items=Array.isArray(analyzed&&analyzed.items)?analyzed.items:[];
      if(!items.length)throw new Error('A IA não encontrou itens de EPI nesta nota.');

      try{
        const ca=await api('epi_ai_assistant',{payload:{mode:'ca_validate',items}});
        const checks=ca.result&&Array.isArray(ca.result.checks)?ca.result.checks:[];
        items.forEach(i=>{
          i.caCheck=checks.find(x=>String(x.ca)===String(i.ca))||null;
        });
      }catch(_){}

      let rows='';
      items.forEach(i=>{
        rows+='<tr>'+
          '<td style="padding:7px;border-top:1px solid #ddd">'+esc(i.name)+'</td>'+
          '<td style="padding:7px;border-top:1px solid #ddd">'+esc(i.ca||'—')+(i.caCheck&&i.caCheck.found?' ✓':'')+'</td>'+
          '<td style="padding:7px;border-top:1px solid #ddd">'+Number(i.qty||0)+'</td>'+
          '<td style="padding:7px;border-top:1px solid #ddd">'+esc(i.lot||'—')+'</td>'+
          '<td style="padding:7px;border-top:1px solid #ddd">'+esc(i.physicalExpiry||'—')+'</td>'+
          '</tr>';
      });
      q('#sstNfPreview',d).innerHTML=
        '<div style="margin:8px 0"><b>NF '+esc(analyzed.number||'—')+'</b> • '+esc(analyzed.supplier||'Fornecedor não identificado')+'</div>'+
        '<table style="width:100%;border-collapse:collapse"><thead><tr><th>EPI</th><th>CA</th><th>Qtd.</th><th>Lote</th><th>Validade</th></tr></thead><tbody>'+rows+'</tbody></table>';
      q('#sstNfStatus',d).textContent=items.length+' item(ns) de EPI identificado(s). Confira antes de confirmar.';
      q('#sstNfConfirm',d).disabled=false;
    }catch(e){
      q('#sstNfStatus',d).textContent=String((e&&e.message)||e);
    }finally{
      btn.disabled=false;
    }
  }

  async function confirmEntry(){
    const d=ensureDialog();
    const companyId=q('#sstNfCompany',d).value;
    if(!analyzed||!companyId)return;

    const snap=load();
    const company=snap.app.companies.find(c=>String(c.id)===companyId);
    const purchaseId=uid('purchase');
    const createdAt=now();
    const purchaseItems=[];

    (analyzed.items||[]).forEach(raw=>{
      let epi=snap.app.epis.find(e=>
        String(e.ca||'')===String(raw.ca||'') &&
        String(e.name||'').toLowerCase()===String(raw.name||'').toLowerCase() &&
        String(e.size||'')===String(raw.size||'')
      );
      if(!epi){
        epi={
          id:uid('epi'),
          name:String(raw.name||''),
          ca:String(raw.ca||''),
          model:String(raw.manufacturer||''),
          size:String(raw.size||''),
          cycle:0,
          createdAt,
          updatedAt:createdAt
        };
        snap.app.epis.push(epi);
      }

      const qty=Math.max(0,Number(raw.qty||0));
      if(!qty)return;
      const batchId=uid('batch');

      snap.app.batches.push({
        id:batchId,
        purchaseId,
        companyId,
        epiId:epi.id,
        lot:String(raw.lot||''),
        physicalExpiry:String(raw.physicalExpiry||''),
        invoiceNumber:String(analyzed.number||''),
        qty,
        remainingQty:qty,
        createdAt,
        updatedAt:createdAt
      });

      snap.stock.movements.push({
        id:uid('stock_in'),
        type:'IN',
        delta:qty,
        companyId,
        epiId:epi.id,
        batchId,
        purchaseId,
        lot:String(raw.lot||''),
        physicalExpiry:String(raw.physicalExpiry||''),
        invoiceNumber:String(analyzed.number||''),
        note:'Entrada por NF '+String(analyzed.number||''),
        createdAt,
        updatedAt:createdAt
      });

      const minKey=companyId+'::'+epi.id;
      if(snap.stock.minimums[minKey]==null)snap.stock.minimums[minKey]=5;

      purchaseItems.push({
        epiId:epi.id,
        batchId,
        code:String(raw.code||''),
        name:epi.name,
        ca:epi.ca,
        size:epi.size,
        qty,
        unit:String(raw.unit||''),
        unitValue:Number(raw.unitValue||0),
        total:Number(raw.total||0),
        lot:String(raw.lot||''),
        physicalExpiry:String(raw.physicalExpiry||'')
      });
    });

    snap.app.purchases.push({
      id:purchaseId,
      companyId,
      invoiceNumber:String(analyzed.number||''),
      series:String(analyzed.series||''),
      invoiceKey:String(analyzed.key||''),
      date:String(analyzed.date||''),
      supplier:String(analyzed.supplier||''),
      supplierCnpj:String(analyzed.supplierCnpj||''),
      items:purchaseItems,
      createdAt,
      updatedAt:createdAt
    });

    snap.app.auditLog.push({
      id:uid('audit'),
      type:'NF_IMPORT',
      companyId,
      purchaseId,
      invoiceNumber:String(analyzed.number||''),
      user:(window.SST_EPI_BOOTSTRAP&&window.SST_EPI_BOOTSTRAP.user&&window.SST_EPI_BOOTSTRAP.user.name)||'',
      createdAt
    });

    save(snap);
    q('#sstNfStatus',d).textContent='Salvando e sincronizando…';

    try{
      if(fileData){
        await api('epi_store_purchase_document',{
          document:fileData,
          meta:{companyName:(company&&company.name)||'',invoiceNumber:analyzed.number||''}
        });
      }
      const sync=await api('epi_sync_merge',{
        deviceId:window.GestaoEpiAuth&&window.GestaoEpiAuth.deviceId?window.GestaoEpiAuth.deviceId():'',
        client:'sst-gestao-nf',
        payload:snap
      });
      if(sync.payload)save(sync.payload);
      document.dispatchEvent(new CustomEvent('sstGestao-epi-data-changed'));
      q('#sstNfStatus',d).textContent='✓ Entrada registrada e sincronizada.';
      setTimeout(()=>location.reload(),700);
    }catch(e){
      q('#sstNfStatus',d).textContent='Entrada salva localmente. Sincronização pendente: '+String((e&&e.message)||e);
    }
  }

  function inject(){
    if(q('#sstEpiNfButton'))return;
    const btn=document.createElement('button');
    btn.id='sstEpiNfButton';
    btn.type='button';
    btn.className='secondary';
    btn.textContent='📄 Entrada por NF/IA';
    btn.addEventListener('click',open);

    if(managementMode()){
      const target=q('#btnStockEntry');
      if(target)target.insertAdjacentElement('afterend',btn);
    }else{
      const target=q('#stock .view-head')||q('#stock .section-title');
      if(target)target.appendChild(btn);
    }
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',inject);
  else inject();
})();