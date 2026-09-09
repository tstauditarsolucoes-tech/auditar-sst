(() => {
  'use strict';

  const MOBILE_APP='auditarEpiV1';
  const MOBILE_STOCK='auditarEpiStockV1';
  const PC_CACHE='auditarEpiGestaoCacheV1';
  const DEFAULT_MIN=5;
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const CA_URL='https://caepi.trabalho.gov.br/internet/ConsultaCAInternet.aspx';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const clean=(v='')=>String(v??'').replace(/\s+/g,' ').trim();
  const norm=(v='')=>clean(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;
  const digits=v=>String(v??'').replace(/\D/g,'');
  let currentInvoice=null;
  let selectedFile=null;

  function isPc(){return !!document.querySelector('.sidebar') || (!!localStorage.getItem(PC_CACHE)&&!localStorage.getItem(MOBILE_APP));}
  function blankApp(){return {companies:[],workers:[],epis:[],deliveries:[]};}
  function blankStock(){return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}};}
  function readState(){
    try{
      if(isPc()){
        const root=JSON.parse(localStorage.getItem(PC_CACHE)||'{}');
        return {root,app:{...blankApp(),...(root.app||{})},stock:{...blankStock(),...(root.stock||{})},pc:true};
      }
      return {root:null,app:{...blankApp(),...JSON.parse(localStorage.getItem(MOBILE_APP)||'{}')},stock:{...blankStock(),...JSON.parse(localStorage.getItem(MOBILE_STOCK)||'{}')},pc:false};
    }catch{return {root:null,app:blankApp(),stock:blankStock(),pc:isPc()};}
  }
  function writeState(state){
    if(state.pc){
      const root={...(state.root||{}),version:1,revision:Number(state.root?.revision||0)+1,updatedAt:new Date().toISOString(),app:state.app,stock:state.stock};
      localStorage.setItem(PC_CACHE,JSON.stringify(root));
      document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'invoice-ai-v350'}}));
      return;
    }
    localStorage.setItem(MOBILE_APP,JSON.stringify(state.app));
    localStorage.setItem(MOBILE_STOCK,JSON.stringify(state.stock));
    document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'invoice-ai-v350'}}));
  }
  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),3000);}
  function authToken(){return window.GestaoEpiAuth?.token?.()||'';}
  function companySelect(){return $(isPc()?'#globalCompany':'#stockCompany');}
  function selectedCompany(){return companySelect()?.value||'';}
  function invoiceMarker(inv){return `NF_IMPORT:${inv.key||`${inv.supplierCnpj||''}|${inv.number||''}|${inv.series||''}|${inv.date||''}`}`;}
  function alreadyImported(stock,inv){const marker=invoiceMarker(inv);return (stock.movements||[]).some(m=>String(m.note||'').includes(marker));}
  function likelyEpi(v){return /capacete|oculos|óculos|luva|botina|bota|calçado|calcado|respirador|mascara|máscara|protetor|abafador|auricular|cinto|talabarte|vestimenta|avental|perneira|mangote|viseira|facial|creme protetor|epi\b/i.test(String(v||''));}
  function extractCa(v){const m=String(v||'').match(/(?:\bCA\b|C\.A\.)\s*[:.#º°-]*\s*(\d{3,6})\b/i);return m?m[1]:'';}
  function extractSize(v){const s=String(v||'');let m=s.match(/\bNR\.?\s*(\d{2})\b/i);if(m)return m[1];m=s.match(/(?:TAM(?:ANHO)?|NUM(?:ERA[CÇ][AÃ]O)?)\s*[:.#º°-]*\s*([A-Z0-9.-]{1,10})\b/i);if(m)return m[1];m=s.match(/\b(PP|P|M|G|GG|XG|XGG)(?:\s+(\d{1,2}(?:-\d{1,2})?))?\b/i);return m?clean(`${m[1]}${m[2]?' '+m[2]:''}`).toUpperCase():'';}
  function stripProductMeta(name){return clean(String(name||'').replace(/\bCA\s*[.:#º°-]*\s*\d{3,6}\b/ig,' ').replace(/\bNR\.?\s*\d{2}\b/ig,' ').replace(/\s{2,}/g,' '));}
  function numberPt(v){const s=String(v??'').trim();if(!s)return 0;if(s.includes(',')&&s.includes('.'))return Number(s.replace(/\./g,'').replace(',','.'))||0;if(s.includes(','))return Number(s.replace(',','.'))||0;return Number(s)||0;}

  function toDataUrl(file){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result||''));r.onerror=()=>reject(r.error||new Error('Falha ao ler arquivo.'));r.readAsDataURL(file);});}
  async function pdfLines(file){
    if(!window.pdfjsLib)throw new Error('Leitor de PDF não disponível.');
    pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    const pdf=await pdfjsLib.getDocument({data:new Uint8Array(await file.arrayBuffer())}).promise;
    const lines=[];
    for(let p=1;p<=Math.min(pdf.numPages,8);p++){
      const page=await pdf.getPage(p),tc=await page.getTextContent(),groups=new Map();
      for(const item of tc.items){
        const y=Math.round(item.transform?.[5]||0),x=item.transform?.[4]||0;let key=y;
        for(const k of groups.keys()){if(Math.abs(k-y)<=2){key=k;break;}}
        if(!groups.has(key))groups.set(key,[]);groups.get(key).push({x,t:clean(item.str)});
      }
      [...groups.entries()].sort((a,b)=>b[0]-a[0]).forEach(([,parts])=>{const line=parts.sort((a,b)=>a.x-b.x).map(x=>x.t).filter(Boolean).join(' ');if(line)lines.push(line);});
    }
    return lines;
  }
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
        rows.push({code:m[1],name:stripProductMeta(rawName),ca:extractCa(rawName),size:extractSize(rawName),unit:m[4].toUpperCase(),qty:numberPt(m[5])||1,unitValue:numberPt(m[6]),total:numberPt(m[7]),manufacturer:'',isEpi:true,confidence:.82,source:'local'});
        continue;
      }
      const ca=extractCa(line);if(!ca)continue;
      const code=(line.match(/^\s*(\d{2,12})\b/)||[])[1]||'';
      rows.push({code,name:stripProductMeta(line.replace(/^\s*\d{2,12}\s+/,'')),ca,size:extractSize(line),unit:'',qty:1,unitValue:0,total:0,manufacturer:'',isEpi:true,confidence:.35,source:'local'});
    }
    const dedup=[];const seen=new Set();
    for(const r of rows){const k=`${r.code}|${norm(r.name)}|${r.ca}|${r.size}`;if(!seen.has(k)){seen.add(k);dedup.push(r);}}
    if(!dedup.length)throw new Error('Não consegui separar os EPIs deste PDF.');
    return {format:'pdf-local',key,number,series:'',date:'',supplier:'',supplierCnpj:'',items:dedup,ai:false};
  }
  function parseXml(text){
    const doc=new DOMParser().parseFromString(text,'application/xml');if(doc.querySelector('parsererror'))throw new Error('XML inválido.');
    const tag=(node,name)=>clean((node?.getElementsByTagNameNS?.('*',name)?.[0]||node?.getElementsByTagName?.(name)?.[0])?.textContent||'');
    const inf=doc.getElementsByTagNameNS('*','infNFe')[0]||doc.getElementsByTagName('infNFe')[0];if(!inf)throw new Error('Este XML não parece ser uma NF-e.');
    const ide=doc.getElementsByTagNameNS('*','ide')[0]||doc.getElementsByTagName('ide')[0],emit=doc.getElementsByTagNameNS('*','emit')[0]||doc.getElementsByTagName('emit')[0],prot=doc.getElementsByTagNameNS('*','protNFe')[0]||doc.getElementsByTagName('protNFe')[0];
    const dets=[...(doc.getElementsByTagNameNS('*','det')||[])];
    const items=dets.map(det=>{const prod=det.getElementsByTagNameNS('*','prod')[0]||det.getElementsByTagName('prod')[0],raw=tag(prod,'xProd'),extra=tag(det,'infAdProd'),joined=`${raw} ${extra}`;return {code:tag(prod,'cProd'),name:stripProductMeta(raw),ca:extractCa(joined),size:extractSize(joined),unit:tag(prod,'uCom'),qty:Number(tag(prod,'qCom'))||1,unitValue:Number(tag(prod,'vUnCom'))||0,total:Number(tag(prod,'vProd'))||0,manufacturer:'',isEpi:likelyEpi(joined),confidence:1,source:'xml'};}).filter(x=>x.name&&x.isEpi);
    return {format:'xml',key:tag(prot,'chNFe')||String(inf.getAttribute('Id')||'').replace(/^NFe/i,''),number:tag(ide,'nNF'),series:tag(ide,'serie'),date:tag(ide,'dhEmi')||tag(ide,'dEmi'),supplier:tag(emit,'xNome'),supplierCnpj:tag(emit,'CNPJ'),items,ai:false};
  }
  async function aiReadPdf(file){
    const token=authToken();if(!token)throw new Error('Faça login para usar a IA.');if(!navigator.onLine)throw new Error('Sem internet para usar a IA.');
    const documentData=await toDataUrl(file);if(documentData.length>18000000)throw new Error('O PDF é muito grande para análise por IA.');
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);
    try{
      const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'tenant_ai_assistant',authToken:token,payload:{mode:'invoice_pdf_import',document:documentData}}),signal:controller.signal});
      const data=await res.json();if(!data?.ok)throw new Error(data?.message||'A IA não conseguiu ler a nota.');
      const inv=data.result?.invoice||data.result||{},items=Array.isArray(inv.items)?inv.items:[];if(!items.length)throw new Error('A IA não identificou EPIs nesta nota.');
      return {format:'pdf-ai',key:clean(inv.key),number:clean(inv.number),series:clean(inv.series),date:clean(inv.date),supplier:clean(inv.supplier),supplierCnpj:clean(inv.supplierCnpj),items:items.map(x=>({code:clean(x.code),name:stripProductMeta(x.name),ca:digits(x.ca),size:clean(x.size),unit:clean(x.unit).toUpperCase(),qty:Math.max(.001,Number(x.qty)||1),unitValue:Number(x.unitValue)||0,total:Number(x.total)||0,manufacturer:clean(x.manufacturer),isEpi:x.isEpi!==false,confidence:Number(x.confidence)||0,source:'ai'})).filter(x=>x.name&&x.isEpi),ai:true,provider:data.provider||'gemini'};
    }finally{clearTimeout(timer);}
  }
  async function validateCa(items){
    const token=authToken(),payloadItems=items.filter(x=>x.ca).map(x=>({ca:x.ca,name:x.name,manufacturer:x.manufacturer||''}));if(!token||!navigator.onLine||!payloadItems.length)return [];
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),22000);
    try{
      const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'tenant_ai_assistant',authToken:token,payload:{mode:'ca_validate',items:payloadItems}}),signal:controller.signal});
      const data=await res.json();return data?.ok&&Array.isArray(data.result?.checks)?data.result.checks:[];
    }catch{return [];}finally{clearTimeout(timer);}
  }
  function applyChecks(inv,checks){const map=new Map((checks||[]).map(c=>[digits(c.ca),c]));inv.items.forEach(i=>{i.caCheck=map.get(digits(i.ca))||null;});}

  function findExisting(app,item){
    const ca=digits(item.ca),size=norm(item.size);
    if(ca){
      const sameCa=(app.epis||[]).filter(e=>digits(e.ca)===ca);
      const exact=sameCa.find(e=>!size||!e.size||norm(e.size)===size);if(exact)return exact;
    }
    return (app.epis||[]).find(e=>norm(e.name)===norm(item.name)&&(!size||!e.size||norm(e.size)===size))||null;
  }
  function existingMismatch(epi,item){
    if(!epi)return '';
    const itemCa=digits(item.ca),epiCa=digits(epi.ca);
    if(itemCa&&epiCa&&itemCa!==epiCa)return `CA da nota (${itemCa}) difere do CA cadastrado (${epiCa}).`;
    if(item.size&&epi.size&&norm(item.size)!==norm(epi.size))return `Tamanho da nota (${item.size}) difere do cadastro (${epi.size}).`;
    return '';
  }
  function confidenceInfo(item){
    const c=Number(item.confidence||0);
    if(item.source==='xml')return {level:'ok',text:'Leitura estruturada do XML',block:false};
    if(c>=.78)return {level:'ok',text:`Confiança ${Math.round(c*100)}%`,block:false};
    if(c>=.55)return {level:'warn',text:`Conferir • confiança ${Math.round(c*100)}%`,block:true};
    return {level:'bad',text:`Duvidoso • confiança ${Math.round(c*100)}%`,block:true};
  }
  function caInfo(item){
    if(!item.ca)return {level:'warn',text:'CA não informado',block:false};
    const c=item.caCheck;if(!c)return {level:'warn',text:`CA ${item.ca} ainda não confirmado`,block:true};
    if(c.found!==true)return {level:'bad',text:`CA ${item.ca} não confirmado em fonte oficial`,block:true};
    const st=norm(c.status);if(/venc|expir|cancel/.test(st))return {level:'bad',text:`CA ${item.ca} • ${c.status||'situação irregular'}`,block:true};
    return {level:'ok',text:`CA ${item.ca} • ${c.status||'confirmado'}`,block:false};
  }
  function riskFor(item,epi){
    const reasons=[];const conf=confidenceInfo(item),ca=caInfo(item),mismatch=existingMismatch(epi,item);
    if(conf.block)reasons.push(conf.text);if(ca.block)reasons.push(ca.text);if(mismatch)reasons.push(mismatch);
    if(Number(item.qty)<=0)reasons.push('Quantidade inválida.');
    if(Number(item.qty)>=1000)reasons.push('Quantidade muito alta; confira se não é código do produto.');
    if(!clean(item.name))reasons.push('Nome do EPI vazio.');
    return {blocked:reasons.length>0,reasons,conf,ca};
  }

  function styles(){
    if($('#nfAi350Style'))return;const s=document.createElement('style');s.id='nfAi350Style';s.textContent=`
      .nf350-box{margin:14px 0;border:1px solid #cfe0dd;background:#f8fbfb;border-radius:18px;padding:14px}.nf350-box h3{margin:0 0 5px}.nf350-box p{margin:0 0 11px;color:#647b78;font-size:12px;line-height:1.4}.nf350-actions{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:end}.nf350-actions input{width:100%}.nf350-preview{display:grid;gap:10px;margin-top:12px}.nf350-row{display:grid;grid-template-columns:28px 1fr;gap:9px;padding:12px;border:1px solid #dbe8e5;border-radius:14px;background:#fff}.nf350-row.risk{border-color:#e9c66f;background:#fffaf0}.nf350-row.blocked{border-color:#efaaaa;background:#fff6f6}.nf350-fields{display:grid;grid-template-columns:1fr 90px 90px;gap:7px}.nf350-fields input,.nf350-row select,.nf350-qty{width:100%;box-sizing:border-box;min-height:44px;padding:8px;border:1px solid #cadbd7;border-radius:10px;background:#fff}.nf350-sub{display:grid;grid-template-columns:1fr 90px;gap:7px;margin-top:7px}.nf350-meta{padding:10px;border-radius:11px;background:#edf8f5;color:#315f59;font-size:12px;margin-top:10px}.nf350-msg{padding:10px;border-radius:11px;margin-top:9px;font-size:12px}.nf350-msg.ok{background:#eaf8ef;color:#176b36}.nf350-msg.warn{background:#fff4dc;color:#8a5d10}.nf350-msg.bad{background:#feecec;color:#9f2929}.nf350-pills{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.nf350-pill{display:inline-block;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:850}.nf350-pill.ok{background:#eaf8ef;color:#176b36}.nf350-pill.warn{background:#fff4dc;color:#8a5d10}.nf350-pill.bad{background:#feecec;color:#9f2929}.nf350-official{color:#0f766e;font-weight:800}.nf350-confirm{width:100%;min-height:54px;border:0;border-radius:14px;background:#0f766e;color:#fff;font-weight:950;font-size:15px}.nf350-confirm:disabled{opacity:.5}.nf350-review{font-size:11px;color:#8a5d10;margin-top:7px}.nf350-continue{margin-top:7px;display:flex;align-items:center;gap:6px;font-size:11px;font-weight:800;color:#794b00}@media(max-width:600px){.nf350-actions{grid-template-columns:1fr}.nf350-fields{grid-template-columns:1fr 1fr}.nf350-fields .wide{grid-column:1/-1}.nf350-sub{grid-template-columns:1fr 88px}}
    `;document.head.appendChild(s);
  }
  function inject(){
    const stock=$('#stock');if(!stock)return;$('#nfEpiBox')?.remove();$('#nfEpiAiBox')?.remove();if($('#nfEpiAi350Box'))return;
    const anchor=stock.querySelector('.stock-toolbar')||stock.querySelector('.panel')||stock.querySelector('.card');if(!anchor)return;
    const box=document.createElement('div');box.id='nfEpiAi350Box';box.className='nf350-box';box.innerHTML=`<h3>✨ Importar EPI pela Nota Fiscal com IA</h3><p>A IA lê a nota, separa código, quantidade, CA e tamanho, consulta o CA e bloqueia automaticamente itens duvidosos até sua conferência.</p><div class="nf350-actions"><label>XML da NF-e ou PDF/DANFE<input id="nf350File" type="file" accept=".xml,.pdf,application/xml,text/xml,application/pdf"></label><button id="nf350Read" class="primary" type="button">✨ Ler nota</button></div><div id="nf350Status"></div><div id="nf350Preview" class="nf350-preview"></div>`;
    anchor.insertAdjacentElement('afterend',box);
    $('#nf350File')?.addEventListener('change',e=>{selectedFile=e.target.files?.[0]||null;currentInvoice=null;$('#nf350Preview').innerHTML='';$('#nf350Status').innerHTML='';});
    $('#nf350Read')?.addEventListener('click',readSelected);
  }
  function optionHtml(app,item){
    const guessed=findExisting(app,item);
    return '<option value="">Cadastrar novo EPI / nova variação</option>'+(app.epis||[]).map(e=>`<option value="${esc(e.id)}" ${guessed?.id===e.id?'selected':''}>${esc(e.name)}${e.ca?' • CA '+esc(e.ca):''}${e.size?' • '+esc(e.size):''}</option>`).join('');
  }
  function render(){
    if(!currentInvoice)return;const state=readState(),app=state.app,company=selectedCompany();
    const header=`<div class="nf350-meta"><b>${currentInvoice.ai?'✨ IA Gemini':'Leitura estruturada/local'}</b>${currentInvoice.number?' • NF '+esc(currentInvoice.number):''}${currentInvoice.supplier?' • '+esc(currentInvoice.supplier):''} • ${currentInvoice.items.length} EPI(s)</div>`;
    $('#nf350Status').innerHTML=header+(!company?'<div class="nf350-msg warn">Selecione a empresa antes de confirmar a entrada.</div>':'');
    $('#nf350Preview').innerHTML=currentInvoice.items.map((item,idx)=>{
      const existing=findExisting(app,item),risk=riskFor(item,existing),rowClass=risk.blocked?'blocked':risk.conf.level==='warn'?'risk':'';
      const source=item.caCheck?.sourceUrl||CA_URL;
      return `<div class="nf350-row ${rowClass}" data-nf350="${idx}" data-confidence="${Number(item.confidence||0)}"><input class="nf350-check" type="checkbox" ${risk.blocked?'':'checked'}><div><div class="nf350-fields"><input class="nf350-name wide" value="${esc(item.name)}" placeholder="EPI"><input class="nf350-ca" value="${esc(item.ca)}" placeholder="CA"><input class="nf350-size" value="${esc(item.size)}" placeholder="Tamanho"></div><div class="nf350-sub"><select class="nf350-existing">${optionHtml(app,item)}</select><input class="nf350-qty" type="number" min="0.001" step="0.001" value="${Number(item.qty)||1}"></div><small>Cód. ${esc(item.code||'—')} • Unidade: ${esc(item.unit||'—')}${item.manufacturer?' • '+esc(item.manufacturer):''}</small><div class="nf350-pills"><span class="nf350-pill ${risk.conf.level}">${esc(risk.conf.text)}</span><span class="nf350-pill ${risk.ca.level}">${esc(risk.ca.text)}</span>${item.ca?`<a class="nf350-official" href="${esc(source)}" target="_blank" rel="noopener">Fonte oficial</a>`:''}</div>${risk.reasons.length?`<div class="nf350-review">⚠ ${risk.reasons.map(esc).join(' ')}</div><label class="nf350-continue"><input type="checkbox" class="nf350-reviewed">Conferi manualmente este item e autorizo o lançamento</label>`:''}</div></div>`;
    }).join('')+'<button id="nf350Confirm" class="nf350-confirm" type="button">✓ Conferir e lançar no estoque</button>';
    $('#nf350Confirm')?.addEventListener('click',confirmImport);
    $('#nf350Preview')?.addEventListener('input',onPreviewInput);
    $('#nf350Preview')?.addEventListener('change',onPreviewInput);
  }
  function rowItem(row){
    const src=currentInvoice?.items?.[Number(row.dataset.nf350)]||{};
    return {...src,name:clean(row.querySelector('.nf350-name')?.value),ca:digits(row.querySelector('.nf350-ca')?.value),size:clean(row.querySelector('.nf350-size')?.value),qty:Number(row.querySelector('.nf350-qty')?.value||0)};
  }
  function onPreviewInput(e){
    const row=e.target.closest?.('[data-nf350]');if(!row||!currentInvoice)return;
    const state=readState(),item=rowItem(row),existingId=row.querySelector('.nf350-existing')?.value||'',existing=state.app.epis.find(x=>x.id===existingId)||findExisting(state.app,item),risk=riskFor(item,existing);
    row.classList.toggle('blocked',risk.blocked);row.classList.toggle('risk',!risk.blocked&&risk.conf.level==='warn');
    const review=row.querySelector('.nf350-review'),manual=row.querySelector('.nf350-continue');
    if(review)review.innerHTML=risk.reasons.length?'⚠ '+risk.reasons.map(esc).join(' '):'';
    if(manual)manual.style.display=risk.reasons.length?'flex':'none';
  }
  async function readSelected(){
    const file=selectedFile||$('#nf350File')?.files?.[0];if(!file)return toast('Selecione a nota fiscal.');
    const btn=$('#nf350Read');btn.disabled=true;btn.textContent='✨ Analisando…';$('#nf350Status').innerHTML='<div class="nf350-msg warn">Lendo a nota e conferindo os CA…</div>';$('#nf350Preview').innerHTML='';
    try{
      const ext=(file.name.split('.').pop()||'').toLowerCase();
      if(ext==='xml')currentInvoice=parseXml(await file.text());
      else if(ext==='pdf'){
        try{currentInvoice=await aiReadPdf(file);}catch(aiErr){currentInvoice=parsePdfLocal(await pdfLines(file));currentInvoice.aiError=String(aiErr?.message||aiErr);}
      }else throw new Error('Use um arquivo XML ou PDF.');
      if(!currentInvoice.items.length)throw new Error('Nenhum EPI identificado.');
      if(alreadyImported(readState().stock,currentInvoice))throw new Error('Esta nota já foi importada anteriormente.');
      applyChecks(currentInvoice,await validateCa(currentInvoice.items));
      render();
      if(currentInvoice.aiError)$('#nf350Status').insertAdjacentHTML('beforeend',`<div class="nf350-msg warn">A IA não respondeu e foi usada a leitura local corrigida. Revise os itens antes de lançar.</div>`);
    }catch(err){currentInvoice=null;$('#nf350Preview').innerHTML='';$('#nf350Status').innerHTML=`<div class="nf350-msg bad">${esc(err?.name==='AbortError'?'A análise demorou demais. Tente novamente.':err.message||String(err))}</div>`;}
    finally{btn.disabled=false;btn.textContent='✨ Ler nota';}
  }
  function confirmImport(){
    if(!currentInvoice)return;const companyId=selectedCompany();if(!companyId)return toast('Selecione a empresa.');
    const state=readState(),app=state.app,stock=state.stock;if(alreadyImported(stock,currentInvoice))return toast('Esta nota já foi importada.');
    const rows=$$('[data-nf350]').filter(r=>r.querySelector('.nf350-check')?.checked);if(!rows.length)return toast('Selecione pelo menos um item.');
    const now=new Date().toISOString(),marker=invoiceMarker(currentInvoice);let created=0,entered=0,updated=0;
    for(const row of rows){
      const src=currentInvoice.items[Number(row.dataset.nf350)]||{},item=rowItem(row),existingId=row.querySelector('.nf350-existing')?.value||'';
      if(!item.name||item.qty<=0)continue;
      let epi=app.epis.find(e=>e.id===existingId)||findExisting(app,item);const risk=riskFor(item,epi);const reviewed=row.querySelector('.nf350-reviewed')?.checked===true;
      if(risk.blocked&&!reviewed){toast('Existe item duvidoso selecionado. Marque “Conferi manualmente” antes de lançar.');row.scrollIntoView({behavior:'smooth',block:'center'});return;}
      const chk=src.caCheck||null;
      if(epi&&existingMismatch(epi,item)&&!reviewed){toast('O CA ou tamanho não corresponde ao cadastro selecionado. Confira o item.');row.scrollIntoView({behavior:'smooth',block:'center'});return;}
      if(!epi){
        epi={id:uid('e'),name:item.name,ca:item.ca,model:clean(chk?.manufacturer||src.manufacturer||''),size:item.size,cycle:0,createdAt:now,updatedAt:now,source:'nota-fiscal-ia-v350',caVerified:chk?.found===true,caStatus:clean(chk?.status),caCheckedAt:chk?now:'',caSource:clean(chk?.sourceUrl||''),caValidity:clean(chk?.validity||''),productCode:clean(src.code)};
        app.epis.push(epi);created++;
      }else{
        let changed=false;
        if(!epi.ca&&item.ca){epi.ca=item.ca;changed=true;}
        if(!epi.size&&item.size){epi.size=item.size;changed=true;}
        if(!epi.model&&clean(chk?.manufacturer||src.manufacturer)){epi.model=clean(chk?.manufacturer||src.manufacturer);changed=true;}
        if(!epi.productCode&&src.code){epi.productCode=clean(src.code);changed=true;}
        if(chk){epi.caVerified=chk.found===true;epi.caStatus=clean(chk.status);epi.caCheckedAt=now;epi.caSource=clean(chk.sourceUrl||CA_URL);epi.caValidity=clean(chk.validity||'');changed=true;}
        if(changed){epi.updatedAt=now;updated++;}
      }
      const sk=`${companyId}::${epi.id}`;if(stock.minimums[sk]==null)stock.minimums[sk]=DEFAULT_MIN;
      stock.movements.unshift({id:uid('sm'),type:'IN',delta:item.qty,companyId,epiId:epi.id,note:`Entrada por nota fiscal IA • ${marker}${currentInvoice.number?' • NF '+currentInvoice.number:''}${currentInvoice.supplier?' • '+currentInvoice.supplier:''}${src.code?' • cód. '+src.code:''}`,invoiceKey:currentInvoice.key||'',invoiceNumber:currentInvoice.number||'',invoiceSupplier:currentInvoice.supplier||'',productCode:src.code||'',createdAt:now});entered++;
    }
    if(!entered)return toast('Nenhum item válido para importar.');
    writeState(state);
    $('#nf350Status').innerHTML=`<div class="nf350-msg ok">✓ Nota importada: ${created} EPI(s) novo(s), ${updated} cadastro(s) atualizado(s) e ${entered} entrada(s) no estoque.</div>`;$('#nf350Preview').innerHTML='';currentInvoice=null;selectedFile=null;const f=$('#nf350File');if(f)f.value='';toast('Nota fiscal importada com sucesso.');
    if(state.pc)setTimeout(()=>location.reload(),900);
  }
  function boot(){
    styles();inject();
    document.addEventListener('click',e=>{
      const go=e.target.closest?.('[data-go="stock"],[data-view="stock"]');if(go)setTimeout(inject,80);
    },true);
    document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(inject,80));
    [400,1200,2600].forEach(ms=>setTimeout(inject,ms));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
