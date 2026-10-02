(()=>{
  const CACHE='auditarEpiGestaoCacheV1';
  const RESUME='pc280ResumeView';
  const FLASH='pc280Flash';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const digits=(v='')=>String(v??'').replace(/\D/g,'');
  const now=()=>new Date().toISOString();
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,9)}`;
  let invoiceState=null;
  let invoiceDocument='';
  let invoiceFile=null;
  let caResults={};

  function read(){
    try{
      const r=JSON.parse(localStorage.getItem(CACHE)||'{}');
      r.app=r.app&&typeof r.app==='object'?r.app:{};
      for(const k of ['companies','workers','epis','deliveries'])r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];
      r.stock=r.stock&&typeof r.stock==='object'?r.stock:{};
      r.stock.movements=Array.isArray(r.stock.movements)?r.stock.movements:[];
      r.stock.minimums=r.stock.minimums&&typeof r.stock.minimums==='object'?r.stock.minimums:{};
      r.stock.processedDeliveryIds=Array.isArray(r.stock.processedDeliveryIds)?r.stock.processedDeliveryIds:[];
      return r;
    }catch(_){
      return {version:1,revision:0,updatedAt:'',app:{companies:[],workers:[],epis:[],deliveries:[]},stock:{startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}}};
    }
  }

  function write(r){
    r.updatedAt=now();
    localStorage.setItem(CACHE,JSON.stringify(r));
  }

  function toast(msg){
    const el=$('#toast');
    if(!el)return alert(msg);
    el.textContent=msg;
    el.classList.add('show');
    setTimeout(()=>el.classList.remove('show'),3000);
  }

  function api(action,extra={}){
    if(!window.GestaoEpiAuth?.api)throw new Error('Faça o login antes de usar esta função.');
    return window.GestaoEpiAuth.api(action,extra);
  }

  function role(){
    return String(window.GestaoEpiAuth?.user?.()?.role||document.body.dataset.epiRole||'');
  }

  function canOperate(){
    return ['admin','campo'].includes(role());
  }

  function saveAndReload(r,message,view){
    write(r);
    sessionStorage.setItem(RESUME,view||'dashboard');
    sessionStorage.setItem(FLASH,message||'Dados atualizados.');
    setTimeout(()=>location.reload(),80);
  }

  function fileToDataUrl(file){
    return new Promise((resolve,reject)=>{
      const reader=new FileReader();
      reader.onload=()=>resolve(String(reader.result||''));
      reader.onerror=()=>reject(new Error('Não foi possível ler o arquivo.'));
      reader.readAsDataURL(file);
    });
  }

  function css(){
    if($('#pc280ParityCss'))return;
    const s=document.createElement('style');
    s.id='pc280ParityCss';
    s.textContent=`
      .pc280-parity-view{display:none}.pc280-parity-view.active{display:block}
      .pc280-parity-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:14px}
      .pc280-parity-head h2{margin:0;color:#173d39;font-size:19px}.pc280-parity-head p{margin:4px 0 0;color:#6c827e;font-size:11px}
      .pc280-parity-card{background:#fff;border:1px solid #dbe8e5;border-radius:14px;padding:14px;margin-bottom:12px;box-shadow:0 4px 16px rgba(22,61,56,.04)}
      .pc280-nf-grid{display:grid;grid-template-columns:minmax(220px,.8fr) minmax(280px,1.2fr) auto;gap:10px;align-items:end}
      .pc280-nf-grid label{display:grid;gap:5px;color:#4e6863;font-size:10px;font-weight:850}.pc280-nf-grid input,.pc280-nf-grid select{width:100%;min-height:39px}
      .pc280-nf-status{padding:10px 12px;border-radius:10px;background:#f4f8f7;color:#5e7671;font-size:10px;margin-top:10px}
      .pc280-nf-status.busy{background:#fff8e6;color:#855f13}.pc280-nf-status.ok{background:#ecfdf3;color:#166534}.pc280-nf-status.fail{background:#fff0ee;color:#b42318}
      .pc280-nf-meta{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin-bottom:11px}
      .pc280-nf-meta>div{border:1px solid #e0e9e7;background:#f9fbfb;border-radius:10px;padding:9px;min-width:0}
      .pc280-nf-meta small{display:block;color:#768984;font-size:8px;text-transform:uppercase;font-weight:900}.pc280-nf-meta b{display:block;color:#183d39;font-size:10.5px;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .pc280-nf-table-wrap{max-height:calc(100vh - 365px);overflow:auto;border:1px solid #e1eae8;border-radius:10px}
      .pc280-nf-table{width:100%;border-collapse:separate;border-spacing:0;font-size:10px}.pc280-nf-table th{position:sticky;top:0;z-index:2;background:#f2f6f5;color:#617672;font-size:8px;text-transform:uppercase;padding:8px;border-bottom:1px solid #dce7e5;text-align:left}.pc280-nf-table td{padding:8px;border-bottom:1px solid #edf2f1;vertical-align:middle}.pc280-nf-table tr:last-child td{border-bottom:0}
      .pc280-nf-table input[type=checkbox]{width:16px;height:16px}.pc280-nf-table input[type=number]{width:76px;min-height:32px;padding:5px 7px}
      .pc280-chip{display:inline-flex;border-radius:999px;padding:4px 7px;font-size:8px;font-weight:900}.pc280-chip.epi{background:#ecfdf3;color:#166534}.pc280-chip.review{background:#fff8e6;color:#8a6418}.pc280-chip.bad{background:#fff0ee;color:#b42318}
      .pc280-nf-actions{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:10px;flex-wrap:wrap}.pc280-nf-actions small{color:#70847f;font-size:9px}
      .pc280-ca-official{display:grid;gap:3px;margin-top:5px;padding:7px 8px;border-radius:8px;background:#f4f9f8;border:1px solid #e0ebe9;min-width:190px}.pc280-ca-official b{font-size:9px;color:#24514c}.pc280-ca-official small{font-size:8px;color:#6b817d;line-height:1.3}
      .pc280-ca-toolbar{display:flex;align-items:center;gap:7px;flex-wrap:wrap}.pc280-ca-live{font-size:9px;color:#667e79}
      @media(min-width:1000px){
        #newDeliveryPc{display:none}
        #newDeliveryPc.active{display:grid!important;grid-template-columns:minmax(0,1.15fr) minmax(360px,.85fr)!important;grid-template-areas:"head head" "form items" "form confirm" "save save"!important;gap:12px!important;align-items:start!important}
        #newDeliveryPc>.pc-modern-head{grid-area:head!important;margin:0!important}
        #newDeliveryPc>.pc-card.pc-grid{grid-area:form!important;margin:0!important;grid-template-columns:1fr 1fr!important;position:sticky!important;top:100px!important}
        #newDeliveryPc>.pc-card:nth-of-type(2){grid-area:items!important;margin:0!important}
        #newDeliveryPc>#pcConfirmCard,#newDeliveryPc>.pc-card:nth-of-type(3){grid-area:confirm!important;margin:0!important}
        #newDeliveryPc>#pcSaveDelivery{grid-area:save!important;width:auto!important;justify-self:stretch!important;margin:0!important}
        #newDeliveryPc .pc-signature{height:135px!important}
        #newDeliveryPc .pc-delivery-item{grid-template-columns:minmax(0,1fr) 72px 38px!important}
      }
      @media(max-width:1100px){.pc280-nf-meta{grid-template-columns:repeat(2,minmax(0,1fr))}.pc280-nf-grid{grid-template-columns:1fr 1fr}.pc280-nf-grid>button{grid-column:1/-1}}
    `;
    document.head.appendChild(s);
  }

  function addNav(){
    const nav=$('.sidebar nav');
    if(!nav||nav.querySelector('[data-view="nfImportPc"]'))return false;
    const b=document.createElement('button');
    b.className='nav pc-new';
    b.dataset.view='nfImportPc';
    b.innerHTML='🧾 <span>Nota Fiscal por IA</span>';
    const ref=nav.querySelector('[data-view="purchasesPc"]')||nav.querySelector('[data-view="stock"]');
    ref?.insertAdjacentElement('afterend',b);
    b.addEventListener('click',()=>openNf());
    return true;
  }

  function ensureNfView(){
    const main=$('.main');
    if(!main||$('#nfImportPc'))return Boolean($('#nfImportPc'));
    const s=document.createElement('section');
    s.id='nfImportPc';
    s.className='view pc280-parity-view';
    s.innerHTML=`
      <div class="pc280-parity-head">
        <div><h2>🧾 Nota Fiscal por IA</h2><p>Leia PDF/DANFE ou XML, confira os EPIs identificados e registre a entrada no estoque.</p></div>
      </div>
      <div class="pc280-parity-card">
        <div class="pc280-nf-grid">
          <label>Empresa<select id="pc280NfCompany"></select></label>
          <label>Nota Fiscal<input id="pc280NfFile" type="file" accept=".pdf,.xml,application/pdf,application/xml,text/xml"></label>
          <button id="pc280NfAnalyze" type="button" class="primary">Analisar documento</button>
        </div>
        <div id="pc280NfStatus" class="pc280-nf-status">Selecione a empresa e um PDF/XML da NF-e.</div>
      </div>
      <div id="pc280NfResult" class="pc280-parity-card" style="display:none">
        <div id="pc280NfMeta" class="pc280-nf-meta"></div>
        <div class="pc280-nf-table-wrap"><table class="pc280-nf-table"><thead><tr><th></th><th>Produto</th><th>CA</th><th>Qtd.</th><th>Lote / validade física</th><th>Classificação</th><th>Conferência CA</th></tr></thead><tbody id="pc280NfBody"></tbody></table></div>
        <div class="pc280-nf-actions"><small id="pc280NfHint"></small><button id="pc280NfCommit" type="button" class="primary">＋ Registrar entrada no estoque</button></div>
      </div>`;
    main.appendChild(s);
    $('#pc280NfAnalyze').addEventListener('click',analyzeInvoice);
    $('#pc280NfCommit').addEventListener('click',commitInvoice);
    return true;
  }

  function fillCompanies(){
    const sel=$('#pc280NfCompany');
    if(!sel)return;
    const old=sel.value;
    const rows=read().app.companies.filter(c=>c.active!==false).sort((a,b)=>String(a.name||'').localeCompare(String(b.name||'')));
    sel.innerHTML='<option value="">Selecione a empresa</option>'+rows.map(c=>`<option value="${esc(c.id)}">${esc(c.name||'Empresa')}</option>`).join('');
    if(rows.some(c=>c.id===old))sel.value=old;
  }

  function openNf(){
    $$('.view').forEach(v=>v.classList.toggle('active',v.id==='nfImportPc'));
    $$('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view==='nfImportPc'));
    if($('#viewTitle'))$('#viewTitle').textContent='Nota Fiscal por IA';
    if($('#viewSub'))$('#viewSub').textContent='Entrada de EPI por PDF/DANFE ou XML, com conferência antes de registrar.';
    fillCompanies();
    $('.main')?.scrollTo({top:0,behavior:'smooth'});
  }

  function setNfStatus(text,kind=''){
    const e=$('#pc280NfStatus');if(!e)return;
    e.className='pc280-nf-status '+kind;
    e.textContent=text;
  }

  async function analyzeInvoice(){
    if(!canOperate())return toast('Seu perfil é somente consulta.');
    const companyId=$('#pc280NfCompany')?.value||'';
    const file=$('#pc280NfFile')?.files?.[0];
    if(!companyId)return toast('Selecione a empresa.');
    if(!file)return toast('Selecione o PDF ou XML da Nota Fiscal.');
    if(file.size>13000000)return toast('Arquivo muito grande. Use um documento de até aproximadamente 13 MB.');
    const ext=(file.name.split('.').pop()||'').toLowerCase();
    if(!['pdf','xml'].includes(ext))return toast('Use PDF/DANFE ou XML da NF-e.');

    invoiceState=null;invoiceDocument='';invoiceFile=file;caResults={};
    $('#pc280NfResult').style.display='none';
    setNfStatus(ext==='xml'?'Lendo XML e classificando itens…':'Lendo a Nota Fiscal com IA…','busy');
    const btn=$('#pc280NfAnalyze');btn.disabled=true;
    try{
      let document=await fileToDataUrl(file);
      const rawBase64=document.includes(',')?document.slice(document.indexOf(',')+1):'';
      if(ext==='pdf'&&!/^data:application\/pdf;base64,/i.test(document))document='data:application/pdf;base64,'+rawBase64;
      if(ext==='xml'&&!/^data:(?:application|text)\/xml(?:;charset=[^;,]+)?;base64,/i.test(document))document='data:application/xml;base64,'+rawBase64;
      const res=await api('tenant_ai_assistant',{payload:{mode:'invoice_document_import',document}});
      if(!res?.ok)throw new Error(res?.message||'Não foi possível ler a Nota Fiscal.');
      const invoice=res?.result?.invoice;
      if(!invoice||!Array.isArray(invoice.items))throw new Error('A Central não retornou os itens da Nota Fiscal.');
      invoiceState={invoice,provider:String(res.provider||''),cached:res.cached===true,documentHash:String(res.documentHash||''),companyId};
      invoiceDocument=document;
      await enrichInvoiceCas(invoice);
      renderInvoice();
      const ignored=Number(invoice.ignoredItemsCount||0);
      setNfStatus(`Documento lido: ${invoice.items.length} item(ns) para conferência${ignored?' • '+ignored+' não-EPI ignorado(s)':''}.`,'ok');
    }catch(err){
      setNfStatus(err?.message||'Falha ao analisar a Nota Fiscal.','fail');
      toast(err?.message||'Falha ao analisar a Nota Fiscal.');
    }finally{btn.disabled=false}
  }

  async function enrichInvoiceCas(invoice){
    const all=(invoice.items||[]).filter(i=>digits(i.ca)).map(i=>({ca:digits(i.ca),name:String(i.name||''),manufacturer:String(i.manufacturer||'')}));
    const unique=[...new Map(all.map(i=>[i.ca,i])).values()];
    if(!unique.length)return;
    for(let start=0;start<unique.length;start+=20){
      const items=unique.slice(start,start+20);
      try{
        const res=await api('tenant_ai_assistant',{payload:{mode:'ca_validate',items}});
        if(!res?.ok)continue;
        for(const check of (res?.result?.checks||[]))caResults[digits(check.ca)]=check;
      }catch(_){}
    }
  }

  function caHtml(ca){
    const n=digits(ca),c=caResults[n];
    if(!n)return '<span class="muted">Sem CA na nota</span>';
    if(!c)return '<span class="muted">Não consultado</span>';
    const ok=c.found===true;
    return `<div class="pc280-ca-official"><b>${ok?'✓ ':''}CA ${esc(n)} • ${esc(c.status||'não confirmado')}</b><small>${c.validity?'Validade CA: '+esc(c.validity):'Validade não localizada'}${c.manufacturer?' • '+esc(c.manufacturer):''}</small></div>`;
  }

  function renderInvoice(){
    const wrap=$('#pc280NfResult'),meta=$('#pc280NfMeta'),body=$('#pc280NfBody'),hint=$('#pc280NfHint');
    if(!wrap||!invoiceState)return;
    const inv=invoiceState.invoice;
    meta.innerHTML=`
      <div><small>NF</small><b>${esc(inv.number||'—')}</b></div>
      <div><small>Fornecedor</small><b title="${esc(inv.supplier||'')}">${esc(inv.supplier||'—')}</b></div>
      <div><small>Data</small><b>${esc(inv.date||'—')}</b></div>
      <div><small>Itens EPI/revisão</small><b>${(inv.items||[]).length}</b></div>
      <div><small>Origem</small><b>${esc(invoiceState.provider||'Central')}</b></div>`;
    body.innerHTML=(inv.items||[]).map((item,index)=>{
      const classification=String(item.classification||'review');
      const checked=classification==='epi'?'checked':'';
      const disabled=(!item.name||Number(item.qty||0)<=0)?'disabled':'';
      const cls=classification==='epi'?'epi':classification==='review'?'review':'bad';
      const label=classification==='epi'?'EPI':classification==='review'?'REVISAR':'NÃO EPI';
      const issues=(item.validation?.issues||[]).join(' • ');
      return `<tr data-nf-index="${index}">
        <td><input class="pc280-nf-select" type="checkbox" ${checked} ${disabled}></td>
        <td><b>${esc(item.name||'—')}</b><br><small>${esc([item.code,item.manufacturer,item.size].filter(Boolean).join(' • ')||'')}</small>${issues?`<br><small style="color:#9a6510">${esc(issues)}</small>`:''}</td>
        <td>${esc(item.ca||'—')}</td>
        <td><input class="pc280-nf-qty" type="number" min="0" step="1" value="${Math.max(0,Number(item.qty||0))}"></td>
        <td>${esc(item.lot||'—')}${item.physicalExpiry?`<br><small>Val. física: ${esc(item.physicalExpiry)}</small>`:''}</td>
        <td><span class="pc280-chip ${cls}">${label}</span></td>
        <td>${caHtml(item.ca)}</td>
      </tr>`;
    }).join('');
    const review=(inv.items||[]).filter(i=>String(i.classification||'')==='review').length;
    hint.textContent=review?`${review} item(ns) precisam de conferência manual antes do lançamento.`:'Confira quantidades e itens antes de registrar.';
    wrap.style.display='';
  }

  function epiMatch(root,item){
    const ca=digits(item.ca);
    if(ca){
      const found=root.app.epis.find(e=>digits(e.ca)===ca&&e.active!==false);
      if(found)return found;
    }
    const n=norm(item.name),size=norm(item.size);
    return root.app.epis.find(e=>e.active!==false&&norm(e.name)===n&&(!size||norm(e.size)===size))||null;
  }

  function safePart(v=''){
    return String(v||'').replace(/[^A-Za-z0-9_-]+/g,'').slice(0,45)||'x';
  }

  async function commitInvoice(){
    if(!canOperate())return toast('Seu perfil é somente consulta.');
    if(!invoiceState||!invoiceDocument)return toast('Analise a Nota Fiscal primeiro.');
    const companyId=$('#pc280NfCompany')?.value||invoiceState.companyId||'';
    if(!companyId)return toast('Selecione a empresa.');
    const rows=$$('#pc280NfBody tr');
    const selected=rows.map(tr=>{
      const check=tr.querySelector('.pc280-nf-select');
      if(!check?.checked)return null;
      const index=Number(tr.dataset.nfIndex);
      const item={...(invoiceState.invoice.items[index]||{})};
      item.qty=Math.max(0,Number(tr.querySelector('.pc280-nf-qty')?.value||0));
      return {index,item};
    }).filter(x=>x&&x.item.name&&x.item.qty>0);
    if(!selected.length)return toast('Selecione pelo menos um EPI com quantidade maior que zero.');

    const inv=invoiceState.invoice;
    const sourceKey=digits(inv.key)||safePart(inv.number||invoiceState.documentHash||Date.now());
    const purchaseId='p_nf_'+safePart(companyId)+'_'+safePart(sourceKey);
    const btn=$('#pc280NfCommit');btn.disabled=true;btn.textContent='Registrando…';
    try{
      const stored=await api('tenant_store_purchase_document',{payload:{
        purchaseId,companyId,invoiceKey:digits(inv.key),invoiceNumber:String(inv.number||''),fileName:String(invoiceFile?.name||'nota-fiscal'),document:invoiceDocument
      }});
      if(!stored?.ok)throw new Error(stored?.message||'Não foi possível armazenar o documento original da NF.');

      const root=read();
      let added=0,duplicates=0,newEpis=0;
      selected.forEach(({index,item})=>{
        let e=epiMatch(root,item);
        const ca=digits(item.ca);
        const c=caResults[ca]||null;
        if(!e){
          e={
            id:uid('e'),name:String(item.name||'EPI').trim(),ca:ca,model:String(item.manufacturer||'').trim(),size:String(item.size||'').trim(),
            active:true,createdAt:now(),updatedAt:now()
          };
          root.app.epis.push(e);newEpis++;
        }else{
          if(!e.ca&&ca)e.ca=ca;
          if(!e.model&&item.manufacturer)e.model=String(item.manufacturer);
          if(!e.size&&item.size)e.size=String(item.size);
          e.updatedAt=now();
        }
        if(c?.found){
          e.caCheckedAt=now();
          e.caCheckedBy=String(window.GestaoEpiAuth?.user?.()?.name||window.GestaoEpiAuth?.user?.()?.username||'');
          e.caValidationStatus=String(c.status||'');
          e.caValidity=String(c.validity||'');
          e.caEquipment=String(c.equipment||'');
          e.caManufacturer=String(c.manufacturer||'');
          e.caSourceUrl=String(c.sourceUrl||'');
          e.caSourceType=String(c.sourceType||'');
        }

        const productKey=safePart(item.code||e.id||index);
        const movementId='sm_nf_'+safePart(companyId)+'_'+safePart(sourceKey)+'_'+productKey+'_'+index;
        if(root.stock.movements.some(m=>String(m.id)===movementId)){duplicates++;return}
        const batchId='b_nf_'+safePart(sourceKey)+'_'+productKey+'_'+index;
        root.stock.movements.unshift({
          id:movementId,type:'IN',delta:Number(item.qty||0),companyId,epiId:e.id,
          purchaseId,batchId,lot:String(item.lot||''),physicalExpiry:String(item.physicalExpiry||''),
          invoiceNumber:String(inv.number||''),invoiceKey:digits(inv.key),supplier:String(inv.supplier||''),
          supplierCnpj:digits(inv.supplierCnpj),productCode:String(item.code||''),unit:String(item.unit||''),
          unitValue:Number(item.unitValue||0),total:Number(item.total||0),source:'pc-nf-ai-v280',
          documentFileId:String(stored.fileId||''),note:`Entrada NF ${String(inv.number||'').trim()||'s/n'} • ${String(inv.supplier||'Fornecedor')}`,
          createdAt:now(),updatedAt:now()
        });
        const minKey=companyId+'::'+e.id;
        if(root.stock.minimums[minKey]==null)root.stock.minimums[minKey]=5;
        added++;
      });
      const msg=`NF registrada: ${added} entrada(s)${newEpis?' • '+newEpis+' novo(s) EPI(s)':''}${duplicates?' • '+duplicates+' duplicada(s) ignorada(s)':''}.`;
      saveAndReload(root,msg,'nfImportPc');
    }catch(err){
      toast(err?.message||'Falha ao registrar a NF.');
      btn.disabled=false;btn.textContent='＋ Registrar entrada no estoque';
    }
  }

  function caIdFromRow(tr){
    return tr?.querySelector('[data-v25-caopen]')?.dataset.v25Caopen||tr?.querySelector('[data-v25-cacheck]')?.dataset.v25Cacheck||'';
  }

  function caOfficialBlock(e){
    if(!e?.caValidationStatus&&!e?.caValidity)return '';
    return `<div class="pc280-ca-official"><b>Fonte oficial • ${esc(e.caValidationStatus||'consultado')}</b><small>${e.caValidity?'Validade CA: '+esc(e.caValidity):'Validade não localizada'}${e.caManufacturer?' • '+esc(e.caManufacturer):''}</small></div>`;
  }

  function decorateCaRows(){
    const table=$('#v25CaTable table');if(!table)return;
    const root=read();
    [...table.querySelectorAll('tbody tr')].forEach(tr=>{
      const id=caIdFromRow(tr),e=root.app.epis.find(x=>x.id===id);
      if(!id||!e)return;
      const action=tr.lastElementChild;
      if(action&&!action.querySelector('[data-pc280-caquery]')){
        const b=document.createElement('button');
        b.type='button';b.className='v25btn p';b.dataset.pc280Caquery=id;b.textContent='Consultar CA';
        action.append(' ',b);
      }
      const caCell=tr.children[1];
      if(caCell&&!caCell.querySelector('.pc280-ca-official')&&(e.caValidationStatus||e.caValidity)){
        caCell.insertAdjacentHTML('beforeend',caOfficialBlock(e));
      }
    });
  }

  function ensureCaToolbar(){
    const view=$('#caSmartPc');if(!view)return false;
    const head=view.querySelector('.v25h');if(!head)return false;
    let right=head.lastElementChild;
    if(!right||right===head.firstElementChild){
      right=document.createElement('div');head.appendChild(right);
    }
    if(!$('#pc280CaAutoAll')){
      const wrap=document.createElement('span');wrap.className='pc280-ca-toolbar';
      wrap.innerHTML='<button id="pc280CaAutoAll" type="button" class="v25btn p">✓ Consultar CAs automaticamente</button><span id="pc280CaLive" class="pc280-ca-live"></span>';
      right.appendChild(wrap);
      $('#pc280CaAutoAll').addEventListener('click',queryAllCas);
    }
    decorateCaRows();
    return true;
  }

  async function queryOneCa(id){
    if(!canOperate())return toast('Seu perfil é somente consulta.');
    const root=read(),e=root.app.epis.find(x=>x.id===id);
    if(!e?.ca)return toast('Este EPI não possui CA informado.');
    const live=$('#pc280CaLive');if(live)live.textContent='Consultando CA '+digits(e.ca)+'…';
    try{
      const res=await api('tenant_ai_assistant',{payload:{mode:'ca_validate',items:[{ca:digits(e.ca),name:e.name||'',manufacturer:e.model||e.manufacturer||''}]}});
      if(!res?.ok)throw new Error(res?.message||'Falha na consulta do CA.');
      const c=(res?.result?.checks||[])[0];
      if(!c?.found)throw new Error('CA não confirmado na fonte oficial.');
      e.caCheckedAt=now();e.caCheckedBy=String(window.GestaoEpiAuth?.user?.()?.name||window.GestaoEpiAuth?.user?.()?.username||'');
      e.caValidationStatus=String(c.status||'');e.caValidity=String(c.validity||'');e.caEquipment=String(c.equipment||'');e.caManufacturer=String(c.manufacturer||'');e.caSourceUrl=String(c.sourceUrl||'');e.caSourceType=String(c.sourceType||'');e.updatedAt=now();
      saveAndReload(root,`CA ${digits(e.ca)} consultado • ${c.status||'confirmado'}${c.validity?' • validade '+c.validity:''}.`,'caSmartPc');
    }catch(err){
      if(live)live.textContent='';
      toast(err?.message||'Falha na consulta do CA.');
    }
  }

  async function queryAllCas(){
    if(!canOperate())return toast('Seu perfil é somente consulta.');
    const root=read(),items=root.app.epis.filter(e=>e.active!==false&&digits(e.ca));
    if(!items.length)return toast('Nenhum CA informado para consultar.');
    const btn=$('#pc280CaAutoAll'),live=$('#pc280CaLive');
    btn.disabled=true;
    try{
      let ok=0,processed=0;
      for(let start=0;start<items.length;start+=20){
        const batch=items.slice(start,start+20);
        if(live)live.textContent=`Consultando CAs ${start+1}–${Math.min(start+20,items.length)} de ${items.length}…`;
        const res=await api('tenant_ai_assistant',{payload:{mode:'ca_validate',items:batch.map(e=>({ca:digits(e.ca),name:e.name||'',manufacturer:e.model||e.manufacturer||''}))}});
        if(!res?.ok)throw new Error(res?.message||'Falha na consulta dos CAs.');
        const map=new Map((res?.result?.checks||[]).map(check=>[digits(check.ca),check]));
        batch.forEach(e=>{
          processed++;
          const check=map.get(digits(e.ca));if(!check?.found)return;
          e.caCheckedAt=now();e.caCheckedBy=String(window.GestaoEpiAuth?.user?.()?.name||window.GestaoEpiAuth?.user?.()?.username||'');
          e.caValidationStatus=String(check.status||'');e.caValidity=String(check.validity||'');e.caEquipment=String(check.equipment||'');e.caManufacturer=String(check.manufacturer||'');e.caSourceUrl=String(check.sourceUrl||'');e.caSourceType=String(check.sourceType||'');e.updatedAt=now();ok++;
        });
      }
      saveAndReload(root,`${ok} de ${processed} CA(s) confirmado(s) pela fonte oficial.`,'caSmartPc');
    }catch(err){
      btn.disabled=false;if(live)live.textContent='';toast(err?.message||'Falha na consulta dos CAs.');
    }
  }

  function bindDelegation(){
    if(window.__pc280ParityBound)return;
    window.__pc280ParityBound=true;
    document.addEventListener('click',e=>{
      const b=e.target.closest('[data-pc280-caquery]');
      if(b){e.preventDefault();queryOneCa(b.dataset.pc280Caquery);return}
      const nav=e.target.closest('.nav[data-view="caSmartPc"]');
      if(nav)setTimeout(()=>{ensureCaToolbar();decorateCaRows()},120);
    },true);
    ['input','change'].forEach(type=>document.addEventListener(type,e=>{
      if(e.target?.matches?.('#v25CaSearch,#v25CaFilter'))setTimeout(decorateCaRows,80);
    },true));
  }

  function resume(){
    const view=sessionStorage.getItem(RESUME)||'';
    const flash=sessionStorage.getItem(FLASH)||'';
    if(view){
      sessionStorage.removeItem(RESUME);
      let n=0;
      const t=setInterval(()=>{
        n++;
        const b=$('.sidebar .nav[data-view="'+view+'"]');
        if(b){clearInterval(t);b.click();if(view==='nfImportPc')openNf();setTimeout(()=>{if(flash)toast(flash)},350)}
        else if(n>35){clearInterval(t)}
      },180);
    }else if(flash){
      sessionStorage.removeItem(FLASH);setTimeout(()=>toast(flash),900);
    }
    if(view)sessionStorage.removeItem(FLASH);
  }

  function boot(){
    css();bindDelegation();
    let n=0;
    const t=setInterval(()=>{
      n++;
      addNav();ensureNfView();ensureCaToolbar();decorateCaRows();
      if(n>25)clearInterval(t);
    },180);
    setTimeout(resume,600);
  }

  window.GestaoEpiPcParityV280={openNf,queryOneCa,queryAllCas};

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();