(() => {
  const KEY = 'auditarEpiV1';
  let stagedWorkers = [];

  const $ = (s, root=document) => root.querySelector(s);
  const norm = (v='') => String(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const clean = (v='') => String(v ?? '').replace(/\s+/g,' ').trim();
  const digits = (v='') => String(v).replace(/\D/g,'');
  const uid = p => `${p}_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;

  function toast(msg){
    const el = $('#toast');
    if(!el) return alert(msg);
    el.textContent = msg; el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 2800);
  }
  function readState(){
    try { return {companies:[],workers:[],epis:[],deliveries:[], ...JSON.parse(localStorage.getItem(KEY)||'{}')}; }
    catch { return {companies:[],workers:[],epis:[],deliveries:[]}; }
  }
  function writeState(state){ localStorage.setItem(KEY, JSON.stringify(state)); }
  function esc(v=''){ return String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }

  function syncCompanySelect(){
    const state = readState();
    const select = $('#importCompany');
    if(!select) return;
    const old = select.value;
    select.innerHTML = '<option value="">Selecione a empresa</option>' + state.companies.map(c=>`<option value="${c.id}">${esc(c.name)}</option>`).join('');
    if(state.companies.some(c=>c.id===old)) select.value = old;
  }

  function splitCsvLine(line, delimiter){
    const out=[]; let cur=''; let quoted=false;
    for(let i=0;i<line.length;i++){
      const ch=line[i];
      if(ch==='"'){
        if(quoted && line[i+1]==='"'){ cur+='"'; i++; }
        else quoted=!quoted;
      } else if(ch===delimiter && !quoted){ out.push(cur.trim()); cur=''; }
      else cur+=ch;
    }
    out.push(cur.trim()); return out;
  }

  function detectDelimiter(text){
    const sample = text.split(/\r?\n/).filter(Boolean).slice(0,5).join('\n');
    const counts = [[';', (sample.match(/;/g)||[]).length], ['\t',(sample.match(/\t/g)||[]).length], [',',(sample.match(/,/g)||[]).length]];
    counts.sort((a,b)=>b[1]-a[1]); return counts[0][1] ? counts[0][0] : ';';
  }

  const aliases = {
    name:['nome','nome completo','funcionario','funcionário','colaborador','empregado','trabalhador'],
    cpf:['cpf','cpf funcionario','cpf funcionário','documento'],
    reg:['matricula','matrícula','registro','chapa','id funcionario','id funcionário'],
    role:['cargo','funcao','função','ocupacao','ocupação'],
    sector:['setor','departamento','area','área','lotacao','lotação']
  };
  function headerField(value){
    const n=norm(value);
    for(const [key,list] of Object.entries(aliases)) if(list.some(a=>norm(a)===n)) return key;
    return null;
  }

  function rowsFromMatrix(matrix){
    const rows = matrix.map(r=>r.map(clean)).filter(r=>r.some(Boolean));
    if(!rows.length) return [];
    let headerIndex = rows.findIndex(r=>r.some(cell=>headerField(cell)==='name'));
    if(headerIndex < 0) headerIndex = 0;
    const headers = rows[headerIndex].map(headerField);
    const hasKnownHeader = headers.some(Boolean);
    if(!hasKnownHeader) return parseLooseLines(rows.map(r=>r.join('\t')));
    const result=[];
    for(const row of rows.slice(headerIndex+1)){
      const obj={name:'',cpf:'',reg:'',role:'',sector:''};
      headers.forEach((key,i)=>{ if(key && !obj[key]) obj[key]=clean(row[i]); });
      if(isLikelyName(obj.name)) result.push(obj);
    }
    return result;
  }

  function isLikelyName(name){
    const n=clean(name);
    if(n.length < 3 || /^\d+$/.test(n)) return false;
    const bad=['nome','funcionario','funcionário','colaborador','cpf','matricula','matrícula','cargo','setor'];
    return !bad.includes(norm(n));
  }

  function parseLooseLines(lines){
    const result=[];
    for(const raw of lines){
      const line=clean(raw); if(!line) continue;
      const cpfMatch=line.match(/\b\d{3}\.?\d{3}\.?\d{3}[-\s]?\d{2}\b/);
      const parts=raw.split(/\t|\s{2,}|;/).map(clean).filter(Boolean);
      let name = parts.find(p=>isLikelyName(p) && !/\d/.test(p) && p.split(' ').length>=2) || '';
      if(!name){
        const beforeCpf = cpfMatch ? line.slice(0, cpfMatch.index).trim() : line;
        if(isLikelyName(beforeCpf) && beforeCpf.split(' ').length>=2) name=beforeCpf;
      }
      if(!name) continue;
      const cpf=cpfMatch?cpfMatch[0]:'';
      const remaining=parts.filter(p=>p!==name && p!==cpf);
      result.push({name,cpf,reg:'',role:remaining[0]||'',sector:remaining[1]||''});
    }
    return result;
  }

  async function parseCsv(file){
    const text=await file.text(); const delimiter=detectDelimiter(text);
    const matrix=text.split(/\r?\n/).filter(l=>l.trim()).map(l=>splitCsvLine(l,delimiter));
    return rowsFromMatrix(matrix);
  }

  async function parseXlsx(file){
    if(!window.XLSX) throw new Error('Leitor de Excel indisponível. Abra o app com internet e tente novamente.');
    const data=await file.arrayBuffer();
    const book=XLSX.read(data,{type:'array'}); const sheet=book.Sheets[book.SheetNames[0]];
    const matrix=XLSX.utils.sheet_to_json(sheet,{header:1,defval:''});
    return rowsFromMatrix(matrix);
  }

  async function parsePdf(file){
    if(!window.pdfjsLib) throw new Error('Leitor de PDF indisponível. Abra o app com internet e tente novamente.');
    pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    const data=new Uint8Array(await file.arrayBuffer()); const pdf=await pdfjsLib.getDocument({data}).promise;
    const matrix=[];
    for(let p=1;p<=pdf.numPages;p++){
      const page=await pdf.getPage(p); const tc=await page.getTextContent(); const groups=new Map();
      tc.items.forEach(item=>{
        const y=Math.round(item.transform?.[5]||0); const x=item.transform?.[4]||0;
        const key=[...groups.keys()].find(k=>Math.abs(k-y)<=2) ?? y;
        if(!groups.has(key)) groups.set(key,[]); groups.get(key).push({x,text:clean(item.str)});
      });
      [...groups.entries()].sort((a,b)=>b[0]-a[0]).forEach(([,items])=>{
        const row=items.sort((a,b)=>a.x-b.x).map(i=>i.text).filter(Boolean); if(row.length) matrix.push(row);
      });
    }
    return rowsFromMatrix(matrix);
  }

  function dedupeStaged(rows){
    const seen=new Set(); const out=[];
    for(const w of rows){
      const key=digits(w.cpf) || clean(w.reg) || norm(w.name);
      if(!key || seen.has(key)) continue; seen.add(key); out.push({...w,name:clean(w.name),cpf:clean(w.cpf),reg:clean(w.reg),role:clean(w.role),sector:clean(w.sector)});
    }
    return out;
  }

  function renderPreview(rows){
    const box=$('#importPreview'); const count=$('#importCount'); const btn=$('#btnCommitImport');
    stagedWorkers=dedupeStaged(rows); count.textContent=`${stagedWorkers.length} trabalhador(es) identificado(s)`;
    btn.disabled=!stagedWorkers.length;
    if(!stagedWorkers.length){ box.innerHTML='<div class="empty">Não consegui identificar trabalhadores nessa lista. Verifique se existe uma coluna de Nome.</div>'; return; }
    box.innerHTML=`<div class="import-table-wrap"><table class="import-table"><thead><tr><th>Nome</th><th>CPF</th><th>Matrícula</th><th>Cargo</th><th>Setor</th></tr></thead><tbody>${stagedWorkers.slice(0,80).map(w=>`<tr><td>${esc(w.name)}</td><td>${esc(w.cpf||'—')}</td><td>${esc(w.reg||'—')}</td><td>${esc(w.role||'—')}</td><td>${esc(w.sector||'—')}</td></tr>`).join('')}</tbody></table></div>${stagedWorkers.length>80?`<small class="import-more">Prévia dos primeiros 80 de ${stagedWorkers.length}.</small>`:''}`;
  }

  async function handleFile(file){
    if(!file) return;
    const ext=(file.name.split('.').pop()||'').toLowerCase();
    $('#importCount').textContent='Lendo arquivo…'; $('#importPreview').innerHTML=''; $('#btnCommitImport').disabled=true;
    try{
      let rows=[];
      if(['csv','txt'].includes(ext)) rows=await parseCsv(file);
      else if(['xlsx','xls'].includes(ext)) rows=await parseXlsx(file);
      else if(ext==='pdf') rows=await parsePdf(file);
      else throw new Error('Formato não aceito. Use PDF, Excel, CSV ou TXT.');
      renderPreview(rows);
    }catch(err){ stagedWorkers=[]; $('#importCount').textContent='Falha na leitura'; $('#importPreview').innerHTML=`<div class="empty">${esc(err.message||'Não foi possível ler o arquivo.')}</div>`; toast(err.message||'Não foi possível ler o arquivo.'); }
  }

  function sameWorker(a,b){
    const acpf=digits(a.cpf), bcpf=digits(b.cpf); if(acpf && bcpf && acpf===bcpf) return true;
    if(a.reg && b.reg && norm(a.reg)===norm(b.reg)) return true;
    return norm(a.name)===norm(b.name);
  }

  function commitImport(){
    const companyId=$('#importCompany').value; if(!companyId) return toast('Selecione a empresa.');
    if(!stagedWorkers.length) return toast('Selecione uma lista de funcionários.');
    const state=readState(); let added=0, updated=0, skipped=0;
    for(const item of stagedWorkers){
      const existing=state.workers.find(w=>w.companyId===companyId && sameWorker(w,item));
      if(existing){
        let changed=false;
        ['cpf','reg','role','sector'].forEach(k=>{ if(!existing[k] && item[k]){ existing[k]=item[k]; changed=true; } });
        if(existing.active===false){ existing.active=true; changed=true; }
        changed?updated++:skipped++;
      }else{
        state.workers.push({id:uid('w'),companyId,name:item.name,cpf:item.cpf||'',reg:item.reg||'',role:item.role||'',sector:item.sector||'',active:true,createdAt:new Date().toISOString(),source:'import'}); added++;
      }
    }
    writeState(state); sessionStorage.setItem('auditarEpiAfterImport','1');
    alert(`Importação concluída.\n\n${added} novo(s) cadastrado(s)\n${updated} atualizado(s)\n${skipped} já estavam cadastrados.`);
    location.reload();
  }

  function deliveryWorkers(search=''){
    const state=readState(); const comp=$('#deliveryCompany')?.value||''; const q=norm(search);
    return state.workers.filter(w=>w.active!==false && (!comp||w.companyId===comp) && (!q || [w.name,w.cpf,w.reg,w.role,w.sector].some(v=>norm(v).includes(q))));
  }
  function filterDeliveryWorkers(){
    const select=$('#deliveryWorker'), input=$('#deliveryWorkerSearch'); if(!select||!input) return;
    const old=select.value; const rows=deliveryWorkers(input.value);
    select.innerHTML='<option value="">Selecione o colaborador</option>'+rows.map(w=>`<option value="${w.id}">${esc(w.name)}${w.reg?' • Mat. '+esc(w.reg):''}${w.cpf?' • CPF '+esc(w.cpf):''}</option>`).join('');
    if(rows.some(w=>w.id===old)) select.value=old;
    $('#deliveryWorkerCount').textContent = input.value ? `${rows.length} encontrado(s)` : `${rows.length} cadastrado(s)`;
  }

  document.addEventListener('DOMContentLoaded',()=>{
    syncCompanySelect();
    $('#importFile')?.addEventListener('change',e=>handleFile(e.target.files?.[0]));
    $('#btnCommitImport')?.addEventListener('click',commitImport);
    $('#deliveryWorkerSearch')?.addEventListener('input',filterDeliveryWorkers);
    $('#deliveryCompany')?.addEventListener('change',()=>{ if($('#deliveryWorkerSearch')) $('#deliveryWorkerSearch').value=''; setTimeout(filterDeliveryWorkers,0); });
    document.addEventListener('click',e=>{ if(e.target.closest('[data-go="importWorkers"]')) setTimeout(syncCompanySelect,0); if(e.target.closest('[data-go="delivery"]')) setTimeout(filterDeliveryWorkers,0); });
    if(sessionStorage.getItem('auditarEpiAfterImport')){
      sessionStorage.removeItem('auditarEpiAfterImport');
      setTimeout(()=>document.querySelector('[data-go="workers"]')?.click(),50);
    }
  });
})();
