(() => {
  'use strict';
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const DEFAULT_MIN=5;
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const CA_URL='https://caepi.trabalho.gov.br/internet/ConsultaCAInternet.aspx';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const clean=(v='')=>String(v??'').replace(/\s+/g,' ').trim();
  const norm=(v='')=>clean(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=(v)=>{const n=Number(String(v??'').replace(/\./g,'').replace(',','.'));return Number.isFinite(n)?n:0;};
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;
  let currentInvoice=null;
  let selectedFile=null;

  function readApp(){try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')};}catch{return {companies:[],workers:[],epis:[],deliveries:[]};}}
  function readStock(){try{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{},...JSON.parse(localStorage.getItem(STOCK_KEY)||'{}')};}catch{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}};}}
  function writeApp(x){localStorage.setItem(APP_KEY,JSON.stringify(x));}
  function writeStock(x){localStorage.setItem(STOCK_KEY,JSON.stringify(x));}
  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);}
  function authToken(){return window.GestaoEpiAuth?.token?.()||'';}
  function invoiceMarker(inv){return `NF_IMPORT:${inv.key||`${inv.supplierCnpj||''}|${inv.number||''}|${inv.series||''}|${inv.date||''}`}`;}
  function alreadyImported(stock,inv){const marker=invoiceMarker(inv);return (stock.movements||[]).some(m=>String(m.note||'').includes(marker));}
  function likelyEpi(v){return /capacete|oculos|óculos|luva|botina|bota|calçado|calcado|respirador|mascara|máscara|protetor|abafador|auricular|cinto|talabarte|vestimenta|avental|perneira|mangote|viseira|facial|creme protetor|epi\b/i.test(String(v||''));}
  function extractCa(v){const m=String(v||'').match(/(?:\bCA\b|C\.A\.)\s*[:.#º°-]*\s*(\d{3,6})\b/i);return m?m[1]:'';}
  function extractSize(v){const s=String(v||'');let m=s.match(/\bNR\.?\s*(\d{2})\b/i);if(m)return m[1];m=s.match(/(?:TAM(?:ANHO)?|NUM(?:ERA[CÇ][AÃ]O)?)\s*[:.#º°-]*\s*([A-Z0-9.-]{1,10})\b/i);if(m)return m[1];m=s.match(/\b(PP|P|M|G|GG|XG|XGG)(?:\s+(\d{1,2}(?:-\d{1,2})?))?\b/i);return m?clean(`${m[1]}${m[2]?' '+m[2]:''}`).toUpperCase():'';}
  function stripProductMeta(name){return clean(String(name||'').replace(/\bCA\s*[.:#º°-]*\s*\d{3,6}\b/ig,'').replace(/\bNR\.?\s*\d{2}\b/ig,'').replace(/\s{2,}/g,' '));}

  function toDataUrl(file){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result||''));r.onerror=()=>reject(r.error||new Error('Falha ao ler arquivo.'));r.readAsDataURL(file);});}
  async function pdfLines(file){if(!window.pdfjsLib)throw new Error('Leitor de PDF não disponível.');pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';const pdf=await pdfjsLib.getDocument({data:new Uint8Array(await file.arrayBuffer())}).promise;const lines=[];for(let p=1;p<=Math.min(pdf.numPages,8);p++){const page=await pdf.getPage(p),tc=await page.getTextContent(),groups=new Map();for(const item of tc.items){const y=Math.round(item.transform?.[5]||0),x=item.transform?.[4]||0;let key=y;for(const k of groups.keys()){if(Math.abs(k-y)<=2){key=k;break;}}if(!groups.has(key))groups.set(key,[]);groups.get(key).push({x,t:clean(item.str)});}[...groups.entries()].sort((a,b)=>b[0]-a[0]).forEach(([,parts])=>{const line=parts.sort((a,b)=>a.x-b.x).map(x=>x.t).filter(Boolean).join(' ');if(line)lines.push(line);});}return lines;}

  function parsePdfLocal(lines){
    const text=lines.join('\n');
    const key=(text.match(/\b\d{44}\b/)||[])[0]||'';
    const number=(text.match(/N[º°o.]?\s*0*([0-9]{3,9})/i)||text.match(/NF-e[^\d]{0,20}(\d{3,9})/i)||[])[1]||'';
    const rows=[];
    for(const line of lines){
      if(!likelyEpi(line))continue;
      const m=line.match(/^\s*(\d{1,12})\s+(.+?)\s+(\d{8})\s+\d{3}\s+\d{4}\s+(UN|UND|PAR|PÇ|PC|CX)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)/i);
      if(m){
        const rawName=clean(m[2]);
        rows.push({code:m[1],name:stripProductMeta(rawName),ca:extractCa(rawName),size:extractSize(rawName),unit:m[4].toUpperCase(),qty:num(m[5])||1,unitValue:num(m[6]),total:num(m[7]),manufacturer:'',isEpi:true,confidence:.86});
        continue;
      }
      const ca=extractCa(line);if(!ca)continue;
      const code=(line.match(/^\s*(\d{2,12})\b/)||[])[1]||'';
      rows.push({code,name:stripProductMeta(line.replace(/^\s*\d{2,12}\s+/,'')),ca,size:extractSize(line),unit:'',qty:1,unitValue:0,total:0,manufacturer:'',isEpi:true,confidence:.45});
    }
    const dedup=[];const seen=new Set();for(const r of rows){const k=`${r.code}|${norm(r.name)}|${r.ca}`;if(!seen.has(k)){seen.add(k);dedup.push(r);}}
    if(!dedup.length)throw new Error('Não consegui separar os EPIs deste PDF.');
    return {format:'pdf-local',key,number,series:'',date:'',supplier:'',supplierCnpj:'',items:dedup,ai:false};
  }

  function parseXml(text){
    const doc=new DOMParser().parseFromString(text,'application/xml');if(doc.querySelector('parsererror'))throw new Error('XML inválido.');
    const tag=(node,name)=>clean((node?.getElementsByTagNameNS?.('*',name)?.[0]||node?.getElementsByTagName?.(name)?.[0])?.textContent||'');
    const inf=doc.getElementsByTagNameNS('*','infNFe')[0]||doc.getElementsByTagName('infNFe')[0];if(!inf)throw new Error('Este XML não parece ser uma NF-e.');
    const ide=doc.getElementsByTagNameNS('*','ide')[0]||doc.getElementsByTagName('ide')[0],emit=doc.getElementsByTagNameNS('*','emit')[0]||doc.getElementsByTagName('emit')[0],prot=doc.getElementsByTagNameNS('*','protNFe')[0]||doc.getElementsByTagName('protNFe')[0];
    const items=[...(doc.getElementsByTagNameNS('*','det')||[])].map(det=>{const prod=det.getElementsByTagNameNS('*','prod')[0]||det.getElementsByTagName('prod')[0],raw=tag(prod,'xProd'),extra=tag(det,'infAdProd'),joined=`${raw} ${extra}`;return {code:tag(prod,'cProd'),name:stripProductMeta(raw),ca:extractCa(joined),size:extractSize(joined),unit:tag(prod,'uCom'),qty:Number(tag(prod,'qCom'))||1,unitValue:Number(tag(prod,'vUnCom'))||0,total:Number(tag(prod,'vProd'))||0,manufacturer:'',isEpi:likelyEpi(joined),confidence:1};}).filter(x=>x.name&&x.isEpi);
    return {format:'xml',key:tag(prot,'chNFe')||String(inf.getAttribute('Id')||'').replace(/^NFe/i,''),number:tag(ide,'nNF'),series:tag(ide,'serie'),date:tag(ide,'dhEmi')||tag(ide,'dEmi'),supplier:tag(emit,'xNome'),supplierCnpj:tag(emit,'CNPJ'),items,ai:false};
  }

  async function aiReadPdf(file){
    const token=authToken();if(!token)throw new Error('Faça login para usar a IA.');if(!navigator.onLine)throw new Error('Sem internet para usar a IA.');
    const documentData=await toDataUrl(file);if(documentData.length>18000000)throw new Error('O PDF é muito grande para análise por IA.');
    const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'tenant_ai_assistant',authToken:token,payload:{mode:'invoice_pdf_import',document:documentData}})});
    const data=await res.json();if(!data?.ok)throw new Error(data?.message||'A IA não conseguiu ler a nota.');
    const inv=data.result?.invoice||data.result||{};const items=Array.isArray(inv.items)?inv.items:[];
    if(!items.length)throw new Error('A IA não identificou EPIs nesta nota.');
    return {format:'pdf-ai',key:clean(inv.key),number:clean(inv.number),series:clean(inv.series),date:clean(inv.date),supplier:clean(inv.supplier),supplierCnpj:clean(inv.supplierCnpj),items:items.map(x=>({code:clean(x.code),name:stripProductMeta(x.name),ca:clean(x.ca).replace(/\D/g,''),size:clean(x.size),unit:clean(x.unit).toUpperCase(),qty:Math.max(.001,Number(x.qty)||1),unitValue:Number(x.unitValue)||0,total:Number(x.total)||0,manufacturer:clean(x.manufacturer),isEpi:x.isEpi!==false,confidence:Number(x.confidence)||0})).filter(x=>x.name&&x.isEpi),ai:true,provider:data.provider||'ia'};
  }

  async function validateCa(items){
    const token=authToken();const payloadItems=items.filter(x=>x.ca).map(x=>({ca:x.ca,name:x.name,manufacturer:x.manufacturer||''}));if(!token||!navigator.onLine||!payloadItems.length)return [];
    try{const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'tenant_ai_assistant',authToken:token,payload:{mode:'ca_validate',items:payloadItems}})});const data=await res.json();return data?.ok&&Array.isArray(data.result?.checks)?data.result.checks:[];}catch{return [];}
  }

  function applyChecks(inv,checks){const map=new Map((checks||[]).map(c=>[String(c.ca||'').replace(/\D/g,''),c]));inv.items.forEach(i=>{i.caCheck=map.get(String(i.ca||'').replace(/\D/g,''))||null;});}
  function findExisting(app,item){if(item.ca){const byCa=(app.epis||[]).find(e=>String(e.ca||'').replace(/\D/g,'')===String(item.ca).replace(/\D/g,''));if(byCa)return byCa;}return (app.epis||[]).find(e=>norm(e.name)===norm(item.name)&&(!item.size||!e.size||norm(e.size)===norm(item.size)))||null;}

  function styles(){if($('#nfAiStyle'))return;const s=document.createElement('style');s.id='nfAiStyle';s.textContent=`
    .nfai-box{margin:14px 0;border:1px solid #cfe0dd;background:#f8fbfb;border-radius:18px;padding:14px}.nfai-box h3{margin:0 0 5px}.nfai-box p{margin:0 0 11px;color:#647b78;font-size:12px;line-height:1.4}.nfai-actions{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:end}.nfai-actions input{width:100%}.nfai-preview{display:grid;gap:10px;margin-top:12px}.nfai-row{display:grid;grid-template-columns:28px 1fr;gap:9px;padding:12px;border:1px solid #dbe8e5;border-radius:14px;background:#fff}.nfai-fields{display:grid;grid-template-columns:1fr 90px 90px;gap:7px}.nfai-fields input,.nfai-row select,.nfai-qty{width:100%;box-sizing:border-box;min-height:44px;padding:8px;border:1px solid #cadbd7;border-radius:10px;background:#fff}.nfai-sub{display:grid;grid-template-columns:1fr 78px;gap:7px;margin-top:7px}.nfai-meta{padding:10px;border-radius:11px;background:#edf8f5;color:#315f59;font-size:12px;margin-top:10px}.nfai-status{margin-top:7px;font-size:11px}.nfai-pill{display:inline-block;padding:4px 8px;border-radius:999px;font-weight:850}.nfai-pill.ok{background:#eaf8ef;color:#176b36}.nfai-pill.warn{background:#fff4dc;color:#8a5d10}.nfai-pill.bad{background:#feecec;color:#9f2929}.nfai-official{margin-left:6px;color:#0f766e;font-weight:800}.nfai-confirm{width:100%;min-height:54px;border:0;border-radius:14px;background:#0f766e;color:#fff;font-weight:950;font-size:15px}.nfai-msg{padding:10px;border-radius:11px;margin-top:9px;font-size:12px}.nfai-msg.ok{background:#eaf8ef;color:#176b36}.nfai-msg.warn{background:#fff4dc;color:#8a5d10}@media(max-width:600px){.nfai-actions{grid-template-columns:1fr}.nfai-fields{grid-template-columns:1fr 1fr}.nfai-fields .wide{grid-column:1/-1}}
  `;document.head.appendChild(s);}

  function inject(){
    const stock=$('#stock');if(!stock)return;$('#nfEpiBox')?.remove();if($('#nfEpiAiBox'))return;
    const anchor=stock.querySelector('.stock-toolbar')||stock.querySelector('.card');const box=document.createElement('div');box.id='nfEpiAiBox';box.className='nfai-box';box.innerHTML=`<h3>✨ Importar EPI pela Nota Fiscal com IA</h3><p>A IA separa código, produto, CA, tamanho, unidade e quantidade. Depois tenta confirmar o CA usando fonte oficial do MTE. Nada é lançado sem sua conferência.</p><div class="nfai-actions"><label>XML da NF-e ou PDF/DANFE<input id="nfAiFile" type="file" accept=".xml,.pdf,application/xml,text/xml,application/pdf"></label><button id="nfAiRead" class="primary" type="button">✨ Ler com IA</button></div><div id="nfAiStatus"></div><div id="nfAiPreview" class="nfai-preview"></div>`;anchor?.insertAdjacentElement('afterend',box);$('#nfAiRead')?.addEventListener('click',readSelected);$('#nfAiFile')?.addEventListener('change',e=>{selectedFile=e.target.files?.[0]||null;currentInvoice=null;$('#nfAiPreview').innerHTML='';$('#nfAiStatus').innerHTML='';});
  }

  function checkHtml(item){if(!item.ca)return '<span class="nfai-pill warn">CA não informado</span>';const c=item.caCheck;if(!c)return `<span class="nfai-pill warn">CA ainda não confirmado</span><a class="nfai-official" href="${CA_URL}" target="_blank" rel="noopener">Consultar MTE</a>`;if(c.found===true){const status=norm(c.status);const cls=/venc|expir|cancel/.test(status)?'bad':'ok';return `<span class="nfai-pill ${cls}">CA ${esc(item.ca)} • ${esc(c.status||'confirmado')}</span><a class="nfai-official" href="${esc(c.sourceUrl||CA_URL)}" target="_blank" rel="noopener">Fonte oficial</a>`;}return `<span class="nfai-pill bad">CA ${esc(item.ca)} não confirmado</span><a class="nfai-official" href="${CA_URL}" target="_blank" rel="noopener">Consultar MTE</a>`;}

  function render(){
    const inv=currentInvoice,app=readApp();if(!inv)return;const company=$('#stockCompany')?.value||'';$('#nfAiStatus').innerHTML=`<div class="nfai-meta"><b>${inv.ai?'✨ IA':'Leitura estruturada'}</b>${inv.number?' • NF '+esc(inv.number):''}${inv.supplier?' • '+esc(inv.supplier):''} • ${inv.items.length} EPI(s) identificado(s)</div>${!company?'<div class="nfai-msg warn">Selecione a empresa no Estoque antes de confirmar.</div>':''}`;
    const opts=item=>{const f=findExisting(app,item);return '<option value="">Cadastrar novo EPI</option>'+app.epis.map(e=>`<option value="${esc(e.id)}" ${f?.id===e.id?'selected':''}>${esc(e.name)}${e.ca?' • CA '+esc(e.ca):''}${e.size?' • '+esc(e.size):''}</option>`).join('');};
    $('#nfAiPreview').innerHTML=inv.items.map((i,idx)=>`<div class="nfai-row" data-nfai="${idx}"><input class="nfai-check" type="checkbox" checked><div><div class="nfai-fields"><input class="nfai-name wide" value="${esc(i.name)}" placeholder="EPI"><input class="nfai-ca" value="${esc(i.ca)}" placeholder="CA"><input class="nfai-size" value="${esc(i.size)}" placeholder="Tamanho"></div><div class="nfai-sub"><select class="nfai-existing">${opts(i)}</select><input class="nfai-qty" type="number" min="0.001" step="0.001" value="${i.qty}"></div><small>Cód. ${esc(i.code||'—')} • Unidade: ${esc(i.unit||'—')}${i.manufacturer?' • '+esc(i.manufacturer):''}</small><div class="nfai-status">${checkHtml(i)}</div></div></div>`).join('')+'<button id="nfAiConfirm" class="nfai-confirm" type="button">✓ Conferir e lançar no estoque</button>';$('#nfAiConfirm')?.addEventListener('click',confirmImport);
  }

  async function readSelected(){
    const file=selectedFile||$('#nfAiFile')?.files?.[0];if(!file)return toast('Selecione a nota fiscal.');const btn=$('#nfAiRead');btn.disabled=true;btn.textContent='✨ Analisando…';$('#nfAiStatus').innerHTML='<div class="nfai-msg warn">A IA está lendo a nota e separando os EPIs…</div>';
    try{const ext=(file.name.split('.').pop()||'').toLowerCase();if(ext==='xml')currentInvoice=parseXml(await file.text());else if(ext==='pdf'){try{currentInvoice=await aiReadPdf(file);}catch(aiErr){currentInvoice=parsePdfLocal(await pdfLines(file));currentInvoice.aiError=String(aiErr?.message||aiErr);}}else throw new Error('Use XML ou PDF.');if(!currentInvoice.items.length)throw new Error('Nenhum EPI identificado.');if(alreadyImported(readStock(),currentInvoice))throw new Error('Esta nota já foi importada.');const checks=await validateCa(currentInvoice.items);applyChecks(currentInvoice,checks);render();if(currentInvoice.aiError)$('#nfAiStatus').insertAdjacentHTML('beforeend',`<div class="nfai-msg warn">A IA do servidor não respondeu, então usei a leitura local corrigida. ${esc(currentInvoice.aiError)}</div>`);}catch(err){currentInvoice=null;$('#nfAiPreview').innerHTML='';$('#nfAiStatus').innerHTML=`<div class="nfai-msg warn">${esc(err.message||String(err))}</div>`;}finally{btn.disabled=false;btn.textContent='✨ Ler com IA';}
  }

  function confirmImport(){
    const inv=currentInvoice;if(!inv)return;const companyId=$('#stockCompany')?.value||'';if(!companyId)return toast('Selecione a empresa no Estoque.');const app=readApp(),stock=readStock();if(alreadyImported(stock,inv))return toast('Esta nota já foi importada.');const rows=$$('[data-nfai]').filter(r=>r.querySelector('.nfai-check')?.checked);if(!rows.length)return toast('Selecione pelo menos um EPI.');const now=new Date().toISOString(),marker=invoiceMarker(inv);let created=0,entered=0;
    for(const row of rows){const idx=Number(row.dataset.nfai),src=inv.items[idx]||{},name=clean(row.querySelector('.nfai-name')?.value),ca=clean(row.querySelector('.nfai-ca')?.value).replace(/\D/g,''),size=clean(row.querySelector('.nfai-size')?.value),qty=Number(row.querySelector('.nfai-qty')?.value||0),existingId=row.querySelector('.nfai-existing')?.value||'';if(!name||qty<=0)continue;let epi=app.epis.find(e=>e.id===existingId)||findExisting(app,{name,ca,size});const chk=src.caCheck||null;if(!epi){epi={id:uid('e'),name,ca,model:clean(chk?.manufacturer||src.manufacturer||''),size,cycle:0,createdAt:now,updatedAt:now,source:'nota-fiscal-ia',caVerified:chk?.found===true,caStatus:clean(chk?.status),caCheckedAt:chk?now:'',caSource:clean(chk?.sourceUrl)};app.epis.push(epi);created++;}else if(!epi.ca&&ca){epi.ca=ca;epi.updatedAt=now;if(chk){epi.caVerified=chk.found===true;epi.caStatus=clean(chk.status);epi.caCheckedAt=now;epi.caSource=clean(chk.sourceUrl);}}
      const sk=`${companyId}::${epi.id}`;if(stock.minimums[sk]==null)stock.minimums[sk]=DEFAULT_MIN;stock.movements.unshift({id:uid('sm'),type:'IN',delta:qty,companyId,epiId:epi.id,note:`Entrada por nota fiscal IA • ${marker}${inv.number?' • NF '+inv.number:''}${inv.supplier?' • '+inv.supplier:''}`,invoiceKey:inv.key||'',invoiceNumber:inv.number||'',invoiceSupplier:inv.supplier||'',createdAt:now});entered++;}
    if(!entered)return toast('Nenhum item válido para importar.');writeApp(app);writeStock(stock);document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'invoice-ai-import'}}));$('#nfAiStatus').innerHTML=`<div class="nfai-msg ok">✓ Nota importada. ${created} EPI(s) novo(s) e ${entered} entrada(s) de estoque.</div>`;$('#nfAiPreview').innerHTML='';currentInvoice=null;selectedFile=null;$('#nfAiFile').value='';toast('Nota fiscal importada com sucesso.');
  }

  function boot(){styles();inject();let tries=0;const timer=setInterval(()=>{tries++;$('#nfEpiBox')?.remove();inject();if(tries>8)clearInterval(timer);},400);document.addEventListener('click',e=>{if(e.target.closest('[data-go="stock"]'))setTimeout(inject,60);});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();