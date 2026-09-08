(() => {
  'use strict';
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const DEFAULT_MIN=5;
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const clean=(v='')=>String(v??'').replace(/\s+/g,' ').trim();
  const norm=(v='')=>clean(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;
  let currentInvoice=null;

  function readApp(){try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')};}catch{return {companies:[],workers:[],epis:[],deliveries:[]};}}
  function readStock(){try{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{},...JSON.parse(localStorage.getItem(STOCK_KEY)||'{}')};}catch{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}};}}
  function writeApp(x){localStorage.setItem(APP_KEY,JSON.stringify(x));}
  function writeStock(x){localStorage.setItem(STOCK_KEY,JSON.stringify(x));}
  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);}
  function nodeText(node,name){const el=node?.getElementsByTagNameNS?.('*',name)?.[0]||node?.getElementsByTagName?.(name)?.[0];return clean(el?.textContent||'');}
  function num(v){const n=Number(String(v??'').replace(',','.'));return Number.isFinite(n)?n:0;}
  function extractCa(text){const m=String(text||'').match(/(?:\bCA\b|C\.A\.)\s*[:#º°Nn-]*\s*(\d{3,6})\b/i);return m?m[1]:'';}
  function extractSize(text){const m=String(text||'').match(/(?:TAM(?:ANHO)?|NUM(?:ERA[CÇ][AÃ]O)?)\s*[:#º°-]*\s*([A-Z0-9.-]{1,8})\b/i);return m?m[1]:'';}
  function likelyEpi(text){return /capacete|oculos|óculos|luva|botina|bota|respirador|mascara|máscara|protetor|abafador|auricular|cinto|talabarte|vestimenta|avental|perneira|mangote|viseira|facial|creme protetor|calçado|calcado|epi\b/i.test(String(text||''));}
  function invoiceMarker(inv){return `NF_IMPORT:${inv.key||`${inv.supplierCnpj}|${inv.number}|${inv.series}|${inv.date}`}`;}
  function alreadyImported(stock,inv){const marker=invoiceMarker(inv);return (stock.movements||[]).some(m=>String(m.note||'').includes(marker));}

  function parseXml(text){
    const doc=new DOMParser().parseFromString(text,'application/xml');
    if(doc.querySelector('parsererror'))throw new Error('XML inválido.');
    const inf=doc.getElementsByTagNameNS('*','infNFe')[0]||doc.getElementsByTagName('infNFe')[0];
    if(!inf)throw new Error('Este XML não parece ser uma NF-e.');
    const ide=doc.getElementsByTagNameNS('*','ide')[0]||doc.getElementsByTagName('ide')[0];
    const emit=doc.getElementsByTagNameNS('*','emit')[0]||doc.getElementsByTagName('emit')[0];
    const prot=doc.getElementsByTagNameNS('*','protNFe')[0]||doc.getElementsByTagName('protNFe')[0];
    const key=nodeText(prot,'chNFe')||String(inf.getAttribute('Id')||'').replace(/^NFe/i,'');
    const items=[...(doc.getElementsByTagNameNS('*','det')||[])].map((det,index)=>{
      const prod=det.getElementsByTagNameNS('*','prod')[0]||det.getElementsByTagName('prod')[0];
      const extra=nodeText(det,'infAdProd');
      const name=nodeText(prod,'xProd');
      const joined=`${name} ${extra}`;
      return {index:index+1,code:nodeText(prod,'cProd'),name,qty:num(nodeText(prod,'qCom'))||1,unit:nodeText(prod,'uCom'),unitValue:num(nodeText(prod,'vUnCom')),total:num(nodeText(prod,'vProd')),ncm:nodeText(prod,'NCM'),ca:extractCa(joined),size:extractSize(joined),model:'',likely:likelyEpi(joined)};
    }).filter(x=>x.name);
    if(!items.length)throw new Error('Nenhum item encontrado na NF-e.');
    if(!items.some(x=>x.likely))items.forEach(x=>x.likely=true);
    return {format:'xml',key,number:nodeText(ide,'nNF'),series:nodeText(ide,'serie'),date:nodeText(ide,'dhEmi')||nodeText(ide,'dEmi'),supplier:nodeText(emit,'xNome'),supplierCnpj:nodeText(emit,'CNPJ'),items};
  }

  async function pdfLines(file){
    if(!window.pdfjsLib)throw new Error('Leitor de PDF não disponível.');
    pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    const pdf=await pdfjsLib.getDocument({data:new Uint8Array(await file.arrayBuffer())}).promise;
    const lines=[];
    for(let p=1;p<=Math.min(pdf.numPages,8);p++){
      const page=await pdf.getPage(p),tc=await page.getTextContent();
      const groups=new Map();
      for(const item of tc.items){const y=Math.round(item.transform?.[5]||0),x=item.transform?.[4]||0;let k=y;for(const old of groups.keys()){if(Math.abs(old-y)<=2){k=old;break;}}if(!groups.has(k))groups.set(k,[]);groups.get(k).push({x,t:clean(item.str)});}
      [...groups.entries()].sort((a,b)=>b[0]-a[0]).forEach(([,parts])=>{const line=parts.sort((a,b)=>a.x-b.x).map(x=>x.t).filter(Boolean).join(' ');if(line)lines.push(line);});
    }
    return lines;
  }
  function parsePdfHeuristic(lines){
    const text=lines.join('\n');
    const key=(text.match(/\b\d{44}\b/)||[])[0]||'';
    const number=(text.match(/(?:N[º°o.]?|NF-e|NOTA\s+FISCAL)\s*[:#-]?\s*(\d{1,9})/i)||[])[1]||'';
    const cnpj=(text.match(/\b\d{2}\.?\d{3}\.?\d{3}[\/\s]?\d{4}[-\s]?\d{2}\b/)||[])[0]||'';
    const epiLines=lines.filter(l=>likelyEpi(l));
    const items=epiLines.slice(0,80).map((line,i)=>{
      const qtyMatch=line.match(/(?:^|\s)(\d+(?:[.,]\d{1,3})?)\s*(?:UN|UND|PAR|PÇ|PC|CX)?(?:\s|$)/i);
      return {index:i+1,code:'',name:clean(line.replace(/\s+\d+[.,]\d{2}\s+\d+[.,]\d{2}.*$/,''))||clean(line),qty:qtyMatch?Math.max(1,num(qtyMatch[1])):1,unit:'UN',unitValue:0,total:0,ncm:'',ca:extractCa(line),size:extractSize(line),model:'',likely:true};
    });
    if(!items.length)throw new Error('Não consegui identificar EPIs automaticamente neste PDF. Use o XML da NF-e, que é mais confiável.');
    return {format:'pdf',key,number,series:'',date:'',supplier:'',supplierCnpj:cnpj,items};
  }

  function findExisting(app,item){
    if(item.ca){const byCa=(app.epis||[]).find(e=>String(e.ca||'').replace(/\D/g,'')===String(item.ca).replace(/\D/g,''));if(byCa)return byCa;}
    return (app.epis||[]).find(e=>norm(e.name)===norm(item.name)&&(!item.size||!e.size||norm(e.size)===norm(item.size)))||null;
  }

  function styles(){if($('#nfEpiStyle'))return;const s=document.createElement('style');s.id='nfEpiStyle';s.textContent=`
    .nfepi-box{margin-top:14px;border:1px solid #cfe0dd;background:#f8fbfb;border-radius:16px;padding:13px}.nfepi-box h3{margin:0 0 4px}.nfepi-box p{margin:0 0 10px;color:#647b78;font-size:12px;line-height:1.4}.nfepi-actions{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:end}.nfepi-actions input[type=file]{width:100%}.nfepi-preview{margin-top:12px;display:grid;gap:9px}.nfepi-meta{padding:10px;border-radius:11px;background:#eef7f5;font-size:12px}.nfepi-row{display:grid;grid-template-columns:auto 1fr 78px;gap:8px;align-items:start;padding:10px;border:1px solid #dce8e6;border-radius:12px;background:#fff}.nfepi-row .fields{display:grid;grid-template-columns:1fr 90px 90px;gap:6px}.nfepi-row input,.nfepi-row select{min-width:0;width:100%;padding:9px;border:1px solid #cbdad8;border-radius:9px}.nfepi-row small{display:block;color:#728783;margin-top:5px}.nfepi-row .qty{width:78px}.nfepi-confirm{width:100%;min-height:52px;margin-top:10px;border:0;border-radius:13px;background:#0f766e;color:#fff;font-weight:900}.nfepi-warn{padding:10px;border-radius:10px;background:#fff5e6;color:#8a5d10;font-size:12px}.nfepi-ok{padding:10px;border-radius:10px;background:#ecfdf3;color:#166534;font-size:12px}@media(max-width:600px){.nfepi-actions{grid-template-columns:1fr}.nfepi-row{grid-template-columns:auto 1fr}.nfepi-row .qty{grid-column:2}.nfepi-row .fields{grid-template-columns:1fr 1fr}.nfepi-row .fields .wide{grid-column:1/-1}}
  `;document.head.appendChild(s);}

  function inject(){
    const stock=$('#stock');if(!stock||$('#nfEpiBox'))return;
    const anchor=stock.querySelector('.stock-toolbar')||stock.querySelector('.card');
    const box=document.createElement('div');box.id='nfEpiBox';box.className='nfepi-box';box.innerHTML=`<h3>🧾 Importar EPI pela Nota Fiscal</h3><p>Use o XML da NF-e ou o PDF/DANFE. Você confere os itens antes de cadastrar e dar entrada no estoque.</p><div class="nfepi-actions"><label>Nota fiscal<input id="nfEpiFile" type="file" accept=".xml,.pdf,application/xml,text/xml,application/pdf"></label><button id="nfEpiRead" class="secondary" type="button">Ler nota</button></div><div id="nfEpiStatus"></div><div id="nfEpiPreview" class="nfepi-preview"></div>`;
    anchor?.insertAdjacentElement('afterend',box);
    $('#nfEpiRead')?.addEventListener('click',readSelected);
    $('#nfEpiFile')?.addEventListener('change',()=>{currentInvoice=null;$('#nfEpiPreview').innerHTML='';$('#nfEpiStatus').textContent='';});
  }

  async function readSelected(){
    const file=$('#nfEpiFile')?.files?.[0];if(!file)return toast('Selecione a nota fiscal.');
    const btn=$('#nfEpiRead');btn.disabled=true;btn.textContent='Lendo…';
    try{
      const ext=(file.name.split('.').pop()||'').toLowerCase();
      if(ext==='xml')currentInvoice=parseXml(await file.text());
      else if(ext==='pdf')currentInvoice=parsePdfHeuristic(await pdfLines(file));
      else throw new Error('Use XML ou PDF.');
      const stock=readStock();if(alreadyImported(stock,currentInvoice))throw new Error('Esta nota já foi importada. Nenhuma entrada foi repetida.');
      renderPreview();
    }catch(err){$('#nfEpiStatus').innerHTML=`<div class="nfepi-warn">${esc(err.message||String(err))}</div>`;$('#nfEpiPreview').innerHTML='';currentInvoice=null;}
    finally{btn.disabled=false;btn.textContent='Ler nota';}
  }

  function renderPreview(){
    const app=readApp(),inv=currentInvoice;if(!inv)return;
    const company=$('#stockCompany')?.value||'';
    $('#nfEpiStatus').innerHTML=`<div class="nfepi-meta"><b>${inv.format==='xml'?'NF-e XML':'DANFE/PDF'}</b>${inv.number?' • Nº '+esc(inv.number):''}${inv.series?' • Série '+esc(inv.series):''}${inv.supplier?' • '+esc(inv.supplier):''}${inv.key?' • chave '+esc(inv.key.slice(-12)):''}</div>${!company?'<div class="nfepi-warn" style="margin-top:8px">Selecione a empresa no Estoque antes de confirmar.</div>':''}`;
    const options=(item)=>{const found=findExisting(app,item);return `<option value="">Cadastrar novo EPI</option>`+(app.epis||[]).map(e=>`<option value="${esc(e.id)}" ${found?.id===e.id?'selected':''}>${esc(e.name)}${e.ca?' • CA '+esc(e.ca):''}${e.size?' • '+esc(e.size):''}</option>`).join('');};
    $('#nfEpiPreview').innerHTML=inv.items.map((item,i)=>`<div class="nfepi-row" data-nf-row="${i}"><input class="nf-select" type="checkbox" ${item.likely?'checked':''} aria-label="Importar item"><div><div class="fields"><input class="nf-name wide" value="${esc(item.name)}" placeholder="Nome do EPI"><input class="nf-ca" value="${esc(item.ca)}" placeholder="CA"><input class="nf-size" value="${esc(item.size)}" placeholder="Tamanho"></div><select class="nf-existing" style="margin-top:6px">${options(item)}</select><small>${item.code?'Cód. '+esc(item.code)+' • ':''}${item.unit||'UN'}${item.unitValue?' • R$ '+item.unitValue.toFixed(2):''}</small></div><input class="nf-qty qty" type="number" min="0.001" step="0.001" value="${item.qty}"></div>`).join('')+`<button id="nfEpiConfirm" class="nfepi-confirm" type="button">✓ Cadastrar EPIs e dar entrada no estoque</button>`;
    $('#nfEpiConfirm')?.addEventListener('click',confirmImport);
  }

  function confirmImport(){
    const inv=currentInvoice;if(!inv)return;
    const companyId=$('#stockCompany')?.value||'';if(!companyId)return toast('Selecione a empresa no Estoque.');
    const app=readApp(),stock=readStock();if(alreadyImported(stock,inv))return toast('Esta nota já foi importada.');
    const rows=$$('[data-nf-row]').filter(r=>r.querySelector('.nf-select')?.checked);if(!rows.length)return toast('Selecione pelo menos um item.');
    let created=0,entered=0;const marker=invoiceMarker(inv),now=new Date().toISOString();
    for(const row of rows){
      const name=clean(row.querySelector('.nf-name')?.value),ca=clean(row.querySelector('.nf-ca')?.value),size=clean(row.querySelector('.nf-size')?.value),qty=num(row.querySelector('.nf-qty')?.value),existingId=row.querySelector('.nf-existing')?.value||'';
      if(!name||qty<=0)continue;
      let epi=(app.epis||[]).find(e=>e.id===existingId)||null;
      if(!epi){epi=findExisting(app,{name,ca,size});}
      if(!epi){epi={id:uid('e'),name,ca,model:'',size,cycle:0,createdAt:now,updatedAt:now,source:'nota-fiscal'};app.epis.push(epi);created++;}
      const key=`${companyId}::${epi.id}`;if(stock.minimums[key]==null)stock.minimums[key]=DEFAULT_MIN;
      stock.movements.unshift({id:uid('sm'),type:'IN',delta:qty,companyId,epiId:epi.id,note:`Entrada por nota fiscal • ${marker}${inv.number?' • NF '+inv.number:''}${inv.supplier?' • '+inv.supplier:''}`,invoiceKey:inv.key||'',invoiceNumber:inv.number||'',invoiceSupplier:inv.supplier||'',createdAt:now});entered++;
    }
    if(!entered)return toast('Nenhum item válido para importar.');
    writeApp(app);writeStock(stock);
    try{window.GestaoEpiReloadFromStorage?.();}catch(_){ }
    document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'invoice-import'}}));
    const sel=$('#stockCompany');if(sel){const v=sel.value;sel.dispatchEvent(new Event('change',{bubbles:true}));sel.value=v;}
    $('#nfEpiStatus').innerHTML=`<div class="nfepi-ok">✓ Nota importada. ${created} EPI(s) novo(s) cadastrado(s) e ${entered} entrada(s) de estoque registrada(s).</div>`;
    $('#nfEpiPreview').innerHTML='';currentInvoice=null;$('#nfEpiFile').value='';toast('Nota fiscal importada com sucesso.');
  }

  function boot(){styles();inject();document.addEventListener('click',e=>{if(e.target.closest('[data-go="stock"]'))setTimeout(inject,40);});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
